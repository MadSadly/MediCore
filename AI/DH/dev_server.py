from pathlib import Path
from dotenv import load_dotenv

# 최상위 폴더의 .env 파일을 불러옵니다.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from DH.router import router  # DH 모듈의 라우터 임포트

# 앱 이름도 팀 컨벤션에 맞춰 변경
app = FastAPI(title="MEDI-Zero AI [DH-Spine] Dev Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 연결
app.include_router(router)

if __name__ == "__main__":
    # 실행 시 DH.dev_server 모듈을 바라보도록 설정, 포트는 8000
    uvicorn.run("DH.dev_server:app", host="0.0.0.0", port=8000, reload=True)