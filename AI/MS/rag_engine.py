import os
import logging
from functools import lru_cache
from typing import Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger("medicore.skin.rag")

MODULE_TAG = "skin"
EMBED_DIM  = 768

# ── 임베딩 모델 (싱글톤) ───────────────────────────────
_embed_model = None

def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        try:
            import vertexai
            from vertexai.language_models import TextEmbeddingModel
            gcp_project  = os.getenv("GCP_PROJECT_ID")
            gcp_location = os.getenv("GCP_LOCATION", "asia-northeast3")
            if gcp_project:
                vertexai.init(project=gcp_project, location=gcp_location)
            _embed_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
            logger.info("gemini-embedding-001 로드 완료")
        except Exception as e:
            logger.warning(f"임베딩 모델 로드 실패: {e}")
            _embed_model = None
    return _embed_model


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> Optional[list[float]]:
    """텍스트를 768차원 벡터로 변환.
    task_type: RETRIEVAL_DOCUMENT (저장용) | RETRIEVAL_QUERY (검색용)
    """
    model = _get_embed_model()
    if model is None:
        return None
    try:
        from vertexai.language_models import TextEmbeddingInput
        result = model.get_embeddings(
            [TextEmbeddingInput(text=text, task_type=task_type)],
            output_dimensionality=EMBED_DIM,
        )
        return result[0].values
    except Exception as e:
        logger.warning(f"임베딩 생성 실패: {e}")
        return None


# ── DB 연결 ────────────────────────────────────────────
def _get_conn():
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL 환경변수가 없습니다.")
    # postgresql://user:pass@host:port/dbname → psycopg2 DSN
    return psycopg2.connect(db_url)


# ── 지식 검색 ──────────────────────────────────────────
def retrieve_knowledge(query: str, top_k: int = 3) -> list[str]:
    """질환명/증상 쿼리로 관련 의학 지식 검색.
    반드시 module_tag='skin' 필터 포함 (타 모듈 데이터 혼입 방지).
    Vertex AI 미설정 또는 DB 오류 시 빈 리스트 반환 (graceful fallback).
    """
    vector = embed_text(query, task_type="RETRIEVAL_QUERY")
    if vector is None:
        logger.warning("임베딩 실패 — RAG 없이 진행")
        return []

    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT content, source
                    FROM medical_knowledge
                    WHERE module_tag = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (MODULE_TAG, vector, top_k))
                rows = cur.fetchall()
        conn.close()
        return [f"{row[0]}\n[출처: {row[1]}]" for row in rows]
    except Exception as e:
        logger.warning(f"RAG 검색 실패: {e}")
        return []


def insert_knowledge(content: str, source: str) -> bool:
    """의학 지식 텍스트를 임베딩 후 DB에 저장 (seed_knowledge.py에서 사용).
    module_tag='skin' 고정.
    """
    vector = embed_text(content, task_type="RETRIEVAL_DOCUMENT")
    if vector is None:
        logger.error("임베딩 실패 — 삽입 취소")
        return False

    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO medical_knowledge (content, source, module_tag, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                """, (content, source, MODULE_TAG, vector))
        conn.close()
        return True
    except Exception as e:
        logger.error(f"지식 삽입 실패: {e}")
        return False