"""
AI/SH/schemas/response.py
안과 CDSS — 응답·공통 Pydantic 스키마
"""

from datetime import datetime
from enum import IntEnum
from typing import Optional, List, Any

from pydantic import BaseModel, Field


# ── 질환 클래스 ───────────────────────────────────────────────

class DiseaseClass(IntEnum):
    NORMAL   = 0
    GLAUCOMA = 1
    CATARACT = 2
    DR       = 3
    AMD      = 4

DISEASE_NAMES = {
    DiseaseClass.NORMAL:   "정상",
    DiseaseClass.GLAUCOMA: "녹내장",
    DiseaseClass.CATARACT: "백내장",
    DiseaseClass.DR:       "당뇨망막병증",
    DiseaseClass.AMD:      "황반변성",
}

STAGE_NAMES = {
    0: "정상",
    1: "경증",
    2: "중등도",
    3: "중증",
    4: "증식성",
}


# ── 이미지 품질 검증 ──────────────────────────────────────────

class ImageQualityResult(BaseModel):
    """이미지 품질 검증 결과 (Laplacian 필터 기반)"""
    is_valid:         bool
    laplacian_var:    float           = Field(..., description="Laplacian 분산값")
    quality_score:    Optional[float] = Field(None, description="정규화된 품질 점수 (0~1)")
    error_code:       Optional[str]   = Field(None, description="에러 코드 (라우터에서 직접 사용)")
    rejection_reason: Optional[str]   = Field(None, description="거부 사유 메시지")


# ── DL 진단 결과 ──────────────────────────────────────────────

class DiseaseScore(BaseModel):
    """개별 질환 점수"""
    disease_id:   int
    disease_name: str
    confidence:   float = Field(..., ge=0.0, le=1.0, description="보정된 확률 (Temperature Scaling 적용)")
    is_positive:  bool  = Field(..., description="Youden's J 임계값 초과 여부")


class StageResult(BaseModel):
    """중증도 단계"""
    stage:      int = Field(..., ge=0, le=4)
    stage_name: str
    disease_id: int


class DLResult(BaseModel):
    """DL 1차 진단 결과 (OPH-07)"""
    model_version:    str               = Field(default="swin_base_v1.0", description="추론에 사용된 모델 버전")
    primary_disease:  DiseaseScore
    all_scores:       List[DiseaseScore]
    stage:            Optional[StageResult]
    gradcam_base64:   Optional[str]       = Field(None, description="GradCAM 히트맵 Base64")
    is_emergency:     bool                = Field(False, description="응급 여부")
    emergency_reason: Optional[str]       = Field(None, description="응급 판정 사유")
    key_findings:     Optional[List[Any]] = Field(default=[], description="주요 병변 좌표 (Phase B 확장용)")


# ── 응급 판정 ─────────────────────────────────────────────────

class EmergencyAlert(BaseModel):
    """응급 강제 알림 (OPH-08)"""
    is_emergency:    bool
    reason:          Optional[str]
    emergency_level: int = Field(0, ge=0, le=3, description="0=정상 1=주의 2=경고 3=응급")


# ── RAG + 리포트 ──────────────────────────────────────────────

class CitationSource(BaseModel):
    """RAG 검색 출처 (OPH-11)"""
    title:   str
    content: str
    source:  str = Field(..., description="대한안과학회 임상진료지침")
    page:    Optional[int]


class ReportChunk(BaseModel):
    """SSE 스트리밍 청크 (OPH-10)"""
    event:      str = Field(..., description="dl_result | rag_retrieved | report_chunk | done")
    data:       str
    session_id: str


# ── 최종 응답 ─────────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    """최종 분석 응답"""
    request_id:        str                  = Field(..., description="요청 추적 ID")
    session_id:        str
    patient_id:        str
    dl_result:         DLResult
    emergency:         EmergencyAlert
    citations:         List[CitationSource] = []
    report:            Optional[str]        = None
    inference_time_ms: float                = Field(..., description="AI 추론 소요 시간 (ms)")
    quality_score:     Optional[float]      = Field(None, description="이미지 선명도 점수")
    timestamp:         str                  = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="AI 추론 완료 UTC 시간 (ISO 8601)"
    )
    status:            str                  = "completed"


# ── 에러 응답 ─────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """에러 응답 (OPH-14)"""
    request_id: Optional[str]
    error_code: str  = Field(..., description="에러 코드")
    message:    str
    detail:     Optional[str]


# ── 에러 코드 상수 ────────────────────────────────────────────

class ErrorCode:
    IMAGE_QUALITY_TOO_LOW  = "IMAGE_QUALITY_TOO_LOW"
    IMAGE_NOT_FUNDUS       = "IMAGE_NOT_FUNDUS"
    MODEL_INFERENCE_FAILED = "MODEL_INFERENCE_FAILED"
    RAG_RETRIEVAL_FAILED   = "RAG_RETRIEVAL_FAILED"
    LLM_GENERATION_FAILED  = "LLM_GENERATION_FAILED"
    INVALID_IMAGE_FORMAT   = "INVALID_IMAGE_FORMAT"
    IMAGE_TOO_LARGE        = "IMAGE_TOO_LARGE"
