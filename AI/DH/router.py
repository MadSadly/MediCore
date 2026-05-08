from fastapi import APIRouter

import os
import json
import tempfile
import torch
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

# DH 패키지 내부의 AI 모듈들을 불러옵니다. (경로에 주의)
from DH.spine_model import load_spine_model
from DH.spine_inference import preprocess_image, get_diagnosis_json
from DH.spine_agent import app as langgraph_app

# APIRouter 생성 (prefix를 주어 엔드포인트를 깔끔하게 관리)
router = APIRouter(prefix="/ai/spine", tags=["Spine Diagnosis"])

vision_model = None
device = None

# [추가] 헬스체크 및 프론트엔드 연결 확인용
@router.get("")
def check_health():
    return {"status": "ok", "message": "척추 AI 서버가 정상 작동 중입니다."}

# 서버 시작 시 모델 로드
@router.on_event("startup")
async def startup_event():
    global vision_model, device
    print("🚀 [DH] PyTorch 척추 모델을 메모리에 로드합니다...")

    # 모델 가중치 파일 경로 (router.py와 같은 폴더에 있다고 가정)
    model_path = os.path.join(os.path.dirname(__file__), 'best_mri_model.pth')
    vision_model, device = load_spine_model(model_path)

    if vision_model:
        vision_model = vision_model.float()
        print("✅ [DH] 비전 AI 모델 로드 완료!")
    else:
        print("❌ [DH] 모델 로드 실패! 파일 경로를 확인하세요.")

# 분석 엔드포인트
@router.post("/analyze")
async def analyze_spine(
        file: UploadFile = File(...),
        clinicalData: str = Form(...)
):
    clinical_dict = json.loads(clinicalData)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # [Step 1] Vision AI (DL) 추론
        input_tensor = preprocess_image(tmp_path).to(device).float()

        with torch.no_grad():
            output = vision_model(input_tensor)
            predictions = torch.sigmoid(output).cpu().numpy()[0]

        mri_result = get_diagnosis_json(predictions)

        # [Step 2] LangGraph (LLM) 통합 진단
        inputs = {
            "raw_data": mri_result,
            "clinical_data": clinical_dict
        }
        final_state = langgraph_app.invoke(inputs)

        # [Step 3] 최종 결과 반환
        response_data = {
            "vision_analysis": mri_result,
            "medical_note": final_state.get("medical_note"),
            "final_report": final_state.get("final_report")
        }
        return JSONResponse(content=response_data)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)