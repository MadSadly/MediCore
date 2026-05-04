"""
AI/SH/rag/retriever.py
Hybrid RAG: Dense (pgvector + BGE-M3) + BM25 → RRF 융합
module_tag = 'eyes' 필터 필수 (CLAUDE.md)
"""

from __future__ import annotations

import logging
import math
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv

_LOGGER = logging.getLogger(__name__)

# MediCore 루트 .env (AI/SH/rag → parents[3])
_load_root = Path(__file__).resolve().parents[3]
load_dotenv(_load_root / ".env")

MODULE_TAG_EYES = "eyes"

_DATABASE_URL_CACHE: str | None = None


def _database_url() -> str:
    """DATABASE_URL 단일 검증(.env 변경 시 프로세스 재시작 필요)."""
    global _DATABASE_URL_CACHE
    if _DATABASE_URL_CACHE is None:
        u = os.getenv("DATABASE_URL")
        if not u or not str(u).strip():
            raise RuntimeError("DATABASE_URL 미설정")
        _DATABASE_URL_CACHE = str(u).strip()
    return _DATABASE_URL_CACHE


def _expanded_bm25_query(query: str, disease_name: str, stage: int) -> str:
    """Dense는 원문 query 유지 · BM25만 질환·stage 토큰으로 보강."""
    q = " ".join((query or "").split())
    dn = " ".join((disease_name or "").split())
    base = f"{q} {dn}".strip()
    suffix = f"stage {stage}" if stage is not None else ""
    out = f"{base} {suffix}".strip()
    return out if out else q


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w가-힣]+", (text or "").lower())


def _title_from_source(source: str) -> str:
    s = (source or "").strip()
    return (s[:160] + "…") if len(s) > 160 else (s or "AAO PPP")


def _bm25_order(query: str, docs: list[dict[str, Any]]) -> list[int]:
    """동일 후보 집합에 대한 BM25 순위 → 문서 인덱스 리스트 (점수 높은 순)."""
    q_terms = _tokenize(query)
    if not q_terms:
        return list(range(len(docs)))

    token_lists = [_tokenize(d.get("content") or "") for d in docs]
    N = len(docs)
    avgdl = sum(len(t) for t in token_lists) / max(N, 1)

    df: dict[str, int] = {}
    for toks in token_lists:
        seen = set(toks)
        for t in seen:
            df[t] = df.get(t, 0) + 1

    k1, b = 1.5, 0.75
    scores: list[tuple[float, int]] = []
    for i, toks in enumerate(token_lists):
        dl = len(toks)
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for term in q_terms:
            if term not in tf:
                continue
            n_df = df.get(term, 0)
            idf = math.log((N - n_df + 0.5) / (n_df + 0.5) + 1.0)
            f = tf[term]
            denom = f + k1 * (1 - b + b * dl / (avgdl or 1.0))
            score += idf * (f * (k1 + 1)) / denom
        scores.append((score, i))

    scores.sort(key=lambda x: (-x[0], x[1]))
    return [idx for _, idx in scores]


def _rrf_fuse(n_docs: int, bm25_ordered_indices: list[int], k_rrf: int = 60) -> list[int]:
    """
    Dense 순위는 SQL 순서 가정 → 인덱스 0..n-1 가 곧 dense rank 순.
    BM25 순위만 별도 부여 후 RRF 점수 합산.
    """
    dense_rank = {i: r + 1 for r, i in enumerate(range(n_docs))}
    bm25_rank = {idx: r + 1 for r, idx in enumerate(bm25_ordered_indices)}
    fused: dict[int, float] = {}
    for i in range(n_docs):
        s = 0.0
        dr = dense_rank.get(i)
        br = bm25_rank.get(i)
        if dr is not None:
            s += 1.0 / (k_rrf + dr)
        if br is not None:
            s += 1.0 / (k_rrf + br)
        fused[i] = s
    order = sorted(fused.keys(), key=lambda i: (-fused[i], i))
    return order


class HybridRetriever:
    """BGE-M3 dense + BM25 + RRF, pgvector `module_tag` 필터."""

    _DENSE_POOL = 50
    _TOP_K_DEFAULT = 3

    def __init__(self) -> None:
        self._model = None

    def load(self) -> None:
        """BGE-M3 미리 로드 (Cold Start 완화)."""
        if self._model is not None:
            return
        try:
            from FlagEmbedding import BGEM3FlagModel

            self._model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
            _LOGGER.info("HybridRetriever: BGEM3FlagModel 로드 완료")
        except Exception as e:
            _LOGGER.exception("HybridRetriever.load 실패: %s", e)
            raise

    def _ensure_model(self) -> None:
        if self._model is None:
            self.load()

    def search(
        self,
        *,
        query: str,
        disease_name: str,
        stage: int,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Dense 후보 풀에서 BM25 재순위 후 RRF로 최종 정렬.

        반환 dict: title, content, source, page (선택)
        """
        self._ensure_model()
        tk = top_k if top_k is not None else self._TOP_K_DEFAULT

        dense_vec = self._model.encode([query], batch_size=1)["dense_vecs"][0]
        vec_lit = "[" + ",".join(str(float(x)) for x in np.asarray(dense_vec).flatten()) + "]"

        import psycopg2

        rows_raw: list[Any] = []
        conn = None
        try:
            conn = psycopg2.connect(_database_url())
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, content, source
                    FROM medical_knowledge
                    WHERE module_tag = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (MODULE_TAG_EYES, vec_lit, self._DENSE_POOL),
                )
                rows_raw = cur.fetchall()
        finally:
            if conn is not None:
                conn.close()

        docs: list[dict[str, Any]] = [
            {
                "id": r[0],
                "content": r[1] or "",
                "source": r[2] or "",
                "title": _title_from_source(str(r[2]) if r[2] else ""),
                "page": None,
            }
            for r in rows_raw
        ]

        if not docs:
            return []

        bm25_q = _expanded_bm25_query(query, disease_name, stage)
        n = len(docs)
        bm25_ord = _bm25_order(bm25_q, docs)
        fused_idx = _rrf_fuse(n, bm25_ord)

        out: list[dict[str, Any]] = []
        for i in fused_idx[:tk]:
            out.append(docs[i])
        return out


hybrid_retriever = HybridRetriever()
