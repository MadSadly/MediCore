"""
임베딩 + pgvector 검색

[개발 모드] GCP_PROJECT_ID 미설정:
    임베딩: BGE-M3  1024차원 (로컬, GCP 불필요)
[실전 모드] GCP_PROJECT_ID 설정:
    임베딩: gemini-embedding-001  output_dimensionality=1024 (Vertex AI)

→ 양쪽 모두 1024차원 — 전환 시 DB 재임베딩 불필요
"""

from __future__ import annotations

import os
import logging

import psycopg2
import psycopg2.extras

logger = logging.getLogger("medicore.kidney.retriever")

MODULE_TAG    = "kidney"
EMBEDDING_DIM = 1024

USE_GEMINI = bool(
    os.getenv("GCP_PROJECT_ID") and
    os.getenv("GCP_PROJECT_ID") != "placeholder"
)

DB_URL = os.getenv(
    "DB_URL",
    "postgresql://medizero:testpassword@127.0.0.1:5432/medizerodb"
)

_embedder = None


def _init_vertexai() -> None:
    import vertexai
    project  = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "asia-northeast3")
    key_path = os.getenv("GCP_KEY_PATH")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID 환경변수가 설정되지 않았습니다.")
    if key_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    vertexai.init(project=project, location=location)


def _get_embedder():
    """임베딩 모델 싱글톤."""
    global _embedder
    if _embedder is not None:
        return _embedder

    if USE_GEMINI:
        _init_vertexai()
        from vertexai.language_models import TextEmbeddingModel
        _embedder = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
        logger.info("임베딩: gemini-embedding-001 (1024차원, Vertex AI)")
    else:
        from FlagEmbedding import FlagModel
        _embedder = FlagModel(
            "BAAI/bge-m3",
            use_fp16=True,
            query_instruction_for_retrieval=(
                "Represent this medical query for searching relevant passages: "
            ),
        )
        logger.info("임베딩: BGE-M3 개발 모드 (1024차원)")

    return _embedder


def embed_query(text: str) -> list[float]:
    """쿼리 텍스트를 1024차원 벡터로 변환."""
    try:
        model = _get_embedder()
        if USE_GEMINI:
            from vertexai.language_models import TextEmbeddingInput
            inputs = [TextEmbeddingInput(text, task_type="RETRIEVAL_QUERY")]
            result = model.get_embeddings(inputs, output_dimensionality=EMBEDDING_DIM)
            return result[0].values
        else:
            return model.encode(text).tolist()
    except Exception as e:
        logger.warning(f"임베딩 실패: {e}")
        return []


def search(query: str, top_k: int = 4) -> list[dict]:
    """medical_knowledge 에서 kidney 데이터만 벡터 검색."""
    if not query:
        return []

    vec = embed_query(query)
    if not vec:
        return []

    try:
        sql = """
            SELECT content, source,
                   1 - (embedding <=> %s::vector) AS score
            FROM   medical_knowledge
            WHERE  module_tag = %s
            ORDER  BY embedding <=> %s::vector
            LIMIT  %s
        """
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (vec, MODULE_TAG, vec, top_k))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"RAG 검색 실패: {e}")
        return []


def multi_search(queries: list, top_k_each: int = 3, max_per_source: int = 2) -> list[dict]:
    """여러 쿼리를 실행하고 출처 다양성을 보장한 결과를 반환.

    - 동일 내용 중복 제거 (content 앞 80자 기준)
    - 동일 출처에서 최대 max_per_source개만 포함
    - score 내림차순 정렬 후 최대 6개 반환
    """
    seen_content: set = set()
    source_count: dict = {}
    merged: list = []

    for q in queries:
        for r in search(q, top_k=top_k_each):
            key = r["content"][:80]
            src = r["source"]

            if key in seen_content:
                continue
            if source_count.get(src, 0) >= max_per_source:
                continue

            seen_content.add(key)
            source_count[src] = source_count.get(src, 0) + 1
            merged.append(r)

    merged.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    logger.info(
        f"multi_search: {len(queries)}개 쿼리 → {len(merged)}건 "
        f"(출처: {list(source_count.keys())})"
    )
    return merged[:6]
