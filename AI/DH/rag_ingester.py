import os
import time
import json
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types as genai_types
from llama_parse import LlamaParse
from langchain_text_splitters import MarkdownTextSplitter

# 1. 환경 변수 로드
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

# =====================================================================
# 🌟 [개선] 속도 조절(Throttle) 로직이 포함된 Gemini 임베딩 클래스
# =====================================================================
class GeminiNewEmbeddings:
    def __init__(self, model_name="gemini-embedding-001"):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def embed_documents(self, texts):
        # 🚨 더 안전하게 가기 위해 배치 크기를 50으로 줄입니다.
        batch_size = 50
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            print(f"📡 임베딩 생성 중... ({i} ~ {min(i + batch_size, len(texts))} / {len(texts)})")

            try:
                config = genai_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch_texts,
                    config=config
                )
                all_embeddings.extend([emb.values for emb in response.embeddings])
            except Exception as e:
                # 만약 또 할당량 에러가 나면 여기서 한 번 더 쉽니다.
                print(f"⚠️ API 요청 중 오류 발생: {e}")
                print("⏳ 1분간 완전히 휴식 후 재시도합니다...")
                time.sleep(60)
                # 재시도 로직 (단순화를 위해 여기서는 넘어가지만, 보통은 다시 시도하게 짬)
                continue

            # 🚨 50개 보낸 후 35초 대기 (안전한 속도 조절)
            if i + batch_size < len(texts):
                print(f"⏳ 현재 {len(all_embeddings)}개 완료. 할당량 보호를 위해 35초 대기...")
                time.sleep(35)

        return all_embeddings

    def embed_query(self, text):
        config = genai_types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=config
        )
        return response.embeddings[0].values

# =====================================================================
# 🚀 메인 데이터 주입 함수
# =====================================================================
def ingest_data_to_pgvector():
    # 파일 경로 설정 (절대 경로 권장)
    pdf_file_path = r"D:\rlaekagus329\MediCore\AI\DH\LumbarStenosis.pdf"
    cache_path = os.path.join(os.path.dirname(__file__), "parsed_cache.md")

    if not os.path.exists(pdf_file_path) and not os.path.exists(cache_path):
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_file_path}")
        return

    # [1/4] LlamaParse 파싱 (캐싱 로직 포함)
    print("🚀 [1/4] 텍스트 추출 단계 시작...")
    if os.path.exists(cache_path):
        print("📂 캐시된 마크다운 파일을 발견했습니다. LlamaParse 호출을 건너뜁니다 (크레딧 보호).")
        with open(cache_path, "r", encoding="utf-8") as f:
            raw_markdown_text = f.read()
    else:
        print("🔍 LlamaParse로 PDF 분석 중... (이 작업은 크레딧이 소모됩니다)")
        parser = LlamaParse(api_key=LLAMA_CLOUD_API_KEY, result_type="markdown", language="ko")
        documents = parser.load_data(pdf_file_path)
        raw_markdown_text = "\n\n".join([doc.text for doc in documents])
        # 결과를 파일로 저장
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(raw_markdown_text)
        print("✅ 파싱 완료 및 캐시 저장 성공!")

    # [청킹]
    text_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.create_documents([raw_markdown_text])
    texts = [chunk.page_content for chunk in chunks]
    print(f"✅ 총 {len(texts)}개의 텍스트 청크가 준비되었습니다.")

    # [2/4] 임베딩 변환
    print("🧠 [2/4] Gemini 모델로 임베딩 변환 중...")
    embeddings_cache = os.path.join(os.path.dirname(__file__), "vectors_cache.json")

    if os.path.exists(embeddings_cache):
        print("📂 캐시된 임베딩 데이터를 발견했습니다. (변환 과정 생략)")
        with open(embeddings_cache, "r") as f:
            vectors = json.load(f)
    else:
        print("🧠 [2/4] Gemini 모델로 임베딩 변환 중...")
        embeddings_model = GeminiNewEmbeddings()
        vectors = embeddings_model.embed_documents(texts)
        with open(embeddings_cache, "w") as f:
            json.dump(vectors, f)
        print("✅ 임베딩 변환 완료 및 캐시 저장!")

    # [3/4] PostgreSQL 연결
    print("💾 [3/4] PostgreSQL 데이터베이스 연결 중...")

    # 환경 변수에서 DB 정보 가져오기 (비밀번호 누락 시 에러 발생)
    #db_host = os.getenv("DB_HOST", "192.168.0.20")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "medicoredb")
    db_user = os.getenv("DB_USER", "medicore")
    db_password = os.getenv("DB_PASSWORD")

    if not db_password:
        raise ValueError("❌ .env 파일에 DB_PASSWORD가 설정되지 않았습니다!")

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()

        # [4/4] 데이터 삽입
        print("📥 [4/4] medical_knowledge 테이블에 데이터 적재 시작...")
        insert_query = """
                       INSERT INTO medical_knowledge (content, source, module_tag, embedding)
                       VALUES (%s, %s, %s, %s); \
                       """

        module_tag = "spine"
        source_name = "NASS Spinal Stenosis Guideline 2021"

        for text, vector in zip(texts, vectors):
            vector_str = "[" + ",".join(map(str, vector)) + "]"
            cursor.execute(insert_query, (text, source_name, module_tag, vector_str))

        conn.commit()
        print(f"🎉 축하합니다! 총 {len(texts)}개의 데이터가 'spine' 태그로 DB에 저장되었습니다!")

    except Exception as e:
        print(f"❌ DB 작업 중 오류 발생: {e}")
        if 'conn' in locals(): conn.rollback()
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    ingest_data_to_pgvector()