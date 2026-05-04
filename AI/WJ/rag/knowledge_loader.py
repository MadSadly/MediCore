from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from WJ.rag.vector_store import ensure_table, insert_documents

_embedding_model = None


def _init_vertexai() -> None:
    import vertexai
    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "asia-northeast3")
    key_path = os.getenv("GCP_KEY_PATH")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID 환경변수가 설정되지 않았습니다.")
    if key_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    vertexai.init(project=project, location=location)


def _get_embedding_model():
    """Vertex AI 임베딩 모델 싱글톤."""
    global _embedding_model
    if _embedding_model is None:
        _init_vertexai()
        from vertexai.language_models import TextEmbeddingModel
        _embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
    return _embedding_model


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    문서 임베딩 생성.
    task_type="RETRIEVAL_DOCUMENT" 사용 (검색 시와 반드시 구분).
    """
    from vertexai.language_models import TextEmbeddingInput
    model = _get_embedding_model()
    inputs = [TextEmbeddingInput(t, task_type="RETRIEVAL_DOCUMENT") for t in texts]
    results = model.get_embeddings(inputs, output_dimensionality=768)
    return [r.values for r in results]


def load_documents(
    documents: list[dict],
    batch_size: int = 10,
) -> int:
    """
    의학 문헌을 임베딩하여 pgvector에 적재.

    Args:
        documents: [{"content": str, "source": str}, ...]
        batch_size: Vertex AI API 배치 크기

    Returns:
        총 삽입된 문서 수
    """
    ensure_table()

    total = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        texts = [d["content"] for d in batch]
        embeddings = embed_documents(texts)

        rows = [
            {
                "content": doc["content"],
                "source": doc.get("source", ""),
                "embedding": emb,
            }
            for doc, emb in zip(batch, embeddings)
        ]
        total += insert_documents(rows)

    return total


# ── 샘플 지식 베이스 (초기 적재용) ──────────────────────────────────────

SAMPLE_KNOWLEDGE = [
    {
        "content": (
            "글리오마(Glioma)는 뇌의 신경교세포에서 발생하는 종양으로, "
            "WHO 분류에 따라 Grade I~IV로 구분된다. "
            "Grade IV(교모세포종, GBM)는 가장 악성이며 중앙 생존기간이 15개월 내외다. "
            "MRI T1 조영증강 영상에서 불규칙한 경계와 괴사 중심부가 특징적이다."
        ),
        "source": "WHO CNS Tumor Classification 2021",
    },
    {
        "content": (
            "뇌종양 MRI 진단 기준: T1 강조 영상에서 조영증강 병변, "
            "T2/FLAIR에서 주변 부종, 주변 뇌실질 침윤 소견. "
            "DWI에서 확산 제한 소견은 세포밀도 높은 종양을 시사. "
            "MR spectroscopy에서 Cho/NAA 비율 상승 시 종양 가능성 높음."
        ),
        "source": "RSNA Brain Tumor Imaging Guidelines 2023",
    },
    {
        "content": (
            "정상 뇌 MRI 소견: 대뇌피질, 백질, 기저핵, 소뇌, 뇌간이 정상 신호강도. "
            "뇌실 크기 정상. 중선구조 편위 없음. 비정상 조영증강 병변 없음. "
            "T2/FLAIR에서 백질 고신호 병변 없음."
        ),
        "source": "Normal Brain MRI Atlas, 2022",
    },
    {
        "content": (
            "뇌종양 감별진단: 원발성(글리오마, 수막종, 청신경초종) vs 전이성 뇌종양. "
            "전이성 종양은 회백질 경계부에 다발성으로 나타나는 경우 많음. "
            "단발성 병변일 경우 원발성 뇌종양과 감별 위해 전신 CT 또는 PET-CT 필요."
        ),
        "source": "NCCN CNS Cancers Guidelines 2024",
    },
    {
        "content": (
            "뇌종양 확진 후 권고사항: 신경외과, 방사선종양학과, 종양내과 다학제 팀 회의. "
            "수술적 절제 가능성 평가 후 최대 안전 절제술 시행. "
            "WHO Grade III~IV는 테모졸로마이드 동시 방사선 항암치료(Stupp protocol) 표준."
        ),
        "source": "Stupp et al., NEJM 2005; NCCN 2024",
    },
    {
        "content": (
            "뇌종양 AI 진단 보조 시스템 활용 지침: AI 결과는 참고용이며 단독 진단 불가. "
            "확신도 85% 미만 시 전문의 추가 검토 필수. "
            "BraTS 데이터셋 기반 모델은 글리오마에 최적화되어 있으며 "
            "수막종, 전이성 종양 등은 별도 검증이 필요하다."
        ),
        "source": "MediCore AI System Documentation v2",
    },
]


def load_sample_knowledge() -> int:
    """샘플 의학 지식 베이스 적재. DB가 비어 있을 때 초기화 용도."""
    return load_documents(SAMPLE_KNOWLEDGE)
