"""
AI/SH/llm/report_generator.py
안과 CDSS — Gemini 소견서 비동기 생성 (OPH-10, SSE용 async generator)

담당: 홍승현 (SH)
300자 이내 단일 응답 → stream=False 단순화
"""

import asyncio
from typing import AsyncGenerator, List

from .vertex_client import get_model
from ..schemas.response import DLResult, EmergencyAlert, CitationSource


SYSTEM_PROMPT = """당신은 대한안과학회 임상진료지침과 AAO(미국안과학회) 가이드라인을 기반으로
안과 임상 소견서를 작성하는 AI 보조 시스템입니다.

규칙:
1. 반드시 제공된 근거 문헌에 기반하여 작성하세요.
2. 확실하지 않은 내용은 작성하지 마세요.
3. 최종 진단 및 치료 결정은 담당 의사의 판단임을 명시하세요.
4. 한국어로 작성하세요.
5. 300자 이내의 간결한 소견서를 작성하세요."""

REPORT_MODEL = "gemini-1.5-pro"


async def generate_report_stream(
    dl_result:    DLResult,
    emergency:    EmergencyAlert,
    citations:    List[CitationSource],
    clinical_note: str | None,
) -> AsyncGenerator[str, None]:
    """
    Gemini 소견서: 300자 이내 단일 응답 → stream=False 단순화.
    역할 규칙은 system_instruction, 여기에는 데이터만.
    SSE 호환을 위해 짧은 텍스트를 한 번 yield.
    """
    model = get_model(REPORT_MODEL, system_instruction=SYSTEM_PROMPT)

    citation_text = "\n".join([
        f"- [{c.source}] {c.title}: {c.content[:200]}"
        for c in citations
    ]) if citations else "RAG 검색 결과 없음 — 일반 임상 지식 기반으로 작성"

    prompt = f"""아래 사용자 데이터만 참고하여 임상 소견서를 작성하세요.

[AI 진단 결과]
- 주요 질환: {dl_result.primary_disease.disease_name}
- 확신도: {dl_result.primary_disease.confidence:.1%}
- 중증도: {dl_result.stage.stage_name if dl_result.stage else '미분류'}
- 모델 버전: {dl_result.model_version or "unknown"}
- 응급 여부: {'응급 — ' + (emergency.reason or '') if emergency.is_emergency else '비응급'}

[의사 임상 소견]
{clinical_note or '없음'}

[근거 문헌 (AAO PPP 기반)]
{citation_text}
"""

    def _call_model():
        return model.generate_content(prompt, stream=False)

    response = await asyncio.to_thread(_call_model)
    text = getattr(response, "text", None) or ""
    if text:
        yield text
