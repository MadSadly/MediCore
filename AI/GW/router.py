from fastapi import APIRouter
from pydantic import BaseModel
from .model import ColonModel
from .rag_engine import get_llm_advice

class ColonInput(BaseModel):
    patient_uid: str
    Age: int
    Gender: str
    Tumor_Size_mm: float
    Family_History: str
    Smoking_History: str
    Obesity_BMI: str

router = APIRouter()
model = ColonModel()

@router.post("/ai/colon/diagnose")
async def diagnose(data: ColonInput):
    # 1. Prediction
    pred_label, confidence = model.predict(data.dict(exclude={'patient_uid'}))
    
    # 2. RAG Advice
    advice = get_llm_advice(pred_label, data.dict())
    
    return {
        "prediction": pred_label,
        "confidence": confidence,
        "llm_advice": advice
    }
