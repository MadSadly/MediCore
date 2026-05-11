"""
AI/SH/llm/report_generator.py
안과 CDSS — Gemini 소견서 비동기 생성 (OPH-10, SSE용 async generator)

담당: 홍승현 (SH)
3000자 이내 단일 응답 → stream=False 단순화
"""

import asyncio
import logging
from typing import AsyncGenerator, List

from .vertex_client import get_model
from ..schemas.response import DLResult, EmergencyAlert, CitationSource

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """당신은 대한안과학회 임상진료지침과 AAO(미국안과학회) 가이드라인을 기반으로
안과 임상 소견서를 작성하는 AI 보조 시스템입니다.

소견서는 반드시 아래 6개 항목을 모두 포함하여 1500자 이상 3000자 이내로 작성하세요.

[필수 포함 항목]
1. 주요 진단 및 소견 요약 (AI 분석 결과 기반)
2. 중증도 분류 및 임상적 의의
3. AAO 가이드라인 기반 권장 치료 방향
4. 추적 관찰 및 검사 계획
5. 응급 여부 판단 근거 (응급이면 즉시 조치 사항 포함)
6. 주의사항 및 면책 조항

규칙:
- 반드시 제공된 근거 문헌에 기반하여 작성하세요.
- 확실하지 않은 내용은 작성하지 마세요.
- 한국어로 작성하세요.
- 최종 진단 및 치료 결정은 반드시 담당 의사의 판단에 따름을 명시하세요."""

REPORT_MODEL = "gemini-2.5-flash"


async def generate_report_stream(
    dl_result:    DLResult,
    emergency:    EmergencyAlert,
    citations:    List[CitationSource],
    clinical_note: str | None,
) -> AsyncGenerator[str, None]:
    """
    Gemini 소견서: 3000자 이내 단일 응답 → stream=False 단순화.
    역할 규칙은 system_instruction, 여기에는 데이터만.
    SSE 호환을 위해 짧은 텍스트를 한 번 yield.
    """
    logger.info(
        "소견서 생성 시작 | model=%s | disease=%s | citations=%d",
        REPORT_MODEL,
        dl_result.primary_disease.disease_name,
        len(citations),
    )

    model = get_model(REPORT_MODEL, system_instruction=SYSTEM_PROMPT)

    citation_text = "\n".join([
        f"- [{c.source}] {c.title}: {c.content[:200]}"
        for c in citations
    ]) if citations else "RAG 검색 결과 없음 — 일반 임상 지식 기반으로 작성"

    prompt = f"""아래 데이터를 바탕으로 6개 항목을 포함한 상세 임상 소견서를 작성하세요.

[AI 진단 결과]
- 주요 질환: {dl_result.primary_disease.disease_name}
- 확신도: {dl_result.primary_disease.confidence:.1%}
- 중증도: {dl_result.stage.stage_name if dl_result.stage else '미분류'} (Stage {dl_result.stage.stage if dl_result.stage else 'N/A'})
- 모델 버전: {dl_result.model_version or "unknown"}
- 응급 여부: {'⚠️ 응급 — ' + (emergency.reason or '') if emergency.is_emergency else '비응급'}
- 응급 레벨: {emergency.emergency_level}/3

[전체 질환 확신도]
{chr(10).join([f"- {s.disease_name}: {s.confidence:.1%}" for s in dl_result.all_scores])}

[의사 임상 소견]
{clinical_note or '없음'}

[근거 문헌 (AAO PPP 기반, RAG 검색 결과)]
{citation_text}

위 데이터를 바탕으로 1500자 이상 3000자 이내의 상세한 임상 소견서를 한국어로 작성하세요.
6개 항목(진단요약, 중증도, 치료방향, 추적계획, 응급판단, 주의사항)을 모두 포함하세요."""

    def _call_model():
        return model.generate_content(prompt, stream=False)

    response = await asyncio.to_thread(_call_model)
    text = getattr(response, "text", None) or ""
    if text:
        logger.info("소견서 생성 완료 | length=%d", len(text))
        yield text
