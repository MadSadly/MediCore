"""
RAG 파이프라인 오케스트레이터

LLM 백엔드 우선순위:
  1. GCP_PROJECT_ID 설정  → Vertex AI Gemini  (실전)
  2. OLLAMA_BASE_URL 설정 → Ollama 로컬 LLM  (개발)
  3. 미설정              → 규칙 기반 템플릿  (폴백)

Ollama 사용 시 .env 에 아래 두 줄 추가:
  OLLAMA_BASE_URL=http://<host>:11434
  OLLAMA_MODEL=llama3.1
"""

from __future__ import annotations

import os
import logging

import requests

from .retriever import search, multi_search, USE_GEMINI
from .report_template import (
    build_section1,
    build_llm_prompt,
    parse_llm_sections,
    build_fallback_sections,
    assemble_report,
)

logger = logging.getLogger("medicore.kidney.rag")

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

# ── 한국어 강제 시스템 프롬프트 ───────────────────────────────────
_KOREAN_SYSTEM = (
    "당신은 한국어로만 응답하는 신장내과 전문의 보조 AI입니다. "
    "반드시 한국어로만 작성하십시오. "
    "영어, 베트남어, 중국어 등 어떠한 외국어도 절대 사용하지 마십시오. "
    "의학 전문 용어도 반드시 한국어로 표기하십시오."
)

_gemini  = None
_gen_cfg = None


def _get_gemini():
    """Vertex AI Gemini 모델 싱글톤 (실전 모드 전용)."""
    global _gemini, _gen_cfg
    if _gemini is not None:
        return _gemini

    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig

    project  = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "asia-northeast3")
    key_path = os.getenv("GCP_KEY_PATH")

    if key_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

    vertexai.init(project=project, location=location)

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-001")
    _gemini    = GenerativeModel(model_name, system_instruction=_KOREAN_SYSTEM)
    _gen_cfg   = GenerationConfig(temperature=0.2, max_output_tokens=2048)

    logger.info(f"Gemini LLM 초기화 완료: {model_name}")
    return _gemini


def _call_gemini(prompt: str) -> str:
    model = _get_gemini()
    resp  = model.generate_content(prompt, generation_config=_gen_cfg)
    return resp.text


def _call_ollama(prompt: str) -> str:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model":   OLLAMA_MODEL,
            "system":  _KOREAN_SYSTEM,
            "prompt":  prompt,
            "stream":  False,
            "options": {"temperature": 0.2},
        },
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def _generate_report(
    prediction: str,
    confidence: float,
    input_data: dict,
    contexts: list,
    query: str,
    llm_caller,
) -> str:
    """LLM을 사용하여 섹션 2~4를 채운 뒤 소견서를 조립."""
    section1 = build_section1(prediction, confidence, input_data)
    prompt   = build_llm_prompt(prediction, input_data, contexts, query)

    try:
        raw      = llm_caller(prompt)
        sections = parse_llm_sections(raw)

        # 파싱 실패한 섹션은 폴백으로 보완
        fallback = build_fallback_sections(prediction, contexts, confidence, input_data)
        for key in ("sec2", "sec3", "sec41", "sec42", "sec43", "sec5"):
            if not sections.get(key):
                sections[key] = fallback[key]

        logger.info(f"LLM 소견서 생성 완료 — 파싱 섹션: {list(sections.keys())}")
    except Exception as e:
        logger.warning(f"LLM 생성 실패: {e} — 규칙 기반 폴백 사용")
        sections = build_fallback_sections(prediction, contexts, confidence, input_data)

    return assemble_report(section1, sections)


def generate(
    query: str,
    prediction: str,
    confidence: float,
    input_data: dict,
    contexts: list,
) -> str:
    if USE_GEMINI:
        return _generate_report(
            prediction, confidence, input_data, contexts, query, _call_gemini
        )
    if USE_OLLAMA:
        return _generate_report(
            prediction, confidence, input_data, contexts, query, _call_ollama
        )
    # 폴백: LLM 없이 규칙 기반
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
