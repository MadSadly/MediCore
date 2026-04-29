import torch
import numpy as np
from PIL import Image
from spine_model import load_spine_model  # 방금 만든 파일에서 함수 가져오기

# ---------------------------------------------------------
# 1. 이미지 전처리 함수 (Pre-processing)
# 모델은 224x224 크기와 특정 숫자 범위(정규화)를 원합니다.
# ---------------------------------------------------------
def preprocess_image(image_path):
    image = Image.open(image_path).convert('RGB')
    image = image.resize((224, 224))

    # 숫자로 변환 (0~1 사이로)
    img_array = np.array(image).astype(np.float32) / 255.0

    # 평균/표준편차 정규화 (모델 학습 시 사용된 값)
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    img_array = (img_array - mean) / std

    # PyTorch 포맷으로 변경 (가로, 세로, 채널 -> 채널, 가로, 세로)
    img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
    return img_tensor

# ---------------------------------------------------------
# 2. 결과 해석 및 JSON 변환 함수
# ---------------------------------------------------------
def get_diagnosis_json(predictions):
    conditions = ['Spinal Canal Stenosis', 'Neural Foraminal Narrowing', 'Subarticular Stenosis']
    severities = ['Normal_Mild', 'Moderate', 'Severe']

    # 9개의 숫자를 3x3 표 형태로 다시 정렬
    pred_matrix = predictions.reshape(3, 3)

    result_json = {}
    for i, condition in enumerate(conditions):
        result_json[condition] = {
            severities[j]: float(pred_matrix[i, j]) for j in range(3)
        }
    return result_json

# ---------------------------------------------------------
# 3. 메인 실행 로직
# ---------------------------------------------------------
if __name__ == "__main__":
    # 모델 로드
    model, device = load_spine_model('best_mri_model.pth')


if __name__ == "__main__":
    model, device = load_spine_model('best_mri_model.pth')

    if model:
        # 모델 자체를 float 타입으로 확실히 변경
        model = model.float()

        test_img_path = 'D:/rlaekagus329/data/processed_spider_jpgs/2_t2.jpg'

        # 1단계: 전처리 및 float 변환
        input_data = preprocess_image(test_img_path).to(device).float()

        # 2단계: 모델 추론
        with torch.no_grad():
            output = model(input_data)
            predictions = torch.sigmoid(output).cpu().numpy()[0]

        # 3단계: JSON 결과 생성
        final_result = get_diagnosis_json(predictions)

        print("\n🔍 --- [AI 분석 결과 JSON] ---")
        import json
        print(json.dumps(final_result, indent=2))
        print("-----------------------------\n")