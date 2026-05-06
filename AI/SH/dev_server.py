"""
AI/SH/dev_server.py
안과 CDSS — 로컬 개발 전용 서버
CLAUDE.md 규칙: AI/main.py 수정 금지, 독립 서버 실행

실행:
  cd D:\\MediCore\\AI
  python -m SH.dev_server
"""

from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드 (AI/SH/dev_server.py 기준 2단계 상위)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router, lifespan

app = FastAPI(
    title="안과 CDSS — SH 로컬 개발 서버",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "SH.dev_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
