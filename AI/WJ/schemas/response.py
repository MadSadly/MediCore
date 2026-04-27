from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    prediction: Literal["Tumor", "Normal"]
    tumor_probability: float = Field(..., ge=0, le=1)
    normal_probability: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)


class SafetyAssessment(BaseModel):
    risk_level: Literal["low", "moderate", "high_uncertainty"]
    clinical_action: str
    requires_specialist_review: bool


class RetrievedDocument(BaseModel):
    content: str
    source: str
    relevance_score: float


class MedicalReport(BaseModel):
    findings: str
    impression: str
    differential_diagnosis: list[str]
    recommendations: list[str]


class DiagnoseResponse(BaseModel):
    classification: ClassificationResult
    safety: SafetyAssessment
    report: MedicalReport
    references: list[RetrievedDocument]
    disclaimer: str
    metadata: dict


class ErrorResponse(BaseModel):
    error: str
    detail: str
    code: str
