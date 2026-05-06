"""
신부전 진단 요청/응답 스키마
"""
from pydantic import BaseModel
from typing import Optional


class KidneyDiagnoseRequest(BaseModel):
    # 수치형
    age:  Optional[float] = None
    bp:   Optional[float] = None
    sg:   Optional[float] = None
    al:   Optional[float] = None
    su:   Optional[float] = None
    bgr:  Optional[float] = None
    bu:   Optional[float] = None
    sc:   Optional[float] = None
    sod:  Optional[float] = None
    pot:  Optional[float] = None
    hemo: Optional[float] = None
    pcv:  Optional[float] = None
    wc:   Optional[float] = None
    rc:   Optional[float] = None
    egfr: Optional[float] = None

    # 범주형
    rbc:   Optional[str] = None
    pc:    Optional[str] = None
    pcc:   Optional[str] = None
    ba:    Optional[str] = None
    htn:   Optional[str] = None
    dm:    Optional[str] = None
    cad:   Optional[str] = None
    appet: Optional[str] = None
    pe:    Optional[str] = None
    ane:   Optional[str] = None

    # 의사 질문
    query: Optional[str] = None


class Alert(BaseModel):
    level:   str
    code:    str
    message: str
    marker:  str


class KidneyDiagnoseResponse(BaseModel):
    module:             str
    prediction:         str
    confidence:         float
    description:        str
    severity:           str
    dialysis_required:  bool
    probabilities:      dict
    alerts:             list[Alert]
    rag_answer:         str
    rag_sources:        list[str]
    feature_importance: Optional[dict] = None


class HealthResponse(BaseModel):
    module:       str
    status:       str
    model_loaded: bool
