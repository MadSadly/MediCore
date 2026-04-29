from pydantic import BaseModel
from typing import Optional, List


class DiseaseCandidate(BaseModel):
    disease_ko: str
    disease_en: str
    confidence: float


class QualityCheck(BaseModel):
    passed:           bool
    sharpness_score:  float
    brightness_score: float
    warning:          Optional[str] = None


class DiagnoseResponse(BaseModel):
    module:      str = "skin"
    patient_id:  Optional[str] = None
    image_name:  str
    quality_check: QualityCheck

    disease_ko:  Optional[str]   = None
    disease_en:  Optional[str]   = None
    confidence:  Optional[float] = None
    top3:        Optional[List[DiseaseCandidate]] = None

    original_b64:        Optional[str] = None  # 원본 이미지 base64 (비교용)
    gradcam_b64:         Optional[str] = None  # Grad-CAM 히트맵 base64
    gradcam_explanation: Optional[str] = None  # Gemini Vision 판단 근거 텍스트

    report:  str
    success: bool
    error:   Optional[str] = None

    triage_level: Optional[str] = None  # RED | YELLOW | GREEN
    triage_label: Optional[str] = None  # 🔴 즉시 전원 권고 등


class MultiDiagnoseResponse(BaseModel):
    module:     str = "skin"
    patient_id: Optional[str] = None
    total_images: int
    results:      List[DiagnoseResponse]
    summary_report: str