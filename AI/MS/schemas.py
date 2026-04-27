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
    # 트리아지 및 임상 정보
    triage_level: Optional[str] = None   # "RED" | "YELLOW" | "GREEN"
    triage_label: Optional[str] = None   # "🔴 즉시 전원 권고" 등
    clinical_features: Optional[str] = None  # ABCDE / 임상 특징
    clinical_action: Optional[str] = None    # 권고 처치
    guideline: Optional[str] = None          # 참고 가이드라인


class MultiDiagnoseResponse(BaseModel):
    module: str = "skin"
    patient_id: Optional[str] = None
    total_images: int
    results: List[DiagnoseResponse]
    summary_report: str