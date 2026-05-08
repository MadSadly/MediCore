from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from MS.router import router

app = FastAPI(title="MEDI-Zero AI [MS-Skin] Dev Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "module": "skin"}


if __name__ == "__main__":
    uvicorn.run("MS.dev_server:app", host="0.0.0.0", port=8000, reload=True)