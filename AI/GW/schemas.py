from pydantic import BaseModel

class DiagnosisRequest(BaseModel):
    patient_uid: str
    age: int
    gender: str
    tumor_size_mm: float #  종양 크기 (mm)
    obesity_bmi: str  # Normal, Overweight, etc. 비만체질량지수
    diabetes: str     # Yes/No 당뇨여부
    ibd: str          # Inflammatory_Bowel_Disease (Yes/No) 염증성 장질환 여부
    genetic_mutation: str # 유전자 변이 정보 (예: KRAS, BRAF 등)

class DiagnosisResponse(BaseModel):
    patient_uid: str
    prediction: str    # Survival_Prediction (Yes/No)
    confidence: float
    ai_advice: str     # RAG를 통해 생성된 조언
