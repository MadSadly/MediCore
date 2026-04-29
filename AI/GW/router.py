from fastapi import APIRouter
from .schemas import DiagnosisRequest, DiagnosisResponse
from .model import ColonModel  # 실제 학습된 모델 로드 (가정)
from .rag_engine import ColonRAGEngine

router = APIRouter()
model = ColonModel()
rag_engine = ColonRAGEngine()

@router.post("/ai/colon/diagnose", response_model=DiagnosisResponse)
async def diagnose_colon_cancer(request: DiagnosisRequest):
    # 1. AI 모델 추론 (CSV 데이터 기반 학습 결과)
    prediction, confidence = model.predict(request)
    
    # 2. RAG 엔진을 통한 의학 지식 결합 (규칙 준수: module='colon')
    # 비만, 당뇨, 염증성 장질환(IBD) 정보를 바탕으로 맞춤 조언 생성
    ai_advice = await rag_engine.get_advice(
        query=f"대장암 환자, BMI: {request.obesity_bmi}, 당뇨여부: {request.diabetes}, IBD여부: {request.ibd}",
        module="colon" # 필터링 필수
    )

    return DiagnosisResponse(
        patient_uid=request.patient_uid,
        prediction="Yes" if prediction == 1 else "No",
        confidence=round(confidence, 2),
        ai_advice=ai_advice
    )

@router.get("/health")
async def health_check():
    return {"status": "ok", "module": "colon"}
