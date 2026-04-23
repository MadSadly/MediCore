"""
MEDI-Zero RAG 엔진
BGE-M3 모델로 의학 지식을 벡터화하고 pgvector에서 유사 문서를 검색.
module_tag로 질환별 데이터를 격리하여 검색 정확도 보장.

메모리: BGE-M3 약 2.2GB (FP16 기준)
"""

import os
import logging
from typing import Optional
import psycopg2
import psycopg2.extras
from FlagEmbedding import FlagModel  # pip install FlagEmbedding

logger = logging.getLogger(__name__)

# ── 설정 ──────────────────────────────────────────────────────────
DB_URL = os.getenv("DB_URL", "postgresql://medizero:password@localhost:5432/medizerodb")
MODULE_NAME = os.getenv("MODULE_NAME", "skin")  # 이 워커의 질환 태그

# BGE-M3: 한국어/영어/의학 용어 모두 강력한 다국어 임베딩 모델
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024   # BGE-M3 출력 차원
TOP_K = 5              # 상위 몇 개 문서를 가져올지


class RAGEngine:
    """
    BGE-M3 기반 RAG 엔진.
    1. 쿼리 텍스트 → 벡터 변환
    2. pgvector에서 코사인 유사도 검색
    3. 검색된 문서를 Ollama LLM에 컨텍스트로 전달
    """

    def __init__(self):
        logger.info("BGE-M3 모델 로딩 중... (최초 1회, 약 2.2GB)")
        # use_fp16=True: 메모리 절반 절약 (정확도 영향 거의 없음)
        self.model = FlagModel(
            EMBEDDING_MODEL,
            use_fp16=True,
            query_instruction_for_retrieval="Represent this medical query for searching relevant passages: "
        )
        self.conn = self._connect_db()
        logger.info(f"RAG 엔진 초기화 완료 (모듈: {MODULE_NAME})")

    def _connect_db(self):
        """pgvector가 활성화된 PostgreSQL에 연결"""
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        # pgvector 타입 등록 (벡터 컬럼 읽기 위해 필수)
        psycopg2.extras.register_vector(conn)
        return conn

    def embed(self, text: str) -> list[float]:
        """텍스트 → 1024차원 벡터 변환"""
        return self.model.encode(text).tolist()

    def search(self, query: str, module_tag: Optional[str] = None, top_k: int = TOP_K) -> list[dict]:
        """
        벡터 유사도 검색.

        Args:
            query: 검색 쿼리 (예: "피부 홍반 치료 가이드라인")
            module_tag: 질환 필터 (None이면 전체 검색)
                        예: 'skin', 'brain', 'kidney'
            top_k: 반환할 문서 수

        Returns:
            [{"content": "...", "source": "...", "score": 0.95}, ...]
        """
        query_vector = self.embed(query)

        # module_tag로 질환별 격리 검색 (다른 질환 데이터 혼입 방지)
        tag = module_tag or MODULE_NAME

        sql = """
            SELECT
                content,
                source,
                module_tag,
                -- <=> 연산자: pgvector 코사인 거리 (0에 가까울수록 유사)
                1 - (embedding <=> %s::vector) AS score
            FROM medical_knowledge
            WHERE module_tag = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (query_vector, tag, query_vector, top_k))
            rows = cur.fetchall()

        return [dict(row) for row in rows]

    def build_prompt(self, query: str, contexts: list[dict]) -> str:
        """
        검색된 문서들을 LLM 프롬프트에 삽입.
        Ollama에 전달할 최종 프롬프트를 구성.
        """
        context_text = "\n\n".join(
            f"[참고자료 {i+1}] (출처: {c['source']}, 유사도: {c['score']:.2f})\n{c['content']}"
            for i, c in enumerate(contexts)
        )

        return f"""당신은 의료 AI 진단 보조 시스템입니다.
아래 의학 참고자료를 바탕으로 질문에 답하세요.
참고자료에 없는 내용은 추측하지 말고 "정보 없음"으로 답하세요.

[의학 참고자료]
{context_text}

[질문]
{query}

[답변]"""

    def query_and_generate(self, query: str, ollama_client) -> dict:
        """
        RAG 전체 파이프라인 실행:
        쿼리 → 벡터 검색 → 프롬프트 구성 → Ollama 생성

        Args:
            query: 사용자 질문
            ollama_client: Ollama API 클라이언트

        Returns:
            {"answer": "...", "sources": [...], "contexts_used": 5}
        """
        # 1단계: 관련 문서 검색
        contexts = self.search(query)

        if not contexts:
            return {
                "answer": "관련 의학 지식 데이터가 없습니다.",
                "sources": [],
                "contexts_used": 0
            }

        # 2단계: 프롬프트 구성
        prompt = self.build_prompt(query, contexts)

        # 3단계: Ollama LLM으로 답변 생성
        response = ollama_client.generate(prompt=prompt)

        return {
            "answer": response.get("response", ""),
            "sources": [c["source"] for c in contexts],
            "contexts_used": len(contexts)
        }

    def add_knowledge(self, content: str, source: str, module_tag: str):
        """
        의학 지식 문서를 벡터화하여 DB에 저장 (데이터 적재용).

        Args:
            content: 문서 본문
            source: 출처 (예: "대한피부과학회 가이드라인 2024")
            module_tag: 질환 태그 (예: "skin")
        """
        vector = self.embed(content)

        sql = """
            INSERT INTO medical_knowledge (content, source, module_tag, embedding)
            VALUES (%s, %s, %s, %s::vector)
            ON CONFLICT DO NOTHING
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (content, source, module_tag, vector))

        logger.info(f"지식 추가 완료: [{module_tag}] {source[:50]}")


# ── FastAPI 라우터에서 사용할 싱글톤 인스턴스 ───────────────────
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """FastAPI dependency injection용 싱글톤 게터"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine