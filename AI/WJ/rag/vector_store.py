from __future__ import annotations

import os
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import execute_values

EMBEDDING_DIM = 1024  # 실제 테이블 vector(1024)에 맞춤
MODULE_NAME = "brain"

_CREATE_EXTENSION = "CREATE EXTENSION IF NOT EXISTS vector;"

# 테이블은 공통 마이그레이션(V1~V4)에서 이미 생성됨.
# 컬럼명: module_tag (module 아님), source NOT NULL
_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS medical_knowledge (
    id         BIGSERIAL PRIMARY KEY,
    module_tag VARCHAR(50)  NOT NULL,
    content    TEXT         NOT NULL,
    source     VARCHAR(500) NOT NULL DEFAULT '',
    embedding  vector({EMBEDDING_DIM}) NOT NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_medical_knowledge_module_tag
    ON medical_knowledge (module_tag);
"""


def _get_conn_params() -> dict:
    """환경변수에서 DB 연결 파라미터 파싱. DB_URL 우선, 없으면 개별 변수."""
    db_url = os.getenv("DB_URL")
    if db_url:
        p = urlparse(db_url)
        return {
            "host": p.hostname,
            "port": p.port or 5432,
            "dbname": p.path.lstrip("/"),
            "user": p.username,
            "password": p.password,
        }
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "medicoredb"),
        "user": os.getenv("DB_USER", "medicore"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def get_connection() -> psycopg2.extensions.connection:
    """새 DB 연결 반환."""
    return psycopg2.connect(**_get_conn_params())


def ensure_table() -> None:
    """medical_knowledge 테이블과 vector 익스텐션이 없으면 생성."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_CREATE_EXTENSION)
            cur.execute(_CREATE_TABLE)
        conn.commit()


def insert_documents(rows: list[dict]) -> int:
    """
    문서 배치 삽입.

    Args:
        rows: [{"content": str, "source": str, "embedding": list[float]}, ...]

    Returns:
        삽입된 행 수
    """
    if not rows:
        return 0

    records = [
        (MODULE_NAME, r["content"], r.get("source", ""), r["embedding"])
        for r in rows
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                "INSERT INTO medical_knowledge (module_tag, content, source, embedding) VALUES %s",
                records,
            )
        conn.commit()

    return len(records)


def search_similar(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    코사인 유사도 기반 검색. 반드시 module='brain' 필터 포함.

    Args:
        query_embedding: 768차원 쿼리 임베딩
        top_k: 반환할 최대 문서 수

    Returns:
        [{"content": str, "source": str, "relevance_score": float}, ...]
    """
    sql = """
        SELECT content, source,
               1 - (embedding <=> %s::vector) AS relevance_score
        FROM medical_knowledge
        WHERE module_tag = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """
    vec_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (vec_str, MODULE_NAME, vec_str, top_k))
            rows = cur.fetchall()

    return [
        {"content": row[0], "source": row[1], "relevance_score": float(row[2])}
        for row in rows
    ]
