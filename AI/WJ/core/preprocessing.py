from __future__ import annotations

import os
import tempfile
from typing import Tuple

import nibabel as nib
import torch
from monai.transforms import (
    Compose,
    CropForegroundd,
    EnsureChannelFirstd,
    LoadImaged,
    NormalizeIntensityd,
    Orientationd,
    Resized,
    Spacingd,
    ToTensord,
)

TARGET_SHAPE: Tuple[int, int, int] = (96, 96, 96)
TARGET_SPACING: Tuple[float, float, float] = (1.5, 1.5, 1.5)


def get_inference_transforms() -> Compose:
    """학습과 100% 동일한 추론용 전처리 (val_transforms 기준, augmentation 없음)."""
    return Compose([
        LoadImaged(keys=["image"]),
        EnsureChannelFirstd(keys=["image"]),
        Orientationd(keys=["image"], axcodes="RAS"),
        Spacingd(keys=["image"], pixdim=TARGET_SPACING, mode="bilinear"),
        CropForegroundd(keys=["image"], source_key="image", allow_smaller=True),
        Resized(keys=["image"], spatial_size=TARGET_SHAPE),
        NormalizeIntensityd(keys=["image"], nonzero=True, channel_wise=True),
        ToTensord(keys=["image"]),
    ])


def skull_strip(nifti_path: str) -> str:
    """
    HD-BET으로 skull stripping 수행.
    정상 뇌 MRI(skull 있는 raw 입력)에만 적용. BraTS 데이터는 이미 stripped이므로 불필요.

    Args:
        nifti_path: skull 있는 raw NIfTI 파일 경로

    Returns:
        skull이 제거된 임시 NIfTI 파일 경로 (호출자가 삭제 책임)

    Raises:
        RuntimeError: HD-BET 실패
    """
    try:
        import torch as _torch
        from HD_BET.hd_bet_prediction import get_hdbet_predictor, hdbet_predict

        device = _torch.device("cuda" if _torch.cuda.is_available() else "cpu")
        predictor = get_hdbet_predictor(use_tta=False, device=device, verbose=False)

        out_dir = tempfile.mkdtemp(prefix="hdbet_")
        hdbet_predict(
            input_file_or_folder=nifti_path,
            output_file_or_folder=out_dir,
            predictor=predictor,
            keep_brain_mask=False,
            compute_brain_extracted_image=True,
        )

        # HD-BET은 입력 파일명 그대로 출력 폴더에 저장
        base = os.path.basename(nifti_path)
        stripped_path = os.path.join(out_dir, base)
        if not os.path.exists(stripped_path):
            # .nii → .nii.gz 변환된 경우
            stripped_path = stripped_path.replace(".nii.gz", ".nii").replace(".nii", ".nii.gz")

        if not os.path.exists(stripped_path):
            raise RuntimeError(f"HD-BET 출력 파일을 찾을 수 없음: {out_dir}")

        return stripped_path

    except ImportError as e:
        raise RuntimeError(f"HD-BET 미설치: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Skull stripping 실패: {e}") from e


def preprocess_nifti(nifti_path: str, apply_skull_strip: bool = False) -> torch.Tensor:
    """
    NIfTI 파일을 모델 입력 텐서로 변환.

    Args:
        nifti_path: .nii 또는 .nii.gz 파일 경로
        apply_skull_strip: True면 HD-BET skull stripping 먼저 수행.
                           정상 뇌 raw MRI (OASIS, HCP 등) 입력 시 True.
                           BraTS 데이터는 이미 stripped이므로 False.

    Returns:
        torch.Tensor: shape (1, 1, 96, 96, 96), dtype float32

    Raises:
        FileNotFoundError: 파일이 존재하지 않음
        ValueError: 잘못된 NIfTI 형식 또는 3D 아님
    """
    if not os.path.exists(nifti_path):
        raise FileNotFoundError(f"NIfTI 파일을 찾을 수 없습니다: {nifti_path}")

    _check_nifti_valid(nifti_path)

    stripped_tmp = None
    try:
        if apply_skull_strip:
            stripped_tmp = skull_strip(nifti_path)
            target_path = stripped_tmp
        else:
            target_path = nifti_path

        transform = get_inference_transforms()
        data = transform({"image": target_path})
        tensor = data["image"]  # (1, 96, 96, 96)

    finally:
        # skull stripping 임시 파일 정리
        if stripped_tmp and os.path.exists(stripped_tmp):
            import shutil
            shutil.rmtree(os.path.dirname(stripped_tmp), ignore_errors=True)

    return tensor.unsqueeze(0)  # (1, 1, 96, 96, 96)


def validate_nifti_file(nifti_path: str) -> dict:
    """
    NIfTI 파일 유효성 검증.

    Returns:
        {
            "valid": bool,
            "shape": tuple,
            "spacing": tuple,
            "is_3d": bool,
            "error": str | None
        }
    """
    result = {"valid": False, "shape": None, "spacing": None, "is_3d": False, "error": None}

    if not os.path.exists(nifti_path):
        result["error"] = f"파일 없음: {nifti_path}"
        return result

    try:
        img = nib.load(nifti_path)
        data = img.get_fdata()
    except Exception as e:
        result["error"] = f"NIfTI 파싱 실패: {e}"
        return result

    if data.size == 0:
        result["error"] = "빈 파일"
        return result

    shape = data.shape
    is_3d = data.ndim == 3
    zooms = img.header.get_zooms()
    spacing = tuple(float(z) for z in zooms[:3])

    result.update({
        "valid": is_3d,
        "shape": shape,
        "spacing": spacing,
        "is_3d": is_3d,
        "error": None if is_3d else f"3D NIfTI만 지원 (입력 ndim={data.ndim})",
    })
    return result


def _check_nifti_valid(nifti_path: str) -> None:
    try:
        img = nib.load(nifti_path)
        data = img.get_fdata()
    except Exception as e:
        raise ValueError(f"NIfTI 파싱 실패: {e}") from e

    if data.size == 0:
        raise ValueError("빈 파일")

    if data.ndim != 3:
        raise ValueError(f"3D NIfTI만 지원 (입력 ndim={data.ndim})")
