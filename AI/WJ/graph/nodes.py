from __future__ import annotations

import logging
import time

from WJ.core.classifier import predict_tumor, predict_from_tensor
from WJ.core.preprocessing import preprocess_nifti
from WJ.core.safety import apply_safety_check
from WJ.graph.state import DiagnosisState
from WJ.llm.report_generator import generate_report
from WJ.rag.retriever import build_rag_query, retrieve
from WJ.schemas.response import DiagnoseResponse

logger = logging.getLogger("medicore.brain")


def preprocess_node(state: DiagnosisState) -> dict:
    """NIfTI 파일 → 전처리된 텐서."""
    try:
        tensor = preprocess_nifti(state["nifti_path"], apply_skull_strip=state.get("skull_strip", False))
        return {"tensor": tensor}
    except Exception as e:
        logger.error(f"[preprocess] {e}")
        return {"error": f"전처리 실패: {e}"}


def classify_node(state: DiagnosisState) -> dict:
    """전처리 텐서 → 분류 결과."""
    try:
        result = predict_from_tensor(state["tensor"])
        return {"classification": result}
    except Exception as e:
        logger.error(f"[classify] {e}")
        return {"error": f"분류 실패: {e}"}


def safety_node(state: DiagnosisState) -> dict:
    """분류 결과 → 안전 평가."""
    try:
        assessment, _ = apply_safety_check(state["classification"])
        return {"safety": assessment}
    except Exception as e:
        logger.error(f"[safety] {e}")
        return {"error": f"안전 평가 실패: {e}"}


def retrieve_node(state: DiagnosisState) -> dict:
    """분류 결과 → RAG 문헌 검색."""
    try:
        query = build_rag_query(state["classification"])
        docs = retrieve(query, top_k=5)
        return {"references": docs}
    except Exception as e:
        # RAG 실패는 치명적이지 않음 — 빈 문헌으로 계속 진행
        logger.warning(f"[retrieve] RAG 실패, 빈 문헌으로 진행: {e}")
        return {"references": []}


def report_node(state: DiagnosisState) -> dict:
    """분류 + 안전 평가 + RAG → LLM 리포트."""
    try:
        report = generate_report(
            classification=state["classification"],
            safety=state["safety"],
            references=state["references"],
        )
        return {"report": report}
    except Exception as e:
        logger.error(f"[report] {e}")
        return {"error": f"리포트 생성 실패: {e}"}


def finalize_node(state: DiagnosisState) -> dict:
    """모든 결과를 DiagnoseResponse로 조립."""
    from WJ.core.safety import DISCLAIMER
    from WJ.schemas.response import ClassificationResult

    elapsed_ms = (time.perf_counter() - state["start_time"]) * 1000
    clf = state["classification"]

    response = DiagnoseResponse(
        classification=ClassificationResult(
            prediction=clf["prediction"],
            tumor_probability=clf["tumor_probability"],
            normal_probability=clf["normal_probability"],
            confidence=clf["confidence"],
        ),
        safety=state["safety"],
        report=state["report"],
        references=state["references"],
        disclaimer=DISCLAIMER,
        metadata={
            "model_version": "v2",
            "processing_time_ms": round(elapsed_ms, 1),
        },
    )
    return {"response": response}


def should_continue(state: DiagnosisState) -> str:
    """에러 발생 여부에 따라 라우팅."""
    return "error" if state.get("error") else "continue"
