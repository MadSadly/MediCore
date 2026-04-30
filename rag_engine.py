import os
import psycopg2
from FlagEmbedding import BGEM3FlagModel
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel

embed_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

def get_llm_advice(prediction, user_data):
    query = f"대장암 예측 결과 {prediction}, 환자 정보: {user_data}. 관리 방법은?"
    query_embedding = embed_model.encode(query)['dense_vecs']
    
    # 1. Vector Search
    conn = psycopg2.connect(os.getenv("DB_URL"))
    cur = conn.cursor()
    cur.execute("""
        SELECT content FROM medical_knowledge 
        WHERE module = 'colon' 
        ORDER BY embedding <=> %s::vector LIMIT 3
    """, (query_embedding.tolist(),))
    context = "\n".join([r[0] for r in cur.fetchall()])
    cur.close()
    conn.close()

    # 2. Gemini LLM (Vertex AI)
    vertexai.init(project=os.getenv("GCP_PROJECT"), location="us-central1")
    model = GenerativeModel("gemini-1.5-flash")
    prompt = f"다음 의학 지식을 바탕으로 환자에게 부드럽게 조언해줘:\n{context}\n\n질문: {query}"
    
    response = model.generate_content(prompt)
    return response.text