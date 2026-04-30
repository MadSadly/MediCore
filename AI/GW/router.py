from fastapi import APIRouter, HTTPException, BackgroundTasks
from GW.model import ColonCancerModel
from GW.rag_engine import ColonRAGEngine
from GW.schemas import TrainResponse, PredictionRequest, PredictionResponse, HealthResponse

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
    try:
        logger.info(f"[COLON] Diagnosis requested. Input size: {len(request.features)}")
        
        # 4. 상담 단계: 모델 로드 및 예측
        pred_class, prob = model_manager.predict(request.features)
        
        # LLM 소견서 생성 (예측 데이터 포함)
        input_summary = f"입력 데이터: {request.features}"
        prediction_text = "위험(사망 가능성 높음)" if pred_class == 1 else "안전(생존 가능성 높음)"
        
        query = f"""
        환자 예측 결과: {prediction_text}
        예측 확률(위험도): {prob*100:.2f}%
        {input_summary}
        """
        
        advice = await rag_engine.get_advice(
            query=query,
            module="colon"
        )
        
        return {
            "prediction": str(pred_class),
            "probability": float(prob),
            "advice": advice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
