from __future__ import annotations

import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from WJ.core.classifier import get_last_inference_data
from WJ.graph.workflow import run_diagnosis
from WJ.schemas.response import DiagnoseResponse, ErrorResponse

logger = logging.getLogger("medicore.brain")

router = APIRouter(prefix="/ai/brain", tags=["brain-tumor"])

_ALLOWED_EXTENSIONS = {".nii", ".nii.gz"}

_BRAIN_TMP = Path(tempfile.gettempdir()) / "medicore_brain"
_BRAIN_TMP.mkdir(exist_ok=True)


def _validate_extension(filename: str) -> None:
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in _ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NIfTI 파일만 허용됩니다 (.nii, .nii.gz). 받은 파일: {filename}",
        )


def _pick_volume(data: np.ndarray) -> np.ndarray:
    if data.ndim == 3:
        return data
    if data.ndim == 4:
        target = 3
        if data.shape[3] <= target:
            return data[:, :, :, 0]
        return data[:, :, :, target]
    raise ValueError(f"Unsupported NIfTI dimension: {data.ndim}")


def _normalize_slice(sl: np.ndarray) -> np.ndarray:
    sl = np.nan_to_num(sl, nan=0.0, posinf=0.0, neginf=0.0)
    vmin = np.percentile(sl, 1)
    vmax = np.percentile(sl, 99)
    if vmax - vmin < 1e-6:
        return np.zeros(sl.shape, dtype=np.uint8)
    sl = np.clip(sl, vmin, vmax)
    return ((sl - vmin) / (vmax - vmin) * 255.0).astype(np.uint8)


def _make_highlight_png(mri_sl: np.ndarray, prob_sl: np.ndarray):
    """그레이스케일 MRI 슬라이스 위에 종양 확률 맵을 빨간색으로 합성한 PNG 반환."""
    from PIL import Image

    gray = _normalize_slice(mri_sl)
    rgb = np.stack([gray, gray, gray], axis=-1).astype(np.uint8)

    tumor_mask = prob_sl > 0.5
    if tumor_mask.any():
        r = np.clip(gray[tumor_mask].astype(np.int32) * 0.35 + 190, 0, 255).astype(np.uint8)
        rgb[tumor_mask, 0] = r
        rgb[tumor_mask, 1] = (gray[tumor_mask] * 0.15).astype(np.uint8)
        rgb[tumor_mask, 2] = (gray[tumor_mask] * 0.15).astype(np.uint8)

    return Image.fromarray(rgb, "RGB")


def _orient(arr: np.ndarray) -> np.ndarray:
    """슬라이스 방향 정규화 (normal slices와 동일)."""
    return np.flipud(np.rot90(arr))


def _save_tumor_artifacts(image_np: np.ndarray, prob_map_np: np.ndarray, file_dir: Path) -> dict:
    """
    종양 감지 시 마스크 NIfTI + 전처리된 NIfTI + 하이라이트 슬라이스 PNG 저장.
    Returns: {"axial": N, "coronal": N, "sagittal": N}
    """
    import nibabel as nib

    affine = np.eye(4)  # 1mm isotropic, preprocessed space

    # 전처리된 MRI NIfTI 저장 (3D Niivue 오버레이용)
    pre_nii = nib.Nifti1Image(image_np.astype(np.float32), affine)
    nib.save(pre_nii, str(file_dir / "preprocessed.nii"))

    # 종양 확률 맵 NIfTI 저장 (float32 0-1, Niivue colormap용)
    mask_nii = nib.Nifti1Image(prob_map_np.astype(np.float32), affine)
    nib.save(mask_nii, str(file_dir / "mask.nii"))

    # 하이라이트 슬라이스 PNG 생성 (3축)
    counts = {}
    axes_config = {
        "axial":    [(image_np[:, :, i], prob_map_np[:, :, i]) for i in range(image_np.shape[2])],
        "coronal":  [(image_np[:, i, :], prob_map_np[:, i, :]) for i in range(image_np.shape[1])],
        "sagittal": [(image_np[i, :, :], prob_map_np[i, :, :]) for i in range(image_np.shape[0])],
    }

    for axis, slice_pairs in axes_config.items():
        out_dir = file_dir / f"highlight_{axis}"
        out_dir.mkdir(exist_ok=True)
        for idx, (mri_sl, prob_sl) in enumerate(slice_pairs):
            img = _make_highlight_png(_orient(mri_sl), _orient(prob_sl))
            img.save(str(out_dir / f"slice_{idx:03d}.png"))
        counts[axis] = len(slice_pairs)
        logger.info(f"하이라이트 슬라이스 생성 | axis: {axis} | count: {len(slice_pairs)}")

    return counts


