"""
AI/SH/core/gradcam.py
안과 CDSS — GradCAM 히트맵 생성 (OPH-16)

ONNX 추론과 분리되어 비동기 호출된다.
실제 ONNX GradCAM 로직 연결 전까지 미생성 시 None 반환.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


class GradCAMEngine:
    """BGR 안저 이미지 + 질환 ID → PNG Base64 (엔진 미구현 시 None)."""

    def generate(self, img_bgr: np.ndarray, disease_id: int) -> Optional[str]:
        # TODO(SH): ONNX/Swin 특성맵 연동 후 Base64 문자열 반환
        del img_bgr, disease_id
        return None


gradcam_engine = GradCAMEngine()
