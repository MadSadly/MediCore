"""
MEDI-Zero RAG 엔진
BGE-M3로 의학 지식을 벡터화 → pgvector에서 유사 문서 검색
→ Google Vertex AI Gemini로 최종 소견서 생성

[메모리 사용량]
- BGE-M3 (FP16): 약 2.2GB
- FastAPI + 기타:  약 1GB
- Ollama 제거로 워커 PC당 약 10GB 절약
"""

import os
import logging
from typing import Optional

import psycopg2
import psycopg2.extras
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from FlagEmbedding import FlagModel

logger = logging.getLogger(__name__)

# ── 환경변수 설정 ──────────────────────────────────────────────
DB_URL          = os.getenv("DB_URL", "postgresql://medicore:pw@localhost:5432/medicoredb")
MODULE_NAME     = os.getenv("MODULE_NAME", "skin")
GCP_PROJECT_ID  = os.getenv("GCP_PROJECT_ID")       # Google Cloud 프로젝트 ID
GCP_LOCATION    = os.getenv("GCP_LOCATION", "asia-northeast3")  # 서울 리전
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-001")
# gemini-1.5-flash: 빠르고 저렴 (진단 보조용으로 충분)
# gemini-1.5-pro  : 더 정확, 복잡한 의학 추론에 적합

EMBEDDING_DIM   = 1024   # BGE-M3 출력 차원
TOP_K           = 5      # RAG 검색 결과 수


class RAGEngine:
    """
    BGE-M3 + pgvector + Vertex AI Gemini 기반 RAG 엔진.

    [파이프라인]
    1. 쿼리 → BGE-M3 임베딩 (1024차원 벡터)
    2. pgvector 코사인 유사도 검색 (module_tag로 질환 격리)
    3. 검색된 문서를 Gemini 프롬프트에 삽입
    4. Gemini가 의학 소견서 생성
    """

    def __init__(self):
        self._init_embedding_model()
        self._init_vertex_ai()
        self.conn = self._connect_db()
        logger.info(f"RAG 엔진 초기화 완료 | 모듈: {MODULE_NAME} | LLM: {GEMINI_MODEL}")

    def _init_embedding_model(self):
        logger.info("BGE-M3 임베딩 모델 로딩 중... (약 2.2GB, 최초 1회)")
        self.embedding_model = FlagModel(
            "BAAI/bge-m3",
            use_fp16=True,   # FP16으로 메모리 절반 절약
            query_instruction_for_retrieval=(
                "Represent this medical query for searching relevant passages: "
            )
        )

    def _init_vertex_ai(self):
        """Vertex AI 초기화. 서비스 계정 JSON이 환경변수로 설정되어 있어야 함."""
        if not GCP_PROJECT_ID:
            raise ValueError(
                "GCP_PROJECT_ID 환경변수가 없습니다. "
                ".env 파일에 GCP_PROJECT_ID를 추가하세요."
            )
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
        self.gemini = GenerativeModel(GEMINI_MODEL)
        logger.info(f"Vertex AI 초기화 완료 | 프로젝트: {GCP_PROJECT_ID} | 리전: {GCP_LOCATION}")

    def _connect_db(self):
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        psycopg2.extras.register_vector(conn)
        return conn

    # ── 임베딩 ──────────────────────────────────────────────────

    def embed(self, text: str) -> list[float]:
        """텍스트 → 1024차원 벡터"""
        return self.embedding_model.encode(text).tolist()

    # ── 벡터 검색 ────────────────────────────────────────────────

    def search(
        self,
        query: str,
        module_tag: Optional[str] = None,
        top_k: int = TOP_K
    ) -> list[dict]:
        """
        pgvector 코사인 유사도 검색.
        module_tag로 질환별 데이터를 격리하여 검색 (피부 데이터에서 뇌 데이터 혼입 방지).
        """
        query_vector = self.embed(query)
        tag = module_tag or MODULE_NAME

        sql = """
            SELECT
                content,
                source,
                module_tag,
                1 - (embedding <=> %s::vector) AS score
            FROM medical_knowledge
            WHERE module_tag = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (query_vector, tag, query_vector, top_k))
            return [dict(row) for row in cur.fetchall()]

    # ── Gemini 소견서 생성 ────────────────────────────────────────

    def generate(self, query: str, contexts: list[dict]) -> str:
        """
        검색된 의학 문서를 컨텍스트로 Gemini에게 소견서 생성 요청.
        참고자료 외의 내용은 추측하지 않도록 프롬프트 설계.
        """
        context_text = "\n\n".join(
            f"[참고자료 {i+1}] 출처: {c['source']} (유사도: {c['score']:.2f})\n{c['content']}"
            for i, c in enumerate(contexts)
        )

        prompt = f"""당신은 의료 AI 진단 보조 시스템입니다.
아래 의학 참고자료만을 근거로 질문에 답하세요.
참고자료에 없는 내용은 "해당 정보 없음"으로 답하고 절대 추측하지 마세요.

[의학 참고자료]
{context_text}

[임상 질문]
{query}

[의학적 소견]"""

        response = self.gemini.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.2,      # 낮을수록 일관성 높음 (의료 용도에 적합)
                max_output_tokens=1024,
                top_p=0.8,
            )
        )
        return response.text

    # ── 전체 RAG 파이프라인 ───────────────────────────────────────

    def query_and_generate(self, query: str) -> dict:
        """
        쿼리 → 벡터 검색 → Gemini 소견서 생성까지 한 번에.

        Returns:
            {
                "answer": "Gemini 생성 소견서",
                "sources": ["출처1", "출처2"],
                "contexts_used": 5
            }
        """
        contexts = self.search(query)

        if not contexts:
            return {
                "answer": "관련 의학 지식 데이터가 없습니다. 데이터 적재 후 다시 시도하세요.",
                "sources": [],
                "contexts_used": 0
            }

        answer = self.generate(query, contexts)

        return {
            "answer": answer,
            "sources": [c["source"] for c in contexts],
            "contexts_used": len(contexts)
        }

    # ── 지식 적재 ────────────────────────────────────────────────

    def add_knowledge(self, content: str, source: str, module_tag: str):
        """의학 문서를 벡터화하여 DB에 저장 (데이터 파이프라인 적재용)."""
        vector = self.embed(content)
        sql = """
            INSERT INTO medical_knowledge (content, source, module_tag, embedding)
            VALUES (%s, %s, %s, %s::vector)
            ON CONFLICT DO NOTHING
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (content, source, module_tag, vector))
        logger.info(f"지식 적재 완료: [{module_tag}] {source[:50]}")


# ── FastAPI 싱글톤 ────────────────────────────────────────────────
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """FastAPI Depends() 주입용 싱글톤 게터."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine