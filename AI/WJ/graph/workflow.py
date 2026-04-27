from __future__ import annotations

import time
from typing import Optional

from langgraph.graph import END, START, StateGraph

from WJ.graph.nodes import (
    classify_node,
    finalize_node,
    preprocess_node,
    report_node,
    retrieve_node,
    safety_node,
    should_continue,
)
from WJ.graph.state import DiagnosisState
from WJ.schemas.response import DiagnoseResponse

_workflow = None


def build_workflow():
    """
    진단 워크플로우 그래프 조립.

    흐름:
      preprocess → classify → safety → retrieve → report → finalize
      각 단계에서 에러 발생 시 즉시 END (에러 상태 보존)
    """
    graph = StateGraph(DiagnosisState)

    graph.add_node("preprocess", preprocess_node)
    graph.add_node("classify", classify_node)
    graph.add_node("safety", safety_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("report", report_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "preprocess")

    for src, dst in [
        ("preprocess", "classify"),
        ("classify", "safety"),
        ("safety", "retrieve"),
        ("retrieve", "report"),
        ("report", "finalize"),
    ]:
        graph.add_conditional_edges(
            src,
            should_continue,
            {"continue": dst, "error": END},
        )

    graph.add_edge("finalize", END)

    return graph.compile()


def get_workflow():
    """워크플로우 싱글톤."""
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


def run_diagnosis(nifti_path: str, skull_strip: bool = False) -> DiagnoseResponse:
    """
    엔드포인트에서 호출하는 진입점.

    Args:
        nifti_path: 업로드된 NIfTI 파일 경로

    Returns:
        DiagnoseResponse

    Raises:
        RuntimeError: 워크플로우 실행 중 복구 불가능한 에러
    """
    workflow = get_workflow()

    initial_state: DiagnosisState = {
        "nifti_path": nifti_path,
        "skull_strip": skull_strip,
        "tensor": None,
        "classification": None,
        "safety": None,
        "references": [],
        "report": None,
        "response": None,
        "error": None,
        "start_time": time.perf_counter(),
    }

    final_state = workflow.invoke(initial_state)

    if final_state.get("error"):
        raise RuntimeError(final_state["error"])

    return final_state["response"]
