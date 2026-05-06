"""RAG 파이프라인 end-to-end 테스트 스크립트."""
import sys
import os
from pathlib import Path

# .env 로드
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

print("=== 환경변수 확인 ===")
print(f"OLLAMA_BASE_URL : {os.getenv('OLLAMA_BASE_URL')}")
print(f"OLLAMA_MODEL    : {os.getenv('OLLAMA_MODEL')}")
print(f"GCP_PROJECT_ID  : {os.getenv('GCP_PROJECT_ID')}")

# AI 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from NJ.rag.retriever import USE_GEMINI, search, embed_query
from NJ.rag.engine import USE_OLLAMA, query_and_generate

print(f"\n=== 모드 확인 ===")
print(f"USE_GEMINI : {USE_GEMINI}")
print(f"USE_OLLAMA : {USE_OLLAMA}")

print("\n=== 임베딩 테스트 ===")
vec = embed_query("CKD Stage3 치료 가이드라인")
print(f"벡터 차원 : {len(vec)}")

print("\n=== 검색 테스트 ===")
results = search("CKD Stage3 치료 관리")
print(f"검색 결과 : {len(results)}건")
for r in results[:2]:
    print(f"  - {r['source']} (score={r['score']:.3f}): {r['content'][:60]}...")

print("\n=== RAG + LLM 소견 생성 ===")
out = query_and_generate("Stage3 단계의 치료 방향은?", "Stage3")
print(f"출처 : {out['sources']}")
print(f"컨텍스트 : {out['contexts']}건")
print(f"\n[소견]\n{out['answer']}")
