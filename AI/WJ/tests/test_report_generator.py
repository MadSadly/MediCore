from __future__ import annotations

import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from WJ.llm.report_generator import _build_rag_context, _parse_report_json, generate_report
from WJ.schemas.response import MedicalReport, RetrievedDocument, SafetyAssessment

# ── 픽스처 ────────────────────────────────────────────────────────────

@pytest.fixture
def tumor_clf():
    return {
        "prediction": "Tumor",
        "tumor_probability": 0.97,
        "normal_probability": 0.03,
        "confidence": 0.97,
    }

@pytest.fixture
def safety():
    return SafetyAssessment(
        risk_level="moderate",
        clinical_action="추가 검사 권고",
        requires_specialist_review=True,
    )

@pytest.fixture
def references():
    return [
        RetrievedDocument(content="글리오마 MRI 소견 설명", source="WHO 2021", relevance_score=0.91),
        RetrievedDocument(content="뇌종양 치료 권고사항", source="NCCN 2024", relevance_score=0.87),
    ]

_SAMPLE_REPORT_JSON = {
    "findings": "T1 강조 영상에서 좌측 전두엽에 불규칙한 조영증강 병변이 관찰됩니다.",
    "impression": "좌측 전두엽 고등급 신경교종 의심 소견입니다.",
    "differential_diagnosis": ["교모세포종(GBM)", "역형성 성상세포종", "전이성 뇌종양"],
    "recommendations": ["신경외과 협진", "MR spectroscopy 추가 촬영", "다학제 팀 회의"],
}

# ── 단위 테스트 ───────────────────────────────────────────────────────

def test_build_rag_context_with_docs(references):
    ctx = _build_rag_context(references)
    assert "WHO 2021" in ctx
    assert "글리오마" in ctx
    assert "[1]" in ctx
    assert "[2]" in ctx


def test_build_rag_context_empty():
    ctx = _build_rag_context([])
    assert ctx == "관련 문헌 없음"


def test_parse_report_json_plain():
    raw = json.dumps(_SAMPLE_REPORT_JSON)
    data = _parse_report_json(raw)
    assert data["impression"] == _SAMPLE_REPORT_JSON["impression"]


def test_parse_report_json_markdown_block():
    raw = "```json\n" + json.dumps(_SAMPLE_REPORT_JSON) + "\n```"
    data = _parse_report_json(raw)
    assert data["findings"] == _SAMPLE_REPORT_JSON["findings"]


@patch("WJ.llm.report_generator.generate_text", return_value=json.dumps(_SAMPLE_REPORT_JSON))
def test_generate_report_success(mock_llm, tumor_clf, safety, references):
    report = generate_report(tumor_clf, safety, references)
    assert isinstance(report, MedicalReport)
    assert "전두엽" in report.findings
    assert len(report.differential_diagnosis) == 3
    assert len(report.recommendations) == 3
    mock_llm.assert_called_once()


@patch("WJ.llm.report_generator.generate_text", return_value="invalid json {{{{")
def test_generate_report_parse_error_returns_fallback(mock_llm, tumor_clf, safety, references):
    report = generate_report(tumor_clf, safety, references)
    assert isinstance(report, MedicalReport)
    assert "전문의 직접 판독" in report.recommendations[0]


@patch("WJ.llm.report_generator.generate_text", return_value=json.dumps(_SAMPLE_REPORT_JSON))
def test_generate_report_prompt_contains_key_info(mock_llm, tumor_clf, safety, references):
    generate_report(tumor_clf, safety, references)
    prompt_used = mock_llm.call_args[0][0]
    assert "Tumor" in prompt_used
    assert "97.0%" in prompt_used or "97" in prompt_used
    assert "추가 검사 권고" in prompt_used
    assert "WHO 2021" in prompt_used
