from __future__ import annotations

import logging
import os
import tempfile
import uuid
from pathlib import Path

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from WJ.graph.workflow import run_diagnosis
from WJ.schemas.response import DiagnoseResponse, ErrorResponse

logger = logging.getLogger("medicore.brain")

router = APIRouter(prefix="/ai/brain", tags=["brain-tumor"])

_ALLOWED_EXTENSIONS = {".nii", ".nii.gz"}

# Temp storage for viewer sessions
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
    axis: str  # axial | coronal | sagittal


@router.post("/slices", summary="2D 슬라이스 PNG 생성")
async def generate_slices(req: SlicesRequest):
    if req.axis not in ("axial", "coronal", "sagittal"):
        raise HTTPException(status_code=400, detail="axis는 axial/coronal/sagittal 중 하나여야 합니다.")

    file_dir = _BRAIN_TMP / req.fileId
    nii_files = list(file_dir.glob("input.nii*"))
    if not nii_files:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다. 먼저 /upload를 호출하세요.")

    out_dir = file_dir / req.axis

    # Return cached if already generated
    if out_dir.exists():
        existing = sorted(out_dir.glob("slice_*.png"))
        if existing:
            return {
                "ok": True,
                "sliceCount": len(existing),
                "baseUrl": f"/ai/brain/slices/{req.fileId}/{req.axis}/",
            }

    out_dir.mkdir(exist_ok=True)

    import nibabel as nib
    from PIL import Image

    nii = nib.load(str(nii_files[0]))
    # 저장 방향과 무관하게 표준 RAS 방향으로 정규화 (IXI 등 비표준 orientation 대응)
    canonical = nib.as_closest_canonical(nii)
    data_arr = canonical.get_fdata()

    try:
        vol = _pick_volume(data_arr)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    slices = []
    if req.axis == "axial":
        # RAS canonical: z = superior → axial은 위에서 아래로
        for i in range(vol.shape[2]):
            sl = vol[:, :, i]
            slices.append(np.flipud(np.rot90(sl)))
    elif req.axis == "coronal":
        # y = anterior → coronal은 앞에서 뒤로
        for i in range(vol.shape[1]):
            sl = vol[:, i, :]
            slices.append(np.flipud(np.rot90(sl)))
    elif req.axis == "sagittal":
        # x = right → sagittal은 오른쪽에서 왼쪽으로
        for i in range(vol.shape[0]):
            sl = vol[i, :, :]
            slices.append(np.flipud(np.rot90(sl)))

    for idx, sl in enumerate(slices):
        img = Image.fromarray(_normalize_slice(sl))
        img.save(str(out_dir / f"slice_{idx:03d}.png"))

    logger.info(f"슬라이스 생성 | fileId: {req.fileId} | axis: {req.axis} | count: {len(slices)}")
    return {
        "ok": True,
        "sliceCount": len(slices),
        "baseUrl": f"/ai/brain/slices/{req.fileId}/{req.axis}/",
    }


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
    description=(
        "NIfTI (.nii / .nii.gz) 파일을 업로드하면 "
        "3D DenseNet121 분류 → RAG 검색 → Gemini 리포트 생성 결과를 반환합니다. "
        "AI 보조 도구이며 최종 진단은 전문의가 수행해야 합니다."
    ),
)
async def diagnose(
    file: UploadFile = File(..., description="T1-weighted MRI NIfTI 파일"),
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