# ──────────────────────────────────────────────
# Viewer endpoints
# ──────────────────────────────────────────────

@router.post("/upload", summary="NIfTI 파일 업로드 (뷰어용)")
async def upload_for_viewer(
    file: UploadFile = File(..., description="T1-weighted MRI NIfTI 파일"),
):
    _validate_extension(file.filename)
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    file_id = str(uuid.uuid4())
    file_dir = _BRAIN_TMP / file_id
    file_dir.mkdir(parents=True, exist_ok=True)

    suffix = ".nii.gz" if file.filename.lower().endswith(".nii.gz") else ".nii"
    nii_path = file_dir / f"input{suffix}"
    nii_path.write_bytes(contents)

    logger.info(f"뷰어 업로드 | fileId: {file_id} | 파일: {file.filename} | 크기: {len(contents):,} bytes")
    return {"ok": True, "fileId": file_id, "fileName": file.filename}


class SlicesRequest(BaseModel):
    fileId: str
    axis: str


@router.post("/slices", summary="2D 슬라이스 PNG 생성")
async def generate_slices(req: SlicesRequest):
    if req.axis not in ("axial", "coronal", "sagittal"):
        raise HTTPException(status_code=400, detail="axis는 axial/coronal/sagittal 중 하나여야 합니다.")

    file_dir = _BRAIN_TMP / req.fileId
    nii_files = list(file_dir.glob("input.nii*"))
    if not nii_files:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다. 먼저 /upload를 호출하세요.")

    out_dir = file_dir / req.axis
    if out_dir.exists():
        existing = sorted(out_dir.glob("slice_*.png"))
        if existing:
            return {"ok": True, "sliceCount": len(existing), "baseUrl": f"/ai/brain/slices/{req.fileId}/{req.axis}/"}

    out_dir.mkdir(exist_ok=True)

    import nibabel as nib
    from PIL import Image

    nii = nib.load(str(nii_files[0]))
    canonical = nib.as_closest_canonical(nii)
    data_arr = canonical.get_fdata()

    try:
        vol = _pick_volume(data_arr)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    slices = []
    if req.axis == "axial":
        for i in range(vol.shape[2]):
            slices.append(np.flipud(np.rot90(vol[:, :, i])))
    elif req.axis == "coronal":
        for i in range(vol.shape[1]):
            slices.append(np.flipud(np.rot90(vol[:, i, :])))
    elif req.axis == "sagittal":
        for i in range(vol.shape[0]):
            slices.append(np.flipud(np.rot90(vol[i, :, :])))

    for idx, sl in enumerate(slices):
        Image.fromarray(_normalize_slice(sl)).save(str(out_dir / f"slice_{idx:03d}.png"))

    logger.info(f"슬라이스 생성 | fileId: {req.fileId} | axis: {req.axis} | count: {len(slices)}")
    return {"ok": True, "sliceCount": len(slices), "baseUrl": f"/ai/brain/slices/{req.fileId}/{req.axis}/"}


