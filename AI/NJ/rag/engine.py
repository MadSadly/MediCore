"""
RAG 파이프라인 오케스트레이터 (Vertex AI Gemini)

LLM 백엔드 우선순위:
  1. GCP_PROJECT_ID 설정  → Vertex AI Gemini
  2. OLLAMA_BASE_URL 설정 → Ollama 로컬 LLM
  3. 미설정              → 규칙 기반 템플릿 (폴백)

.env 필수 설정:
  GCP_PROJECT_ID=your-project-id
  GCP_LOCATION=us-central1
  GEMINI_MODEL=gemini-2.5-flash
  GCP_KEY_PATH=./secrets/gcp-key.json
"""

from __future__ import annotations

import os
import logging
from pathlib import Path

from .retriever import search, multi_search
from .report_template import (
    build_section1,
    build_lc_prompt,
    build_fallback_sections,
    assemble_report,
    get_report_parser,
)

logger = logging.getLogger("medicore.kidney.rag")

_GCP_PROJECT   = os.getenv("GCP_PROJECT_ID", "")
USE_VERTEX_LLM = bool(_GCP_PROJECT and _GCP_PROJECT != "placeholder")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.1")
USE_OLLAMA      = bool(OLLAMA_BASE_URL)

# ── 단계별 다중 서브쿼리 ──────────────────────────────────────────
_STAGE_SUBQUERIES: dict[str, list[str]] = {
    "Normal_Stage1": [
        "CKD Stage 1 normal GFR monitoring cardiovascular risk reduction",
        "blood pressure target CKD prevention lifestyle physical activity",
    ],
    "Stage2": [
        "CKD Stage 2 mild kidney disease management ACE inhibitor ARB proteinuria",
        "blood pressure control CKD 130 80 target antihypertensive",
    ],
    "Stage3": [
        "CKD Stage 3 moderate kidney disease management complications",
        "blood pressure hypertension CKD kidney protection ACE ARB",
        "CKD mineral bone disease calcium phosphorus PTH monitoring Stage 3",
    ],
    "Stage4": [
        "CKD Stage 4 severe kidney disease dialysis preparation vascular access",
        "blood pressure management hypertension CKD Stage 4 antihypertensive",
        "mineral bone disease phosphate binder vitamin D CKD advanced",
        "anemia erythropoietin stimulating agent hemoglobin target CKD",
    ],
    "Stage5": [
        "ESRD end stage renal disease dialysis kidney transplant management",
        "dialysis patient blood pressure cardiovascular management ESRD",
        "mineral bone disease phosphorus management ESRD dialysis",
    ],
}

_KOREAN_SYSTEM = (
    "당신은 한국어로만 응답하는 신장내과 전문의 보조 AI입니다. "
    "반드시 한국어로만 작성하십시오. "
    "영어, 베트남어, 중국어 등 어떠한 외국어도 절대 사용하지 마십시오. "
    "의학 전문 용어도 반드시 한국어로 표기하십시오."
)

_gemini_llm = None
_ollama_llm = None


def _get_gemini_llm():
    """Vertex AI Gemini LangChain 모델 싱글톤."""
    global _gemini_llm
    if _gemini_llm is not None:
        return _gemini_llm

    import vertexai
    from langchain_google_vertexai import ChatVertexAI

    project  = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    key_path = os.getenv("GCP_KEY_PATH")

    if key_path:
        key_abs = Path(key_path)
        if not key_abs.is_absolute():
            key_abs = (Path(__file__).resolve().parents[3] / key_path).resolve()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_abs)
        logger.info(f"GCP 인증 키: {key_abs}")

    vertexai.init(project=project, location=location)

    model_name  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    _gemini_llm = ChatVertexAI(
        model=model_name,
        project=project,
        location=location,
        temperature=0.2,
        max_output_tokens=8192,
    )

    logger.info(f"Vertex AI Gemini 초기화 완료: {model_name} @ {location}")
    return _gemini_llm


def _get_ollama_llm():
    """Ollama LangChain 모델 싱글톤."""
    global _ollama_llm
    if _ollama_llm is not None:
        return _ollama_llm

    from langchain_community.chat_models import ChatOllama

    _ollama_llm = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0.2,
    )

    logger.info(f"Ollama LLM 초기화 완료: {OLLAMA_MODEL}")
    return _ollama_llm


def _generate_report(
    prediction: str,
    confidence: float,
    input_data: dict,
    contexts: list,
    query: str,
    llm,
) -> str:
    """LCEL 체인(llm | PydanticOutputParser)으로 섹션 2~5 생성 후 소견서 조립."""
    from langchain_core.messages import HumanMessage, SystemMessage

    section1 = build_section1(prediction, confidence, input_data)
    parser   = get_report_parser()

    prompt_text = build_lc_prompt(
        prediction, input_data, contexts, query,
        format_instructions=parser.get_format_instructions(),
    )

    messages = [
        SystemMessage(content=_KOREAN_SYSTEM),
        HumanMessage(content=prompt_text),
    ]

    chain = llm | parser

    try:
        result   = chain.invoke(messages)
        sections = result.model_dump()

        fallback = build_fallback_sections(prediction, contexts, confidence, input_data)
        for key in ("sec2", "sec3", "sec41", "sec42", "sec43", "sec5"):
            if not sections.get(key):
                sections[key] = fallback[key]

        logger.info(f"Vertex AI 소견서 생성 완료 — 섹션: {[k for k, v in sections.items() if v]}")
    except Exception as e:
        logger.warning(f"LangChain 생성 실패: {e} — 규칙 기반 폴백 사용")
        sections = build_fallback_sections(prediction, contexts, confidence, input_data)

    return assemble_report(section1, sections)


def generate(
    query: str,
    prediction: str,
    confidence: float,
    input_data: dict,
    contexts: list,
) -> str:
    if USE_VERTEX_LLM:
        return _generate_report(
            prediction, confidence, input_data, contexts, query, _get_gemini_llm()
        )
    if USE_OLLAMA:
        return _generate_report(
            prediction, confidence, input_data, contexts, query, _get_ollama_llm()
        )
    section1 = build_section1(prediction, confidence, input_data)
    sections = build_fallback_sections(prediction, contexts, confidence, input_data)
    return assemble_report(section1, sections)


def query_and_generate(
    query: str,
    prediction: str,
    confidence: float = 0.0,
    input_data: dict | None = None,
) -> dict:
    if input_data is None:
        input_data = {}

    main_query  = query or f"CKD {prediction} 치료 관리"
    sub_queries = _STAGE_SUBQUERIES.get(prediction, [])
    contexts    = multi_search([main_query] + sub_queries)

    if not contexts:
        contexts = search(main_query)

    answer = generate(query, prediction, confidence, input_data, contexts)
    return {
        "answer":   answer,
        "sources":  list({c["source"] for c in contexts}),
        "contexts": len(contexts),
    }
