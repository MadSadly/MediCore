"""
신부전 RAG 엔진
gemini-embedding-001 (768차원) + pgvector + Vertex AI Gemini
"""

import os
import logging
import psycopg2
import psycopg2.extras

logger = logging.getLogger("medicore.kidney.rag")

MODULE        = "kidney"
TOP_K         = 5
EMBEDDING_DIM = 768

DB_URL = os.getenv(
    "DB_URL",
    "postgresql://medizero:testpassword@127.0.0.1:5432/medizerodb"
)


class KidneyRAGEngine:

    def __init__(self):
        self._init_embedding()
        self._init_llm()
        self.conn = self._connect_db()
        logger.info("신부전 RAG 엔진 초기화 완료")

    def _init_embedding(self):
        """gemini-embedding-001 초기화"""
        self.embed_client = None
        gcp_project = os.getenv("GCP_PROJECT_ID")

        if not gcp_project or gcp_project == "placeholder":
            logger.info("GCP 미설정 — 임베딩 없이 동작합니다.")
            return

        try:
            from google import genai
            from google.genai import types as genai_types

            self.embed_client      = genai.Client()
            self.genai_types       = genai_types
            self.embedding_model   = "gemini-embedding-001"
            logger.info("gemini-embedding-001 초기화 완료")
        except Exception as e:
            logger.warning(f"임베딩 초기화 실패: {e}")

    def _init_llm(self):
        """Vertex AI Gemini 초기화"""
        self.gemini = None
        gcp_project = os.getenv("GCP_PROJECT_ID")

        if not gcp_project or gcp_project == "placeholder":
            logger.info("GCP 미설정 — Gemini 없이 동작합니다.")
            return

        try:
            import vertexai
            from vertexai.generative_models import (
                GenerativeModel, GenerationConfig)

            vertexai.init(
                project=gcp_project,
                location=os.getenv("GCP_LOCATION", "asia-northeast3")
            )
            self.gemini     = GenerativeModel(
                os.getenv("GEMINI_MODEL", "gemini-1.5-flash-001")
            )
            self.gen_config = GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
            )
            logger.info(f"Vertex AI 초기화 완료 | {gcp_project}")
        except Exception as e:
            logger.warning(f"Vertex AI 초기화 실패: {e}")

    def _connect_db(self):
        try:
            conn = psycopg2.connect(DB_URL)
            conn.autocommit = True
            return conn
        except Exception as e:
            logger.warning(f"DB 연결 실패: {e}")
            return None

    def embed(self, text: str) -> list[float]:
        """gemini-embedding-001로 텍스트 임베딩 (768차원)"""
        if self.embed_client is None:
            return []
        try:
            result = self.embed_client.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=self.genai_types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=EMBEDDING_DIM
                )
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.warning(f"임베딩 실패: {e}")
            return []

    def search(self, query: str) -> list[dict]:
        """medical_knowledge에서 kidney 데이터만 검색"""
        if self.conn is None or not query:
            return []

        vec = self.embed(query)
        if not vec:
            return []

        try:
            sql = """
                SELECT content, source,
                       1 - (embedding <=> %s::vector) AS score
                FROM medical_knowledge
                WHERE module_tag = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            with self.conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                cur.execute(sql, (vec, MODULE, vec, TOP_K))
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.warning(f"RAG 검색 실패: {e}")
            return []

    def generate(self, query: str,
                 prediction: str,
                 contexts: list[dict]) -> str:
        """Vertex AI Gemini로 소견서 생성"""
        if not contexts:
            return self._fallback_answer(prediction)

        context_text = "\n\n".join(
            f"[참고자료 {i+1}] 출처: {c['source']} "
            f"(유사도: {c['score']:.2f})\n{c['content']}"
            for i, c in enumerate(contexts)
        )

        prompt = f"""당신은 신장내과 전문의 보조 AI입니다.
아래 KDIGO 가이드라인 참고자료만을 근거로 답변하세요.
참고자료에 없는 내용은 절대 추측하지 마세요.

[AI 진단 결과]
{prediction}

[KDIGO 가이드라인 참고자료]
{context_text}

[임상 질문]
{query if query else f"{prediction} 단계의 치료 방향과 주의사항은?"}

[의학적 소견]"""

        if self.gemini is None:
            return self._fallback_answer(prediction)

        try:
            resp = self.gemini.generate_content(
                prompt, generation_config=self.gen_config)
            return resp.text
        except Exception as e:
            logger.warning(f"Gemini 생성 실패: {e}")
            return self._fallback_answer(prediction)

    def _fallback_answer(self, prediction: str) -> str:
        """GCP 없을 때 기본 응답"""
        fallback = {
            "Normal_Stage1": "신기능이 정상입니다. 정기적인 모니터링을 권장합니다.",
            "Stage2": "경미한 신기능 저하입니다. 혈압 관리와 단백뇨 모니터링이 필요합니다.",
            "Stage3": "중등도 신기능 저하입니다. 신장내과 전문의 진료를 권장합니다.",
            "Stage4": "중증 신기능 저하입니다. 투석 준비 및 신장이식 상담이 필요합니다.",
            "Stage5": "신부전 단계입니다. 즉각적인 투석 치료가 필요합니다.",
        }
        return fallback.get(prediction, "전문의 상담이 필요합니다.")

    def query_and_generate(self, query: str,
                            prediction: str) -> dict:
        contexts = self.search(query or prediction)
        answer   = self.generate(query, prediction, contexts)
        return {
            "answer":   answer,
            "sources":  [c["source"] for c in contexts],
            "contexts": len(contexts),
        }


# 싱글톤
_rag_engine = None


def get_rag_engine() -> KidneyRAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = KidneyRAGEngine()
    return _rag_engine
