import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_engine import get_rag_engine

MODULE_NAME = os.getenv("MODULE_NAME", "skin")

MODULE_DISPLAY = {
    "skin":   "피부 진단",
    "brain":  "뇌종양 진단",
    "eyes":   "안과 진단",
    "spine":  "척추 진단",
    "kidney": "신장 진단",
    "colon":  "대장암 진단",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 RAG 엔진(BGE-M3 + Vertex AI) 미리 로드
    get_rag_engine()
    yield


app = FastAPI(title=f"MEDI-Zero AI Server [{MODULE_NAME}]", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnoseResponse(BaseModel):
    module: str
    answer: str
    sources: list[str]
    contexts_used: int


@app.get("/health")
def health():
    return {"status": "ok", "server": "FastAPI", "module": MODULE_NAME}


@app.get("/ai/{module}/health")
def module_health(module: str):
    if module != MODULE_NAME:
        raise HTTPException(status_code=404, detail=f"이 서버는 {MODULE_NAME} 전담입니다.")
    return {"module": MODULE_NAME, "display": MODULE_DISPLAY.get(MODULE_NAME), "status": "ready"}


@app.post("/ai/{module}/diagnose", response_model=DiagnoseResponse)
async def diagnose(
    module: str,
    query: str = Form(...),
    image: UploadFile = File(None),
):
    if module != MODULE_NAME:
        raise HTTPException(status_code=404, detail=f"이 서버는 {MODULE_NAME} 전담입니다.")

    rag = get_rag_engine()

    # 이미지가 있으면 파일명을 쿼리에 포함 (추후 AI 모델 추론 결과로 교체)
    full_query = query
    if image:
        full_query = f"[이미지: {image.filename}] {query}"

    result = rag.query_and_generate(full_query)

    return DiagnoseResponse(
        module=MODULE_NAME,
        answer=result["answer"],
        sources=result["sources"],
        contexts_used=result["contexts_used"],
    )