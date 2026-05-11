"""
AI/SH/llm/vertex_client.py
안과 CDSS — Google Vertex AI Gemini 클라이언트

담당: 홍승현 (SH)
"""

import logging
import os

import vertexai
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)


_initialized = False


def _project_id() -> str:
    """AI/main.py 및 .env 호환: GOOGLE_CLOUD_PROJECT 또는 GCP_PROJECT_ID."""
    for key in ("GOOGLE_CLOUD_PROJECT", "GCP_PROJECT_ID"):
        val = os.getenv(key)
        if val and val.strip():
            return val.strip()
    return ""


def _region() -> str:
    return (
        os.getenv("GOOGLE_CLOUD_REGION")
        or os.getenv("GCP_LOCATION")
        or "asia-northeast3"
    )


def _init_vertex():
    global _initialized
    gcp_key_raw = os.getenv("GCP_KEY_PATH") or ""
    adc = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or ""
    if gcp_key_raw.strip() and not adc.strip():
        expanded = os.path.expanduser(os.path.expandvars(gcp_key_raw.strip()))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = expanded
        logger.info(
            "GCP_KEY_PATH → GOOGLE_APPLICATION_CREDENTIALS 설정됨 | path=%s",
            expanded,
        )

    if _initialized:
        return
    project = _project_id()
    if not project:
        raise RuntimeError(
            "GCP 프로젝트 ID가 설정되지 않았습니다. "
            "GOOGLE_CLOUD_PROJECT 또는 GCP_PROJECT_ID 중 하나를 .env 등에 설정하세요."
        )
    region = _region()
    try:
        vertexai.init(project=project, location=region)
    except Exception:
        logger.exception(
            "Vertex AI vertexai.init 실패 | project=%s | region=%s",
            project,
            region,
        )
        raise
    logger.info(
        "Vertex AI 초기화 완료 | 프로젝트: %s | 리전: %s",
        project,
        region,
    )
    _initialized = True


def get_model(
    model_name: str = "gemini-2.5-flash",
    *,
    system_instruction: str | None = None,
) -> GenerativeModel:
    """
    Vertex GenerativeModel.
    시스템 규칙은 system_instruction으로 분리 가능.
    """
    _init_vertex()
    if system_instruction is not None:
        return GenerativeModel(model_name, system_instruction=system_instruction)
    return GenerativeModel(model_name)
