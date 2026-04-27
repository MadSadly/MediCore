from __future__ import annotations

import os
import sys
import tempfile

import nibabel as nib
import numpy as np
import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from WJ.core.preprocessing import preprocess_nifti, validate_nifti_file


def create_dummy_nifti(shape=(120, 120, 80)) -> str:
    data = np.random.rand(*shape).astype(np.float32) * 1000
    img = nib.Nifti1Image(data, affine=np.eye(4))
    tmp = tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False)
    nib.save(img, tmp.name)
    return tmp.name


@pytest.fixture(scope="module")
def dummy_nifti():
    path = create_dummy_nifti()
    yield path
    os.unlink(path)


def test_output_shape(dummy_nifti):
    tensor = preprocess_nifti(dummy_nifti)
    assert tensor.shape == (1, 1, 96, 96, 96), f"Shape 다름: {tensor.shape}"


def test_value_range(dummy_nifti):
    tensor = preprocess_nifti(dummy_nifti)
    assert tensor.min().item() > -10, "최솟값이 너무 낮음 (정규화 이상)"
    assert tensor.max().item() < 10, "최댓값이 너무 높음 (정규화 이상)"


def test_dtype(dummy_nifti):
    tensor = preprocess_nifti(dummy_nifti)
    assert tensor.dtype == torch.float32, f"Dtype 다름: {tensor.dtype}"


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        preprocess_nifti("/nonexistent/path/brain.nii.gz")


def test_invalid_file():
    tmp = tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False, mode="w")
    tmp.write("this is not a nifti file")
    tmp.close()
    try:
        with pytest.raises(ValueError):
            preprocess_nifti(tmp.name)
    finally:
        os.unlink(tmp.name)


def test_validate_valid_file(dummy_nifti):
    result = validate_nifti_file(dummy_nifti)
    assert result["valid"] is True
    assert result["is_3d"] is True
    assert result["shape"] == (120, 120, 80)
    assert result["error"] is None


def test_validate_missing_file():
    result = validate_nifti_file("/nonexistent/brain.nii.gz")
    assert result["valid"] is False
    assert result["error"] is not None
