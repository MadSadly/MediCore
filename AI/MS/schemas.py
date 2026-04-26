from pydantic import BaseModel
from typing import Optional, List


class DiseaseCandidate(BaseModel):
    disease_ko: str
    disease_en: str
    confidence: float


class QualityCheck(BaseModel):
    passed: bool
    sharpness_score: float
    brightness_score: float
    warning: Optional[str] = None


class DiagnoseResponse(BaseModel):
    module: str = "skin"
    patient_id: Optional[str] = None
    image_name: str
    quality_check: QualityCheck
    disease_ko: Optional[str] = None
    disease_en: Optional[str] = None
    confidence: Optional[float] = None
    top3: Optional[List[DiseaseCandidate]] = None
    gradcam_b64: Optional[str] = None  # base64 PNG (Grad-CAM overlay)
    report: str
    success: bool
    error: Optional[str] = None


class MultiDiagnoseResponse(BaseModel):
    module: str = "skin"
    patient_id: Optional[str] = None
    total_images: int
    results: List[DiagnoseResponse]
    summary_report: str