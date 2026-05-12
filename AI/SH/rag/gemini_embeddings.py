"""
AI/SH/rag/gemini_embeddings.py
Vertex AI gemini-embedding-001 (768차원) — 문서/쿼리 임베딩 공통

DB(medical_knowledge) 스키마 V13과 동일 차원 사용.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768
MODEL_NAME = "gemini-embedding-001"

_vertex_inited = False
_embed_model = None


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def ensure_vertex() -> None:
    global _vertex_inited
    if _vertex_inited:
        return
    from dotenv import load_dotenv

    load_dotenv(_project_root() / ".env")

    import vertexai

    project = (os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
    location = os.getenv("GCP_LOCATION", "asia-northeast3")
    if not project:
        raise RuntimeError(
            "GCP_PROJECT_ID(또는 GOOGLE_CLOUD_PROJECT)가 .env에 필요합니다. "
            "gemini-embedding-001은 Vertex 초기화가 필요합니다."
        )

    key_path = (os.getenv("GCP_KEY_PATH") or "").strip()
    if key_path:
        kp = Path(key_path)
        if not kp.is_absolute():
            kp = (_project_root() / key_path).resolve()
        if kp.exists():
            os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(kp))
        else:
            _logger.warning("GCP_KEY_PATH 파일을 찾을 수 없음: %s", kp)

    vertexai.init(project=project, location=location)
    _vertex_inited = True
    _logger.info("Vertex AI 초기화 완료 | embedding=%s dim=%s", MODEL_NAME, EMBEDDING_DIM)


def get_embedding_model():
    global _embed_model
    ensure_vertex()
    if _embed_model is None:
        from vertexai.language_models import TextEmbeddingModel

        _embed_model = TextEmbeddingModel.from_pretrained(MODEL_NAME)
        _logger.info("TextEmbeddingModel 로드: %s", MODEL_NAME)
    return _embed_model


def embed_query(text: str) -> list[float]:
    """검색 쿼리 → 768차원 (RETRIEVAL_QUERY)."""
    from vertexai.language_models import TextEmbeddingInput

    m = get_embedding_model()
    inputs = [TextEmbeddingInput(text or "", task_type="RETRIEVAL_QUERY")]
    result = m.get_embeddings(inputs, output_dimensionality=EMBEDDING_DIM)
    return list(result[0].values)


def embed_documents(texts: list[str], batch_size: int = 8) -> list[list[float]]:
    """문서 배치 → 768차원 리스트 (RETRIEVAL_DOCUMENT)."""
    from vertexai.language_models import TextEmbeddingInput

    if not texts:
        return []
    m = get_embedding_model()
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = [TextEmbeddingInput(t, task_type="RETRIEVAL_DOCUMENT") for t in batch]
        results = m.get_embeddings(inputs, output_dimensionality=EMBEDDING_DIM)
        out.extend(list(r.values) for r in results)
    return out
