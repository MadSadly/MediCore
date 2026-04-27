from __future__ import annotations

import os

from WJ.rag.vector_store import search_similar
from WJ.schemas.response import RetrievedDocument

_embedding_model = None


def _get_embedding_model():
    """Vertex AI 임베딩 모델 싱글톤."""
    global _embedding_model
    if _embedding_model is None:
        from vertexai.language_models import TextEmbeddingModel
        _embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
    return _embedding_model


def embed_query(text: str) -> list[float]:
    """
    검색용 쿼리 임베딩 생성.
    task_type="RETRIEVAL_QUERY" 사용 (저장 시와 반드시 구분).
    """
    from vertexai.language_models import TextEmbeddingInput
    model = _get_embedding_model()
    inputs = [TextEmbeddingInput(text, task_type="RETRIEVAL_QUERY")]
    result = model.get_embeddings(inputs, output_dimensionality=1024)
    return result[0].values


def retrieve(query: str, top_k: int = 5) -> list[RetrievedDocument]:
    """
    쿼리 텍스트로 관련 의학 문헌 검색.

    Args:
        query: 검색 쿼리 (예: 분류 결과 기반 텍스트)
        top_k: 반환할 최대 문서 수

    Returns:
        RetrievedDocument 리스트 (관련도 높은 순)
    """
    query_embedding = embed_query(query)
    rows = search_similar(query_embedding, top_k=top_k)

    return [
        RetrievedDocument(
            content=row["content"],
            source=row["source"],
            relevance_score=row["relevance_score"],
        )
        for row in rows
    ]


def build_rag_query(classification: dict) -> str:
    """분류 결과로부터 RAG 검색 쿼리 문자열 생성."""
    pred = classification["prediction"]
    conf = classification["confidence"]

    if pred == "Tumor":
        return (
            f"뇌종양 MRI 소견 및 임상적 특성. "
            f"종양 확률 {conf:.1%}. 글리오마 감별진단 및 치료 권고사항."
        )
    else:
        return (
            f"정상 뇌 MRI 소견. "
            f"정상 확률 {conf:.1%}. 뇌종양 음성 판정 기준 및 추적 관찰 가이드라인."
        )
