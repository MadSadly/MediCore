"""
신부전 진단 API 라우터
"""
import logging
from fastapi import APIRouter
from .schemas import (
    KidneyDiagnoseRequest,
    KidneyDiagnoseResponse,
    HealthResponse,
)
from .model import KidneyPredictor
from .rag_engine import get_rag_engine

logger = logging.getLogger("medicore.kidney")
router = APIRouter()

_predictor = None


def get_predictor() -> KidneyPredictor:
    global _predictor
    if _predictor is None:
        _predictor = KidneyPredictor()
    return _predictor


@router.get("/ai/kidney/health", response_model=HealthResponse)
def kidney_health():
    try:
        get_predictor()
        loaded = True
    except Exception:
        loaded = False
    return HealthResponse(
        module="kidney",
        status="ready" if loaded else "model_not_found",
        model_loaded=loaded,
    )


@router.post("/ai/kidney/diagnose", response_model=KidneyDiagnoseResponse)
async def kidney_diagnose(req: KidneyDiagnoseRequest):
    # 1. 임상 수치 추출
    clinical_data = req.dict(exclude={"query"}, exclude_none=False)

    # 2. TabNet 예측
    predictor  = get_predictor()
    dl_result  = predictor.predict(clinical_data)
    prediction = dl_result["prediction"]

    logger.info(f"신부전 예측: {prediction} "
                f"(신뢰도: {dl_result['confidence']:.3f})")

    # 3. RAG + 소견서
    rag        = get_rag_engine()
    query      = req.query or f"{prediction} 단계의 치료 방향은?"
    rag_result = rag.query_and_generate(query, prediction)

    return KidneyDiagnoseResponse(
        module            = "kidney",
        prediction        = prediction,
        confidence        = dl_result["confidence"],
        description       = dl_result["description"],
        severity          = dl_result["severity"],
        dialysis_required = dl_result["dialysis_required"],
        probabilities     = dl_result["probabilities"],
        rag_answer        = rag_result["answer"],
        rag_sources       = rag_result["sources"],
    )
