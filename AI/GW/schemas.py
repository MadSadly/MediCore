from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TrainResponse(BaseModel):
    message: str
    eda_plots: List[str]
    model_comparison: Dict[str, float]
    best_model: str
    pipeline_path: str

class PredictionRequest(BaseModel):
    # 10개 주요 피처 예시 (실제 데이터셋 컬럼에 맞춰 확장 가능)
    features: List[Any] 

class PredictionResponse(BaseModel):
    prediction: str
    probability: float
    advice: str

class HealthResponse(BaseModel):
    status: str
    module: str