import os
# GPU 비활성화 — 임베딩/TabNet 모두 CPU 전용이므로 CUDA 초기화 불필요
# 병렬 쓰레드에서 CUDA 컨텍스트 충돌 방지
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[2] / ".env"
_loaded = load_dotenv(_env_path, override=True)

# GCP_KEY_PATH 상대경로 → 프로젝트 루트 기준 절대경로로 정규화
_raw_key = os.getenv("GCP_KEY_PATH", "")
if _raw_key and not Path(_raw_key).is_absolute():
    _abs_key = (_env_path.parent / _raw_key).resolve()
    os.environ["GCP_KEY_PATH"] = str(_abs_key)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from NJ.router import router

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.on_event("startup")
async def _startup_diagnostic():
    from NJ.rag.engine import USE_VERTEX_LLM, USE_OLLAMA

    project  = os.getenv("GCP_PROJECT_ID", "")
    location = os.getenv("GCP_LOCATION", "us-central1")
    key_path = os.getenv("GCP_KEY_PATH", "")

    if USE_VERTEX_LLM:
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-002")
        mode  = f"[OK] Vertex AI ({model} @ {location})"
    elif USE_OLLAMA:
        mode  = f"[DEV] Ollama ({os.getenv('OLLAMA_MODEL', 'llama3.1')})"
    else:
        mode  = "[FALLBACK] Rule-based (no LLM)"

    proj_display = project if project else "[NOT SET]"
    key_display  = key_path if key_path else "[NOT SET]"

    print("\n" + "=" * 60)
    print(f"  [Kidney] .env 경로        : {_env_path}")
    print(f"  [Kidney] .env 로드        : {'성공' if _loaded else '❌ 실패 (파일 없음)'}")
    print(f"  [Kidney] LLM 모드         : {mode}")
    print(f"  [Kidney] GCP_PROJECT_ID   : {proj_display}")
    print(f"  [Kidney] GCP_LOCATION     : {location}")
    print(f"  [Kidney] GCP_KEY_PATH     : {key_display}")
    print(f"  [Kidney] CUDA             : 비활성화 (CPU 전용)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    uvicorn.run("NJ.dev_server:app", host="0.0.0.0", port=8000, reload=True)
