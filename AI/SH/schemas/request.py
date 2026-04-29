"""
AI/SH/schemas/request.py
안과 CDSS — 요청 Pydantic 스키마
"""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """AI 통합 분석 요청"""
    request_id:       str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="고유 요청 추적 ID (UUID 자동 생성)"
    )
    patient_id:       str           = Field(..., min_length=1, description="환자 ID (공백 불가)")
    patient_age:      Optional[int] = Field(None, ge=0, le=120, description="환자 나이 (0~120)")
    has_diabetes:     bool          = Field(False, description="당뇨 여부")
    has_hypertension: bool          = Field(False, description="고혈압 여부")
    clinical_note:    Optional[str] = Field(None, description="의사 1차 소견")
