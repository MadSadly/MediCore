from __future__ import annotations

import os
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


def preprocess_nifti(nifti_path: str) -> torch.Tensor:
    """
    NIfTI 파일을 모델 입력 텐서로 변환.
    skull strip은 사전에 완료된 파일을 전달할 것.

    Returns:
        torch.Tensor: shape (1, 1, 96, 96, 96), dtype float32
    """
    if not os.path.exists(nifti_path):
        raise FileNotFoundError(f"NIfTI 파일을 찾을 수 없습니다: {nifti_path}")

    _check_nifti_valid(nifti_path)

    transform = get_inference_transforms()
    data = transform({"image": nifti_path})
    tensor = data["image"]  # (1, 96, 96, 96)

    return tensor.unsqueeze(0)  # (1, 1, 96, 96, 96)


def validate_nifti_file(nifti_path: str) -> dict:
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
