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
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import psycopg2.extras

logger = logging.getLogger("medicore.kidney.retriever")

MODULE_TAG    = "kidney"
EMBEDDING_DIM = 768

USE_GEMINI = bool(
    os.getenv("GCP_PROJECT_ID") and
    os.getenv("GCP_PROJECT_ID") != "placeholder"
)

_db_user = os.getenv("DB_USER", "medicore")
_db_pass = os.getenv("DB_PASSWORD", "")
_db_host = os.getenv("DB_HOST", "127.0.0.1")
_db_port = os.getenv("DB_PORT", "5432")
_db_name = os.getenv("DB_NAME", "medicoredb")

DB_URL = os.getenv(
    "DB_URL",
    f"postgresql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}"
)

_embedder      = None
_embedder_lock = threading.Lock()

_QUERY_INSTRUCTION = (
    "Represent this medical query for searching relevant passages: "
)


class _BGEWrapper:
    """FlagEmbedding 로드 실패 시 sentence-transformers로 자동 폴백하는 래퍼.

    PyTorch 2.6 + accelerate 조합에서 FlagEmbedding이 meta tensor 오류를
    일으키는 경우 sentence-transformers 백엔드로 투명하게 전환된다.
    두 백엔드 모두 동일한 BAAI/bge-m3 가중치를 사용하므로 벡터 호환성 유지.
    """

    def __init__(self):
        try:
            from FlagEmbedding import FlagModel
            self._m = FlagModel(
                "BAAI/bge-m3",
                use_fp16=False,
                query_instruction_for_retrieval=_QUERY_INSTRUCTION,
            )
            self._backend = "flag"
        except Exception as e:
            logger.warning(f"FlagEmbedding 로드 실패 ({e}) — sentence-transformers 폴백")
            from sentence_transformers import SentenceTransformer
            self._m = SentenceTransformer("BAAI/bge-m3", device="cpu")
            self._backend = "sbert"
        logger.info(f"임베딩: BGE-M3 [{self._backend}] (1024차원)")

    def encode(self, text: str):
        if self._backend == "flag":
            vec = self._m.encode(text)
        else:
            vec = self._m.encode(
                _QUERY_INSTRUCTION + text, normalize_embeddings=True
            )
        # DB schema is VECTOR(768); BGE-M3 outputs 1024-dim
        # Matryoshka training keeps first N dims meaningful
        return vec[:EMBEDDING_DIM]


def _init_vertexai() -> None:
    import vertexai
    project  = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "asia-northeast3")
    key_path = os.getenv("GCP_KEY_PATH")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID 환경변수가 설정되지 않았습니다.")
    if key_path:
        key_abs = Path(key_path)
        if not key_abs.is_absolute():
            # .env 파일 위치(프로젝트 루트) 기준 절대경로로 변환
            # retriever.py 위치: AI/NJ/rag/ → parents[3] = 프로젝트 루트
            key_abs = (Path(__file__).resolve().parents[3] / key_path).resolve()
        if not key_abs.exists():
            logger.warning(f"GCP 키 파일을 찾을 수 없음: {key_abs}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_abs)
        logger.info(f"GCP 인증 키: {key_abs}")
    vertexai.init(project=project, location=location)


def _get_embedder():
    """임베딩 모델 싱글톤 — 이중 잠금으로 병렬 초기화 방지."""
    global _embedder
    if _embedder is not None:
        return _embedder
    with _embedder_lock:
        if _embedder is not None:   # 락 획득 전 다른 쓰레드가 이미 초기화한 경우
            return _embedder
        if USE_GEMINI:
            _init_vertexai()
            from vertexai.language_models import TextEmbeddingModel
            _embedder = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
            logger.info("임베딩: gemini-embedding-001 (1024차원, Vertex AI)")
        else:
            _embedder = _BGEWrapper()
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
    """여러 쿼리를 병렬 실행하고 출처 다양성을 보장한 결과를 반환.

    - 임베딩 API 호출을 ThreadPoolExecutor로 병렬화 (순차 → 동시)
    - 동일 내용 중복 제거 (content 앞 80자 기준)
    - 동일 출처에서 최대 max_per_source개만 포함
    - score 내림차순 정렬 후 최대 6개 반환
    """
    valid_queries = [q for q in queries if q]
    all_raw: list[dict] = []

    with ThreadPoolExecutor(max_workers=min(len(valid_queries), 5)) as executor:
        futures = [executor.submit(search, q, top_k_each) for q in valid_queries]
        for future in as_completed(futures):
            try:
                all_raw.extend(future.result())
            except Exception as e:
                logger.warning(f"multi_search 일부 쿼리 실패: {e}")

    # score 내림차순 정렬 후 중복 제거 및 출처 다양성 필터
    all_raw.sort(key=lambda x: float(x.get("score", 0)), reverse=True)

    seen_content: set = set()
    source_count: dict = {}
    merged: list = []

    for r in all_raw:
        key = r["content"][:80]
        src = r["source"]
        if key in seen_content:
            continue
        if source_count.get(src, 0) >= max_per_source:
            continue
        seen_content.add(key)
        source_count[src] = source_count.get(src, 0) + 1
        merged.append(r)

    logger.info(
        f"multi_search: {len(valid_queries)}개 쿼리 병렬 → {len(merged)}건 "
        f"(출처: {list(source_count.keys())})"
    )
    return merged[:6]
