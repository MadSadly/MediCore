from pathlib import Path
from dotenv import load_dotenv

# .env 로드 (프로젝트 루트 기준)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from GW.router import router

app = FastAPI(title="MediCore Colon Dev Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("GW.dev_server:app", host="0.0.0.0", port=8000, reload=True)
