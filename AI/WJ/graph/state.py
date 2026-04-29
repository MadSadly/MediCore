from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict

from WJ.schemas.response import DiagnoseResponse, MedicalReport, RetrievedDocument, SafetyAssessment


class DiagnosisState(TypedDict):
    # 입력 (skull strip은 사전 처리된 파일을 전달)
    nifti_path: str

    # 전처리 결과 (torch.Tensor — in-memory only, 체크포인트 미사용)
    tensor: Optional[Any]

    # 분류 결과
    classification: Optional[dict]

    # 안전 평가
    safety: Optional[SafetyAssessment]

    # RAG 검색 결과
    references: list[RetrievedDocument]

    # LLM 리포트
    report: Optional[MedicalReport]

    # 최종 응답
    response: Optional[DiagnoseResponse]

    # 에러 메시지 (None이면 정상)
    error: Optional[str]

    # 처리 시작 시각 (perf_counter)
    start_time: float
