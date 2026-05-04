from __future__ import annotations

import os
import time
from typing import Optional

import numpy as np
import torch
from monai.inferers import sliding_window_inference
from monai.networks.nets import UNet

from WJ.core.preprocessing import preprocess_nifti

_model: Optional[UNet] = None
_device: Optional[torch.device] = None
_last_image_np: Optional[np.ndarray] = None
_last_prob_map_np: Optional[np.ndarray] = None

_CHECKPOINT_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "checkpoints", "best_model_v2.pth")

TUMOR_VOL_THR = 0.005   # 뇌 복셀의 0.5% 이상 → TUMOR
TUMOR_CONF_THR = 0.05   # 뇌 복셀의 5% 이상 → confidence 1.0 (포화점)


def load_model(checkpoint_path: str = _CHECKPOINT_DEFAULT) -> tuple[UNet, torch.device]:
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

    model = UNet(
        spatial_dims=3,
        in_channels=1,
        out_channels=2,
        channels=(16, 32, 64, 128, 256),
        strides=(2, 2, 2, 2),
        num_res_units=2,
        dropout=0.2,
    ).to(_device)

    try:
        ckpt = torch.load(checkpoint_path, map_location=_device)
        state_dict = ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt
        model.load_state_dict(state_dict)
    except Exception as e:
        raise RuntimeError(f"가중치 로드 실패: {e}") from e

    model.eval()
    _model = model
    return _model, _device


def _tumor_fraction(prob_map: torch.Tensor, image: torch.Tensor) -> float:
    """종양으로 예측된 복셀 / 뇌 복셀 (intensity > 0 기준)."""
    brain_voxels = (image > 0).sum().item()
    tumor_voxels = (prob_map > 0.5).sum().item()
    return tumor_voxels / (brain_voxels + 1e-6)


def _confidence_from_fraction(frac: float, is_tumor: bool) -> float:
    """
    tumor_fraction을 [0.5, 1.0] 신뢰도로 변환.
    결정 경계(TUMOR_VOL_THR)에서 0.5, 경계에서 멀수록 1.0에 수렴.
    """
    if is_tumor:
        raw = min(frac / TUMOR_CONF_THR, 1.0)
    else:
        raw = 1.0 - min(frac / TUMOR_VOL_THR, 1.0)
    return 0.5 + raw * 0.5


def get_last_inference_data() -> Optional[tuple]:
    """마지막 추론의 (image_np, prob_map_np) 반환. 추론 전이면 None."""
    if _last_image_np is None or _last_prob_map_np is None:
        return None
    return _last_image_np.copy(), _last_prob_map_np.copy()


def predict_tumor(nifti_path: str) -> dict:
    """
    NIfTI 파일 → 종양 분류 결과.

    Returns:
        {
            "prediction": "Tumor" | "Normal",
            "tumor_fraction": float,       # 뇌 복셀 대비 종양 복셀 비율 (핵심 지표)
            "tumor_probability": float,    # 종양 방향 신뢰도 (0~1)
            "normal_probability": float,   # 정상 방향 신뢰도 (0~1)
            "confidence": float,           # 결정 경계 거리 기반 신뢰도 (0.5~1.0)
            "inference_time_ms": float
        }
    """
    t0 = time.perf_counter()

    tensor = preprocess_nifti(nifti_path)
    result = predict_from_tensor(tensor)

    result["inference_time_ms"] = (time.perf_counter() - t0) * 1000
    return result


def predict_from_tensor(tensor: torch.Tensor) -> dict:
    """이미 전처리된 텐서 (1, 1, H, W, D) 로부터 추론."""
    model, device = load_model()

    x = tensor.to(device)
    if x.dim() == 4:
        x = x.unsqueeze(0)  # (1, 1, H, W, D) 보장

    model.eval()
    with torch.no_grad():
        logits = sliding_window_inference(
            x, roi_size=(128, 128, 128), sw_batch_size=4, predictor=model
        )
        prob_map = torch.softmax(logits, dim=1)[0, 1]  # tumor channel: (H, W, D)
        image = x[0, 0]                                 # (H, W, D)

    global _last_image_np, _last_prob_map_np
    _last_image_np = image.cpu().numpy()
    _last_prob_map_np = prob_map.cpu().numpy()

    frac = _tumor_fraction(prob_map, image)
    is_tumor = frac > TUMOR_VOL_THR
    conf = _confidence_from_fraction(frac, is_tumor)

    prediction = "Tumor" if is_tumor else "Normal"
    tumor_probability = conf if is_tumor else (1.0 - conf)
    normal_probability = 1.0 - tumor_probability

    return {
        "prediction": prediction,
        "tumor_fraction": frac,
        "tumor_probability": tumor_probability,
        "normal_probability": normal_probability,
        "confidence": conf,
    }
