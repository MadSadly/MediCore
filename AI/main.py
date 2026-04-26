import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("medicore")
logging.basicConfig(level=logging.INFO)

# .env 로드 (uvicorn이 직접 띄울 때 환경변수 설정)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k.strip(), _v.strip())

# GCP 키 파일 경로 적용
_gcp_key = os.getenv("GCP_KEY_PATH")
if _gcp_key:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _gcp_key


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _check_gcp()
    yield


def _check_gcp():
    gcp_project = os.getenv("GCP_PROJECT_ID")
    gcp_key = os.getenv("GCP_KEY_PATH")

    if not gcp_project:
        logger.info("GCP 미설정 — Vertex AI 없이 시작합니다.")
        return

    if gcp_key and not Path(gcp_key).exists():
        logger.warning(f"GCP 키 파일을 찾을 수 없음: {gcp_key}")
        return

    try:
        import vertexai
        vertexai.init(project=gcp_project, location=os.getenv("GCP_LOCATION", "asia-northeast3"))
        logger.info(f"Vertex AI 초기화 완료 | 프로젝트: {gcp_project} | 리전: {os.getenv('GCP_LOCATION', 'asia-northeast3')}")
    except Exception as e:
        logger.warning(f"Vertex AI 초기화 실패: {e}")


app = FastAPI(title="MEDI-Zero AI Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "server": "MEDI-Zero AI"}


# ── 팀원별 라우터 등록 ───────────────────────────────────────────
from WJ.router import router as wj_router
from DH.router import router as dh_router
from GW.router import router as gw_router
from MS.router import router as ms_router
from NJ.router import router as nj_router
from SH.router import router as sh_router

app.include_router(wj_router)
app.include_router(dh_router)
app.include_router(gw_router)
app.include_router(ms_router)
app.include_router(nj_router)
app.include_router(sh_router)
