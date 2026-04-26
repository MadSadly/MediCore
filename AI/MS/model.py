import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
from typing import Optional

# 15개 피부 질환 (학습 폴더명 순서와 반드시 일치해야 함)
DISEASE_CLASSES = [
    ("광선각화증",   "Actinic Keratosis"),
    ("기저세포암",   "Basal Cell Carcinoma"),
    ("멜라닌세포모반", "Melanocytic Nevus"),
    ("보웬병",      "Bowen's Disease"),
    ("비립종",      "Milia"),
    ("사마귀",      "Wart"),
    ("악성흑색종",   "Malignant Melanoma"),
    ("지루각화증",   "Seborrheic Keratosis"),
    ("편평세포암",   "Squamous Cell Carcinoma"),
    ("표피낭종",    "Epidermal Cyst"),
    ("피부섬유종",   "Dermatofibroma"),
    ("피지샘증식증", "Sebaceous Hyperplasia"),
    ("혈관종",      "Hemangioma"),
    ("화농 육아종",  "Pyogenic Granuloma"),
    ("흑색점",      "Lentigo"),
]

NUM_CLASSES = len(DISEASE_CLASSES)

# EfficientNet-B4 기본 입력 크기
INPUT_SIZE = 380

TRANSFORM = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

_model: Optional[nn.Module] = None
_device: Optional[torch.device] = None

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "weights", "skin_efficientnet_b4.pth")


def build_model() -> nn.Module:
    model = models.efficientnet_b4(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, NUM_CLASSES)
    return model


def get_device() -> torch.device:
    global _device
    if _device is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return _device


def load_model() -> nn.Module:
    global _model
    if _model is not None:
        return _model

    device = get_device()
    model = build_model()

    if not os.path.exists(WEIGHTS_PATH):
        raise FileNotFoundError(
            f"모델 가중치 파일이 없습니다: {WEIGHTS_PATH}\n"
            "캐글에서 학습 후 weights/ 폴더에 skin_efficientnet_b4.pth 를 넣어주세요."
        )

    state_dict = torch.load(WEIGHTS_PATH, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    _model = model
    return _model


def preprocess(image_bytes: bytes) -> tuple[torch.Tensor, Image.Image]:
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = TRANSFORM(pil_img).unsqueeze(0).to(get_device())
    return tensor, pil_img


def predict(image_bytes: bytes) -> dict:
    model = load_model()
    tensor, pil_img = preprocess(image_bytes)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

    sorted_idx = probs.argsort()[::-1]
    top3 = [
        {
            "disease_ko": DISEASE_CLASSES[i][0],
            "disease_en": DISEASE_CLASSES[i][1],
            "confidence": round(float(probs[i]) * 100, 2),
        }
        for i in sorted_idx[:3]
    ]

    best_idx = int(sorted_idx[0])
    return {
        "disease_ko":  DISEASE_CLASSES[best_idx][0],
        "disease_en":  DISEASE_CLASSES[best_idx][1],
        "confidence":  top3[0]["confidence"],
        "top3":        top3,
        "class_idx":   best_idx,
        "tensor":      tensor,
        "pil_img":     pil_img,
    }