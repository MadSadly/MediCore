from __future__ import annotations

import os
import time
from typing import Optional

import torch
from monai.networks.nets import DenseNet121

from WJ.core.preprocessing import preprocess_nifti

_model: Optional[DenseNet121] = None
_device: Optional[torch.device] = None

_CHECKPOINT_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "checkpoints", "best_model_v2.pth")


def load_model(checkpoint_path: str = _CHECKPOINT_DEFAULT) -> tuple[DenseNet121, torch.device]:
    """
    모델 로드 (싱글톤). 첫 호출 시 로드, 이후 호출 시 캐시 반환.

    Returns:
        (model, device) 튜플

    Raises:
        FileNotFoundError: 체크포인트 없음
        RuntimeError: 가중치 로드 실패
    """
    global _model, _device

    if _model is not None:
        return _model, _device

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"체크포인트를 찾을 수 없습니다: {checkpoint_path}")

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = DenseNet121(spatial_dims=3, in_channels=1, out_channels=2).to(_device)

    try:
        ckpt = torch.load(checkpoint_path, map_location=_device)
        model.load_state_dict(ckpt["model_state_dict"])
    except KeyError as e:
        raise RuntimeError(f"체크포인트 구조 불일치 — 'model_state_dict' 키 없음: {e}") from e
    except Exception as e:
        raise RuntimeError(f"가중치 로드 실패: {e}") from e

    model.eval()
    _model = model
    return _model, _device


def predict_tumor(nifti_path: str) -> dict:
    """
    NIfTI 파일 → 종양 분류 결과.

    Returns:
        {
            "prediction": "Tumor" | "Normal",
            "tumor_probability": float,
            "normal_probability": float,
            "confidence": float,
            "inference_time_ms": float
        }
    """
    t0 = time.perf_counter()

    tensor = preprocess_nifti(nifti_path)  # (1, 1, 96, 96, 96)
    result = predict_from_tensor(tensor)

    result["inference_time_ms"] = (time.perf_counter() - t0) * 1000
    return result


def predict_from_tensor(tensor: torch.Tensor) -> dict:
    """이미 전처리된 텐서 (1, 1, 96, 96, 96) 로부터 추론."""
    model, device = load_model()

    x = tensor.to(device)
    if x.dim() == 4:
        x = x.unsqueeze(0)  # (1, 1, 96, 96, 96) 보장

    model.eval()
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

    pred = int(probs.argmax())
    return {
        "prediction": "Tumor" if pred == 1 else "Normal",
        "tumor_probability": float(probs[1]),
        "normal_probability": float(probs[0]),
        "confidence": float(probs[pred]),
    }
