from __future__ import annotations

import os
import sys
import tempfile

import nibabel as nib
import numpy as np
import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from WJ.core.classifier import load_model, predict_tumor
import WJ.core.classifier as _clf_module


def create_dummy_nifti(shape=(120, 120, 80)) -> str:
    data = np.random.rand(*shape).astype(np.float32) * 1000
    img = nib.Nifti1Image(data, affine=np.eye(4))
    tmp = tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False)
    nib.save(img, tmp.name)
    return tmp.name


def test_model_loading():
    model, device = load_model()
    assert model is not None
    assert isinstance(device, torch.device)


def test_singleton():
    m1, _ = load_model()
    m2, _ = load_model()
    assert m1 is m2


def test_model_param_count():
    model, _ = load_model()
    n_params = sum(p.numel() for p in model.parameters())
    # 실측 11.2M (MODEL_CONTEXT.md 추정 ~7M과 다름 — MONAI DenseNet121 3D 실제 크기)
    assert 10_000_000 < n_params < 15_000_000, f"파라미터 수 이상: {n_params}"


def test_predict_dummy():
    dummy = create_dummy_nifti()
    try:
        result = predict_tumor(dummy)
        assert result["prediction"] in ["Tumor", "Normal"]
        assert 0 <= result["tumor_probability"] <= 1
        assert 0 <= result["normal_probability"] <= 1
        assert abs(result["tumor_probability"] + result["normal_probability"] - 1.0) < 1e-5
    finally:
        os.unlink(dummy)


def test_inference_time():
    dummy = create_dummy_nifti()
    try:
        result = predict_tumor(dummy)
        assert result["inference_time_ms"] < 10_000
    finally:
        os.unlink(dummy)