@router.get("/slices/{file_id}/{axis}/{filename}", summary="슬라이스 PNG 서빙")
async def serve_slice(file_id: str, axis: str, filename: str):
    if axis not in ("axial", "coronal", "sagittal"):
        raise HTTPException(status_code=400, detail="Invalid axis")
    if not filename.endswith(".png"):
        raise HTTPException(status_code=400, detail="PNG 파일만 서빙 가능합니다.")
    file_path = _BRAIN_TMP / file_id / axis / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="슬라이스를 찾을 수 없습니다.")
    return FileResponse(str(file_path), media_type="image/png")


@router.get("/highlight/{file_id}/{axis}/{filename}", summary="하이라이트 슬라이스 PNG 서빙")
async def serve_highlight_slice(file_id: str, axis: str, filename: str):
    if axis not in ("axial", "coronal", "sagittal"):
        raise HTTPException(status_code=400, detail="Invalid axis")
    if not filename.endswith(".png"):
        raise HTTPException(status_code=400, detail="PNG 파일만 서빙 가능합니다.")
    file_path = _BRAIN_TMP / file_id / f"highlight_{axis}" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="하이라이트 슬라이스를 찾을 수 없습니다.")
    return FileResponse(str(file_path), media_type="image/png")


@router.get("/mask/{file_id}/mask.nii", summary="종양 확률 맵 NIfTI 서빙 (3D 오버레이용)")
async def serve_mask(file_id: str):
    file_path = _BRAIN_TMP / file_id / "mask.nii"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="마스크 파일을 찾을 수 없습니다.")
    return FileResponse(str(file_path), media_type="application/octet-stream")


@router.get("/preprocessed/{file_id}/preprocessed.nii", summary="전처리된 MRI NIfTI 서빙 (3D 뷰어용)")
async def serve_preprocessed(file_id: str):
    file_path = _BRAIN_TMP / file_id / "preprocessed.nii"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="전처리 파일을 찾을 수 없습니다.")
    return FileResponse(str(file_path), media_type="application/octet-stream")


# ──────────────────────────────────────────────
# Diagnosis endpoint
# ──────────────────────────────────────────────

@router.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 파일 형식"},
        422: {"model": ErrorResponse, "description": "처리 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    summary="뇌종양 진단",
)
async def diagnose(
    file: UploadFile = File(..., description="T1-weighted MRI NIfTI 파일"),
    fileId: Optional[str] = Form(None),
) -> DiagnoseResponse:
    _validate_extension(file.filename)

    suffix = ".nii.gz" if file.filename.lower().endswith(".nii.gz") else ".nii"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="빈 파일입니다.")
        tmp.write(contents)
        tmp.flush()
        tmp.close()

        logger.info(f"진단 시작 | 파일: {file.filename} | 크기: {len(contents):,} bytes")
        response = run_diagnosis(tmp.name)
        logger.info(
            f"진단 완료 | 판정: {response.classification.prediction} "
            f"| 확신도: {response.classification.confidence:.1%} "
            f"| 처리시간: {response.metadata.get('processing_time_ms', '?')}ms"
        )

        # 종양 감지 + fileId 있으면 하이라이트 아티팩트 생성
        if response.classification.prediction == "Tumor" and fileId:
            try:
                inference_data = get_last_inference_data()
                file_dir = _BRAIN_TMP / fileId
                if inference_data and file_dir.exists():
                    image_np, prob_map_np = inference_data
                    counts = _save_tumor_artifacts(image_np, prob_map_np, file_dir)
                    response.metadata["mask_ready"] = True
                    response.metadata["highlight_slice_counts"] = counts
                    logger.info(f"종양 아티팩트 저장 완료 | fileId: {fileId}")
            except Exception as e:
                logger.warning(f"마스크 생성 실패 (진단 결과는 정상): {e}")

        return response

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"워크플로우 실패: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.exception(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="서버 내부 오류가 발생했습니다.")
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


@router.get("/health", summary="뇌종양 모듈 헬스체크")
def health() -> dict:
    return {"module": "brain", "status": "ok"}
