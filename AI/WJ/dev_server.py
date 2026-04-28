"""
WJ 단독 개발 서버 — main.py 없이 WJ 라우터만 실행.

사용법:
    cd D:\workspace\MediCore\AI
    python -m WJ.dev_server
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from WJ.router import router

app = FastAPI(title="MediCore Brain (WJ Dev)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("WJ.dev_server:app", host="0.0.0.0", port=8000, reload=True)
