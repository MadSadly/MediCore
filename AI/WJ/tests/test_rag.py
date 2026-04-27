from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from WJ.rag.vector_store import _get_conn_params
from WJ.rag.retriever import build_rag_query
from WJ.schemas.response import RetrievedDocument


# ── vector_store 단위 테스트 ─────────────────────────────────────────

def test_conn_params_from_db_url(monkeypatch):
    monkeypatch.setenv("DB_URL", "postgresql://user:pass@myhost:5433/mydb")
    monkeypatch.delenv("DB_HOST", raising=False)
    params = _get_conn_params()
    assert params["host"] == "myhost"
    assert params["port"] == 5433
    assert params["dbname"] == "mydb"
    assert params["user"] == "user"


def test_conn_params_from_individual_envs(monkeypatch):
    monkeypatch.delenv("DB_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "medicoredb")
    monkeypatch.setenv("DB_USER", "medicore")
    params = _get_conn_params()
    assert params["host"] == "localhost"
    assert params["dbname"] == "medicoredb"


# ── retriever 단위 테스트 ───────────────────────────────────────────

def test_build_rag_query_tumor():
    clf = {"prediction": "Tumor", "confidence": 0.97}
    query = build_rag_query(clf)
    assert "뇌종양" in query or "글리오마" in query


def test_build_rag_query_normal():
    clf = {"prediction": "Normal", "confidence": 0.98}
    query = build_rag_query(clf)
    assert "정상" in query


@patch("WJ.rag.retriever.embed_query", return_value=[0.1] * 768)
@patch("WJ.rag.retriever.search_similar", return_value=[
    {"content": "뇌종양 MRI 소견", "source": "TestSource", "relevance_score": 0.92}
])
def test_retrieve_returns_documents(mock_search, mock_embed):
    from WJ.rag.retriever import retrieve
    docs = retrieve("뇌종양 진단", top_k=1)
    assert len(docs) == 1
    assert isinstance(docs[0], RetrievedDocument)
    assert docs[0].relevance_score == 0.92
    # module 필터가 search_similar에 위임됨을 확인
    mock_search.assert_called_once()


# ── knowledge_loader 단위 테스트 ────────────────────────────────────

@patch("WJ.rag.knowledge_loader.ensure_table")
@patch("WJ.rag.knowledge_loader.insert_documents", return_value=2)
@patch("WJ.rag.knowledge_loader.embed_documents", return_value=[[0.0] * 768, [0.0] * 768])
def test_load_documents(mock_embed, mock_insert, mock_ensure):
    from WJ.rag.knowledge_loader import load_documents
    docs = [
        {"content": "뇌종양 내용1", "source": "src1"},
        {"content": "뇌종양 내용2", "source": "src2"},
    ]
    total = load_documents(docs)
    assert total == 2
    mock_embed.assert_called_once_with(["뇌종양 내용1", "뇌종양 내용2"])
