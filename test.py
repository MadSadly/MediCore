import os
from vertexai.generative_models import GenerativeModel
from google.cloud import aiplatform
from dotenv import load_dotenv

# .env 로드 및 프로젝트 초기화
load_dotenv()
aiplatform.init(
    project=os.getenv("GCP_PROJECT"),
    location=os.getenv("GCP_REGION", "us-central1")
)

# Gemini 모델은 보통 이름이 정해져 있으므로, 
# 작동 여부를 확인하려면 목록 조회 대신 직접 호출 테스트를 해보는 것이 빠릅니다.
def test_model_access(model_name):
    try:
        model = GenerativeModel(model_name)
        # 아주 짧은 텍스트로 테스트 호출
        response = model.generate_content("hi")
        print(f"✅ {model_name}: 사용 가능")
    except Exception as e:
        print(f"❌ {model_name}: 사용 불가 ({e})")

if __name__ == "__main__":
    # 궁금하신 모델들을 리스트에 넣고 돌려보세요
    models_to_check = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-2.5-flash-lite"
    ]
    
    for m in models_to_check:
        test_model_access(m)