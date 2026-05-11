"""
AI/SH/core/gradcam.py
안과 CDSS — GradCAM++ 히트맵 생성 (OPH-16)

구현 방식:
  ONNX(추론)와 분리, PyTorch(.pth) + timm으로 GradCAM++ 계산
  pytorch-grad-cam(패키지명: grad-cam) 활용
  Swin_Base patch/feature shape 변환 포함
  weights/swin_base_final.pth 없으면 None 반환
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

_LOGGER = logging.getLogger(__name__)

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"
PTH_PATH = WEIGHTS_DIR / "swin_base_final.pth"

IMG_SIZE = 224
IMG_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMG_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _reshape_transform(tensor, height=7, width=7):
    """
    Swin 특성 텐서 → (B, C, H, W) 형태로 맞춤 (GradCAM upsample용).

    timm Swin 블록 `norm1` 출력은 종종 (B, H, W, C) 4텐서.
    어떤 버전/layer에서는 (B, N, C) 시퀀스로 들어오기도 함.
    """
    if tensor.dim() == 4:
        # (B, H, W, C) → (B, C, H, W)
        return tensor.permute(0, 3, 1, 2).contiguous()
    # (B, N, C) → spatial map
    result = tensor.reshape(tensor.size(0), height, width, tensor.size(-1))
    result = result.transpose(2, 3).transpose(1, 2).contiguous()
    return result


class GradCAMEngine:
    """
    Swin_Base GradCAM++ 엔진
    - swin_base_final.pth 로드 (ONNX 추론과 별도)
    - .pth 없으면 None 반환 (graceful fallback)
    - _unavailable=True 이면 재시도 없음 (성능 보호)
    """

    def __init__(self) -> None:
        self._cam = None
        self._loaded = False
        self._unavailable = False

    def _try_load(self) -> bool:
        if self._unavailable:
            return False
        if self._loaded:
            return True

        if not PTH_PATH.exists():
            _LOGGER.warning(
                "GradCAM: %s 없음 → None 반환 (weights 배치 후 서버 재시작)",
                PTH_PATH,
            )
            self._unavailable = True
            return False

        try:
            import torch
            import timm
            from pytorch_grad_cam import GradCAMPlusPlus

            model = timm.create_model(
                "swin_base_patch4_window7_224",
                pretrained=False,
                num_classes=5,
            )
            try:
                state = torch.load(str(PTH_PATH), map_location="cpu", weights_only=False)
            except TypeError:
                state = torch.load(str(PTH_PATH), map_location="cpu")
            if isinstance(state, dict) and "model" in state:
                state = state["model"]
            model.load_state_dict(state, strict=False)
            model.eval()

            target_layers = [model.layers[-1].blocks[-1].norm1]

            self._cam = GradCAMPlusPlus(
                model=model,
                target_layers=target_layers,
                reshape_transform=_reshape_transform,
            )
            self._loaded = True
            _LOGGER.info("GradCAMEngine: swin_base_final.pth 로드 완료")
            return True

        except ImportError as e:
            _LOGGER.warning("GradCAM 의존성 없음 (%s) → None 반환", e)
            self._unavailable = True
            return False
        except Exception as e:
            _LOGGER.exception("GradCAMEngine 로드 실패: %s", e)
            self._unavailable = True
            return False

    def generate(self, img_bgr: np.ndarray, disease_id: int) -> Optional[str]:
        """
        BGR 안저 이미지 + 질환 ID → PNG Base64 히트맵

        Returns:
            Base64 PNG 문자열 | None (weights 없거나 실패 시)
        """
        if not self._try_load():
            return None

        try:
            import torch
            from pytorch_grad_cam.utils.image import show_cam_on_image
            from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

            # 원본 크기 저장
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            h_orig, w_orig = img_rgb.shape[:2]

            # 모델 입력: 224x224 단순 리사이즈
            img_resized = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE))
            img_float = img_resized.astype(np.float32) / 255.0

            # input tensor
            model = self._cam.model
            device = next(model.parameters()).device
            input_tensor = torch.from_numpy(
                ((img_float - IMG_MEAN) / IMG_STD).transpose(2, 0, 1)
            ).unsqueeze(0).float().to(device)

            # GradCAM 실행 (224x224)
            targets = [ClassifierOutputTarget(int(disease_id))]
            grayscale_cam = self._cam(
                input_tensor=input_tensor,
                targets=targets,
            )[0]

            cam_min = grayscale_cam.min()
            cam_max = grayscale_cam.max()
            if cam_max - cam_min > 1e-8:
                grayscale_cam = (grayscale_cam - cam_min) / (cam_max - cam_min)

            # 히트맵을 원본 크기로 리사이즈
            cam_resized = cv2.resize(grayscale_cam, (w_orig, h_orig))

            # 원본 이미지에 오버레이
            img_orig_float = img_rgb.astype(np.float32) / 255.0
            visualization = show_cam_on_image(
                img_orig_float,
                cam_resized,
                use_rgb=True,
                colormap=cv2.COLORMAP_JET,
            )

            # PNG → Base64
            _, buf = cv2.imencode(".png", cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR))
            return base64.b64encode(buf.tobytes()).decode("utf-8")

        except Exception as e:
            _LOGGER.exception("GradCAM 생성 실패: %s", e)
            return None


gradcam_engine = GradCAMEngine()
