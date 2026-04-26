import cv2
import numpy as np

SHARPNESS_THRESHOLD = 80.0   # Laplacian variance 기준
BRIGHTNESS_MIN = 30.0         # 너무 어두움
BRIGHTNESS_MAX = 225.0        # 너무 밝음 (과노출)


def check_quality(image_bytes: bytes) -> dict:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {
            "passed": False,
            "sharpness_score": 0.0,
            "brightness_score": 0.0,
            "warning": "이미지를 디코딩할 수 없습니다. JPG 또는 PNG 파일을 업로드해 주세요.",
        }

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())

    passed = True
    warning = None

    if sharpness < SHARPNESS_THRESHOLD:
        passed = False
        warning = "이미지가 흐릿합니다. 선명한 사진을 업로드해 주세요."
    elif brightness < BRIGHTNESS_MIN:
        passed = False
        warning = "이미지가 너무 어둡습니다. 밝은 환경에서 촬영해 주세요."
    elif brightness > BRIGHTNESS_MAX:
        passed = False
        warning = "이미지가 너무 밝습니다 (과노출). 노출을 낮춰 촬영해 주세요."

    return {
        "passed": passed,
        "sharpness_score": round(sharpness, 2),
        "brightness_score": round(brightness, 2),
        "warning": warning,
    }