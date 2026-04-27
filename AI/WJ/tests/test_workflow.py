from __future__ import annotations

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from WJ.graph.nodes import should_continue
from WJ.graph.state import DiagnosisState
from WJ.graph.workflow import build_workflow
from WJ.schemas.response import (
    DiagnoseResponse,
    MedicalReport,
    RetrievedDocument,
    SafetyAssessment,
)

# ── 공통 픽스처 ───────────────────────────────────────────────────────

@pytest.fixture
def base_state() -> DiagnosisState:
    return {
        "nifti_path": "/tmp/test.nii.gz",
        "tensor": torch.zeros(1, 1, 96, 96, 96),
        "classification": {
            "prediction": "Tumor",
            "tumor_probability": 0.97,
            "normal_probability": 0.03,
            "confidence": 0.97,
        },
        "safety": SafetyAssessment(
            risk_level="moderate",
            clinical_action="추가 검사 권고",
            requires_specialist_review=True,
        ),
        "references": [
            RetrievedDocument(content="뇌종양 소견", source="WHO 2021", relevance_score=0.91)
        ],
        "report": MedicalReport(
            findings="전두엽 병변 관찰",
            impression="고등급 신경교종 의심",
            differential_diagnosis=["GBM", "전이성 종양"],
            recommendations=["신경외과 협진"],
        ),
        "response": None,
        "error": None,
        "start_time": time.perf_counter(),
    }


# ── should_continue 라우팅 테스트 ────────────────────────────────────

def test_should_continue_no_error(base_state):
    assert should_continue(base_state) == "continue"


def test_should_continue_with_error(base_state):
    base_state["error"] = "전처리 실패"
    assert should_continue(base_state) == "error"


# ── 개별 노드 단위 테스트 ─────────────────────────────────────────────

@patch("WJ.graph.nodes.preprocess_nifti", return_value=torch.zeros(1, 1, 96, 96, 96))
def test_preprocess_node_success(mock_pre, base_state):
    from WJ.graph.nodes import preprocess_node
    result = preprocess_node(base_state)
    assert "tensor" in result
    assert result["tensor"].shape == (1, 1, 96, 96, 96)


@patch("WJ.graph.nodes.preprocess_nifti", side_effect=FileNotFoundError("없음"))
def test_preprocess_node_error(mock_pre, base_state):
    from WJ.graph.nodes import preprocess_node
    result = preprocess_node(base_state)
    assert "error" in result
    assert result["error"] is not None


@patch("WJ.graph.nodes.predict_from_tensor", return_value={
    "prediction": "Tumor", "tumor_probability": 0.97,
    "normal_probability": 0.03, "confidence": 0.97,
})
def test_classify_node_success(mock_clf, base_state):
    from WJ.graph.nodes import classify_node
    result = classify_node(base_state)
    assert result["classification"]["prediction"] == "Tumor"


@patch("WJ.graph.nodes.retrieve", side_effect=Exception("DB 연결 실패"))
@patch("WJ.graph.nodes.build_rag_query", return_value="뇌종양 쿼리")
def test_retrieve_node_rag_failure_continues(mock_query, mock_retrieve, base_state):
    """RAG 실패 시 에러 없이 빈 references로 계속 진행."""
    from WJ.graph.nodes import retrieve_node
    result = retrieve_node(base_state)
    assert result["references"] == []
    assert "error" not in result


# ── 워크플로우 통합 테스트 ────────────────────────────────────────────

@patch("WJ.graph.nodes.preprocess_nifti", return_value=torch.zeros(1, 1, 96, 96, 96))
@patch("WJ.graph.nodes.predict_from_tensor", return_value={
    "prediction": "Tumor", "tumor_probability": 0.97,
    "normal_probability": 0.03, "confidence": 0.97,
})
@patch("WJ.graph.nodes.retrieve", return_value=[])
@patch("WJ.graph.nodes.build_rag_query", return_value="쿼리")
@patch("WJ.graph.nodes.generate_report", return_value=MedicalReport(
    findings="전두엽 병변", impression="종양 의심",
    differential_diagnosis=["GBM"], recommendations=["협진"],
))
def test_full_workflow_success(m1, m2, m3, m4, m5):
    workflow = build_workflow()
    state = {
        "nifti_path": "/tmp/test.nii.gz",
        "tensor": None, "classification": None, "safety": None,
        "references": [], "report": None, "response": None,
        "error": None, "start_time": time.perf_counter(),
    }
    final = workflow.invoke(state)
    assert final["error"] is None
    assert isinstance(final["response"], DiagnoseResponse)
    assert final["response"].classification.prediction == "Tumor"


@patch("WJ.graph.nodes.preprocess_nifti", side_effect=FileNotFoundError("파일 없음"))
def test_full_workflow_early_exit_on_error(mock_pre):
    """전처리 실패 시 이후 노드 실행 없이 END."""
    workflow = build_workflow()
    state = {
        "nifti_path": "/tmp/missing.nii.gz",
        "tensor": None, "classification": None, "safety": None,
        "references": [], "report": None, "response": None,
        "error": None, "start_time": time.perf_counter(),
    }
    final = workflow.invoke(state)
    assert final["error"] is not None
    assert final["response"] is None
