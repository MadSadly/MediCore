from __future__ import annotations

import json
import os

from langsmith import traceable

from WJ.llm.vertex_client import generate_text
from WJ.schemas.response import MedicalReport, RetrievedDocument, SafetyAssessment

_SYSTEM_CONTEXT = """당신은 신경영상의학과 전문의를 보조하는 AI 시스템입니다.
MRI 뇌종양 분류 결과와 관련 의학 문헌을 바탕으로 구조화된 의학 리포트를 작성합니다.
반드시 JSON 형식으로만 응답하고, 추측보다는 근거 기반의 신중한 표현을 사용하세요."""

_REPORT_PROMPT = """{system_context}

## 분류 결과
- 판정: {prediction}
- 종양 확률: {tumor_probability:.1%}
- 정상 확률: {normal_probability:.1%}
- 확신도: {confidence:.1%}
- 임상 권고: {clinical_action}

## 관련 의학 문헌
{rag_context}

## 지시사항
위 분류 결과와 의학 문헌을 근거로 아래 JSON 형식의 상세한 임상 의학 리포트를 작성하세요.
- findings: MRI 영상 소견을 구체적으로 서술 (신호 특성, 추정 위치, 크기, 경계, 부종 및 주변 구조 영향, 조영 증강 패턴 가능성 포함) — 5~7문장
- impression: 종합 판정과 임상적 의의를 서술 (판정 근거, 감별진단 우선순위, 임상 중요도 포함) — 3~5문장
- differential_diagnosis: 반드시 고려해야 할 감별진단 4~5개
- recommendations: 구체적인 임상 권고사항 4~6개 (추가 영상검사, 추적 관찰 간격, 전문의 협진, 조직검사 여부 등)
모든 필드는 한국어로 작성하며, "소견상", "시사된다", "권고됨", "고려 가능" 등의 신중한 표현을 사용하세요.
의학 문헌의 근거를 반영하여 구체적이고 임상에 도움이 되는 내용을 작성하세요.

```json
{{
  "findings": "상세한 MRI 영상 소견 (5~7문장)",
  "impression": "종합 판정 및 임상적 의의 (3~5문장)",
  "differential_diagnosis": ["감별진단1", "감별진단2", "감별진단3", "감별진단4", "감별진단5"],
  "recommendations": ["권고사항1", "권고사항2", "권고사항3", "권고사항4", "권고사항5"]
}}
```"""


def _build_rag_context(references: list[RetrievedDocument]) -> str:
    if not references:
        return "관련 문헌 없음"
    lines = []
    for i, doc in enumerate(references, 1):
        lines.append(f"[{i}] (출처: {doc.source})\n{doc.content}")
    return "\n\n".join(lines)


def _parse_report_json(raw: str) -> dict:
    """LLM 출력에서 JSON 파싱. 마크다운 코드블록 자동 제거."""
    text = raw.strip()
    # ```json ... ``` 블록 처리
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


@traceable(name="brain_report_generation")
def generate_report(
    classification: dict,
    safety: SafetyAssessment,
    references: list[RetrievedDocument],
) -> MedicalReport:
    """
    분류 결과 + 안전 평가 + RAG 문헌으로 의학 리포트 생성.

    LangSmith @traceable 데코레이터로 자동 트레이싱됨.
    LANGCHAIN_API_KEY, LANGCHAIN_TRACING_V2=true 환경변수 필요.

    Args:
        classification: predict_tumor() 반환값
        safety: apply_safety_check() 반환값
        references: retrieve() 반환값

    Returns:
        MedicalReport
    """
    prompt = _REPORT_PROMPT.format(
        system_context=_SYSTEM_CONTEXT,
        prediction=classification["prediction"],
        tumor_probability=classification["tumor_probability"],
        normal_probability=classification["normal_probability"],
        confidence=classification["confidence"],
        clinical_action=safety.clinical_action,
        rag_context=_build_rag_context(references),
    )

    raw = generate_text(prompt, temperature=0.2, max_tokens=8192)

    try:
        data = _parse_report_json(raw)
    except json.JSONDecodeError as e:
        # 파싱 실패 시 안전한 기본값 반환
        return MedicalReport(
            findings=f"리포트 생성 중 파싱 오류 발생. 원본: {raw[:200]}",
            impression="파싱 오류로 인해 결과를 표시할 수 없습니다. 전문의 직접 판독을 요청하세요.",
            differential_diagnosis=[],
            recommendations=["전문의 직접 판독 요청"],
        )

    return MedicalReport(
        findings=data.get("findings", ""),
        impression=data.get("impression", ""),
        differential_diagnosis=data.get("differential_diagnosis", []),
        recommendations=data.get("recommendations", []),
    )
