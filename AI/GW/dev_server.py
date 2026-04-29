from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 로드하기 위해 경로 설정 (AI/GW/dev_server.py 기준 상위 두 단계 위)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from GW.router import router  # GW 폴더 내의 router.py 임포트

app = FastAPI(title="MediCore Colon Cancer AI Server (Dev)")

# CORS 설정: 프론트엔드 및 백엔드와의 통신 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 담당 라우터 등록
app.include_router(router)

if __name__ == "__main__":
    # 로컬 개발 시 8000 포트 사용, 코드 수정 시 자동 재시작(reload) 활성화
    uvicorn.run("GW.dev_server:app", host="0.0.0.0", port=8000, reload=True)
