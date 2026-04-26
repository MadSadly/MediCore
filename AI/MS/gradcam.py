import base64
import io
import numpy as np
from PIL import Image

import torch
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from model import load_model, preprocess, INPUT_SIZE


def _get_target_layer():
    """EfficientNet-B4 마지막 Conv Block (Grad-CAM 기준 레이어)"""
    model = load_model()
    return [model.features[-1]]


def generate_gradcam_b64(image_bytes: bytes, class_idx: int) -> str:
    """
    Grad-CAM 히트맵을 원본 이미지에 오버레이한 뒤 base64 PNG 문자열로 반환.
    프론트엔드에서 <img src="data:image/png;base64,..."> 로 바로 사용 가능.
    """
    model = load_model()
    tensor, pil_img = preprocess(image_bytes)

    target_layers = _get_target_layer()
    targets = [ClassifierOutputTarget(class_idx)]

    with GradCAM(model=model, target_layers=target_layers) as cam:
        grayscale_cam = cam(input_tensor=tensor, targets=targets)[0]  # (H, W)

    # 원본 이미지를 모델 입력 크기로 리사이즈 후 float 배열로 변환
    rgb_resized = np.array(pil_img.resize((INPUT_SIZE, INPUT_SIZE)), dtype=np.float32) / 255.0

    overlay = show_cam_on_image(rgb_resized, grayscale_cam, use_rgb=True)  # (H, W, 3) uint8

    buf = io.BytesIO()
    Image.fromarray(overlay).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")