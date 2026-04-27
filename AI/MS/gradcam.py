import base64
import io
import numpy as np
from PIL import Image

import torch
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

try:
    from MS.model import load_model, preprocess, INPUT_SIZE
except ImportError:
    from model import load_model, preprocess, INPUT_SIZE


def _get_target_layer():
    model = load_model()
    return [model.features[-1]]


def generate_gradcam_b64(image_bytes: bytes, class_idx: int) -> str:
    model = load_model()
    tensor, pil_img = preprocess(image_bytes)

    target_layers = _get_target_layer()
    targets = [ClassifierOutputTarget(class_idx)]

    with GradCAM(model=model, target_layers=target_layers) as cam:
        grayscale_cam = cam(input_tensor=tensor, targets=targets)[0]

    rgb_resized = np.array(pil_img.resize((INPUT_SIZE, INPUT_SIZE)), dtype=np.float32) / 255.0
    overlay = show_cam_on_image(rgb_resized, grayscale_cam, use_rgb=True)

    buf = io.BytesIO()
    Image.fromarray(overlay).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")