from fastapi import APIRouter, HTTPException
from .schemas import TrainResponse, PredictionRequest, PredictionResponse, HealthResponse
from .model import ColonCancerModel
from .rag_engine import ColonRAGEngine
import pandas as pd

router = APIRouter(tags=["colon"])
model_manager = ColonCancerModel()
rag_engine = ColonRAGEngine()

@router.get("/ai/colon/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "module": "colon"}

@router.post("/ai/colon/train", response_model=TrainResponse)
async def train_model():
    try:
        df = model_manager.load_data()
        eda_plots = model_manager.perform_eda(df)
        comparison, best_name, path = model_manager.train_pipeline(df)
        
        return {
            "message": "Model training completed successfully.",
            "eda_plots": eda_plots,
            "model_comparison": comparison,
            "best_model": best_name,
            "pipeline_path": path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/colon/diagnose", response_model=PredictionResponse)
async def diagnose(request: PredictionRequest):
    # 실제 환경에서는 request.features를 DataFrame으로 변환하는 로직 필요
    # 여기서는 예시로 RAG 엔진 호출만 보여줌
    try:
        # pred_class, prob = model_manager.predict(request.features)
        pred_class, prob = "Yes", 0.85 # 더미 결과
        
        advice = await rag_engine.get_advice(
            query=f"대장암 예측 결과가 {pred_class}이며 확률이 {prob:.2f}인 환자를 위한 조언",
            module="colon" # GW 모듈 태깅 필수
        )
        
        return {
            "prediction": pred_class,
            "probability": prob,
            "advice": advice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
