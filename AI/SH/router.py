"""
AI/SH/router.py
안과 CDSS — FastAPI 라우터
OPH-03: 이미지 업로드
OPH-05: 이미지 유효성 검증
OPH-06: AI 통합 분석 버튼
OPH-07: DL 1차 진단 결과
OPH-08: 응급 강제 알림
OPH-09: LangGraph 진행률 SSE
OPH-10: 리포트 스트리밍 SSE
OPH-11: 근거 문헌 Citation
OPH-16: GradCAM 히트맵

담당: 홍승현 (SH)
"""

import time
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .schemas import (
    AnalysisRequest, AnalysisResponse, DLResult,
    EmergencyAlert, ErrorResponse, ErrorCode,
    ReportChunk, CitationSource,
)
from .quality_check import check_image_quality
from .model import eye_model, OODInferenceError, ModelLoadError
from .gradcam import gradcam_engine


# ── 보안 ─────────────────────────────────────────────────────
security = HTTPBearer()

router = APIRouter(prefix="/sh", tags=["안과 진단"])


# ── Lifespan (서버 시작 시 모델 워밍업) ──────────────────────
@asynccontextmanager
async def lifespan(app):
    """FastAPI Lifespan: Cold Start 방지 (Gemini 지적 반영)"""
    try:
        eye_model.load()
        print("✅ EyeModel 워밍업 완료")
    except Exception as e:
        print(f"⚠️ EyeModel 워밍업 실패: {e}")
    yield


# ── 헬스체크 ──────────────────────────────────────────────────
@router.get("/health")
async def health():
    return {"status": "ok", "module": "eyes", "model_loaded": eye_model._loaded}


# ── 메인 분석 엔드포인트 (SSE 스트리밍) ──────────────────────
@router.post("/analyze")
async def analyze(
    file:            UploadFile = File(...),
    patient_id:      str        = Form(...),
    patient_age:     int        = Form(None),
    has_diabetes:    bool       = Form(False),
    has_hypertension: bool      = Form(False),
    clinical_note:   str        = Form(None),
    credentials:     HTTPAuthorizationCredentials = Depends(security),
):
    """
    안과 AI 통합 분석 (OPH-06)
    SSE 스트리밍으로 단계별 결과 전달
    """
    # 요청 객체 생성
    request = AnalysisRequest(
        patient_id=patient_id,
        patient_age=patient_age,
        has_diabetes=has_diabetes,
        has_hypertension=has_hypertension,
        clinical_note=clinical_note,
    )

    # 이미지 바이트 읽기
    image_bytes = await file.read()

    return StreamingResponse(
        _analysis_stream(request, image_bytes, file.filename),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx proxy_buffering off
        },
    )


async def _analysis_stream(
    request:     AnalysisRequest,
    image_bytes: bytes,
    filename:    str,
) -> AsyncGenerator[str, None]:
    """
    SSE 이벤트 스트리밍 생성기

    이벤트 순서:
      1. image_validated
      2. dl_result
      3. emergency (응급 시)
      4. rag_retrieved
      5. report_chunk (반복)
      6. done
    """
    session_id = request.request_id

    # ── Step 1: 이미지 품질 검증 (OPH-05) ───────────────────
    quality_result, img_bgr = check_image_quality(image_bytes, filename)

    if not quality_result.is_valid:
        yield _sse_event("error", {
            "error_code": quality_result.error_code,
            "message":    quality_result.rejection_reason,
            "session_id": session_id,
        })
        return

    yield _sse_event("image_validated", {
        "quality_score": quality_result.quality_score,
        "session_id":    session_id,
    })

    # ── Step 2: DL 추론 (OPH-07) ─────────────────────────────
    try:
        dl_result, emergency, inference_time_ms = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: eye_model.predict(
                img_bgr,
                patient_age=request.patient_age,
                has_diabetes=request.has_diabetes,
                has_hypertension=request.has_hypertension,
            )
        )

    except OODInferenceError as e:
        yield _sse_event("error", {
            "error_code": ErrorCode.IMAGE_NOT_FUNDUS,
            "message":    str(e),
            "session_id": session_id,
        })
        return

    except Exception as e:
        yield _sse_event("error", {
            "error_code": ErrorCode.MODEL_INFERENCE_FAILED,
            "message":    f"모델 추론 실패: {str(e)}",
            "session_id": session_id,
        })
        return

    # DL 결과 전송 (OPH-07)
    yield _sse_event("dl_result", {
        "session_id":       session_id,
        "dl_result":        dl_result.model_dump(),
        "inference_time_ms": inference_time_ms,
    })

    # ── Step 3: 응급 판정 (OPH-08) ───────────────────────────
    if emergency.is_emergency:
        yield _sse_event("emergency", {
            "session_id":    session_id,
            "emergency":     emergency.model_dump(),
        })

    # ── Step 4: GradCAM 비동기 생성 (OPH-16) ─────────────────
    # ONNX 추론 결과와 독립적으로 비동기 처리
    # 프론트엔드는 dl_result 먼저 표시, GradCAM은 나중에 렌더링
    gradcam_b64 = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: gradcam_engine.generate(
            img_bgr,
            dl_result.primary_disease.disease_id,
        )
    )

    if gradcam_b64:
        yield _sse_event("gradcam_ready", {
            "session_id":    session_id,
            "gradcam_base64": gradcam_b64,
        })

    # ── Step 5: RAG 검색 (OPH-11) ────────────────────────────
    yield _sse_event("rag_searching", {"session_id": session_id})

    citations = await _retrieve_rag(
        disease_name=dl_result.primary_disease.disease_name,
        stage=dl_result.stage.stage if dl_result.stage else 0,
    )

    yield _sse_event("rag_retrieved", {
        "session_id": session_id,
        "citations":  [c.model_dump() for c in citations],
    })

    # ── Step 6: 소견서 스트리밍 (OPH-10) ─────────────────────
    yield _sse_event("report_generating", {"session_id": session_id})

    async for chunk in _generate_report_stream(
        dl_result=dl_result,
        emergency=emergency,
        citations=citations,
        clinical_note=request.clinical_note,
        session_id=session_id,
    ):
        yield chunk

    # ── Step 7: 완료 ─────────────────────────────────────────
    yield _sse_event("done", {
        "session_id":       session_id,
        "inference_time_ms": inference_time_ms,
        "quality_score":    quality_result.quality_score,
    })


# ── RAG 검색 ─────────────────────────────────────────────────

async def _retrieve_rag(
    disease_name: str,
    stage:        int,
) -> list[CitationSource]:
    """
    pgvector에서 대한안과학회 임상진료지침 검색
    module='eyes' 필터 필수 (CLAUDE.md 규칙)
    """
    try:
        import asyncpg
        import os
        import numpy as np

        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

        # 검색 쿼리 임베딩 생성 (간단히 질환명 사용)
        query = f"{disease_name} Stage {stage} 치료 가이드라인"

        # pgvector 검색 (module='eyes' 필터)
        rows = await conn.fetch("""
            SELECT title, content, source, page
            FROM medical_knowledge
            WHERE module = 'eyes'
            ORDER BY embedding <=> $1::vector
            LIMIT 3
        """, query)

        await conn.close()

        return [
            CitationSource(
                title=row["title"],
                content=row["content"][:500],
                source=row["source"],
                page=row["page"],
            )
            for row in rows
        ]

    except Exception as e:
        print(f"⚠️ RAG 검색 실패: {e}")
        return []


# ── Gemini 소견서 스트리밍 ────────────────────────────────────

async def _generate_report_stream(
    dl_result:    DLResult,
    emergency:    EmergencyAlert,
    citations:    list[CitationSource],
    clinical_note: str | None,
    session_id:   str,
) -> AsyncGenerator[str, None]:
    """
    Google Vertex AI Gemini 소견서 생성 (스트리밍)
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        import os

        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_REGION", "asia-northeast3"),
        )

        model = GenerativeModel("gemini-1.5-pro")

        # 프롬프트 구성
        citation_text = "\n".join([
            f"- {c.title}: {c.content[:200]}"
            for c in citations
        ])

        prompt = f"""
당신은 대한안과학회 임상진료지침을 기반으로 소견서를 작성하는 AI입니다.
반드시 제공된 근거 문헌에 기반하여 작성하고, 출처를 명시하세요.

[AI 진단 결과]
- 주요 질환: {dl_result.primary_disease.disease_name}
- 확신도: {dl_result.primary_disease.confidence:.1%}
- 중증도: {dl_result.stage.stage_name if dl_result.stage else '미분류'}
- 응급 여부: {'응급' if emergency.is_emergency else '비응급'}

[의사 소견]
{clinical_note or '없음'}

[근거 문헌]
{citation_text or '검색된 문헌 없음'}

위 정보를 바탕으로 간결한 임상 소견서를 작성하세요.
        """.strip()

        # 스트리밍 생성
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(prompt, stream=True)
        )

        for chunk in response:
            if chunk.text:
                yield _sse_event("report_chunk", {
                    "session_id": session_id,
                    "data":       chunk.text,
                })
                await asyncio.sleep(0)  # 이벤트 루프 양보

    except Exception as e:
        print(f"⚠️ 소견서 생성 실패: {e}")
        yield _sse_event("error", {
            "error_code": ErrorCode.LLM_GENERATION_FAILED,
            "message":    "소견서 생성에 실패했습니다.",
            "session_id": session_id,
        })


# ── 진단 이력 조회 (OPH-15) ──────────────────────────────────

@router.get("/history/{patient_id}")
async def get_patient_history(
    patient_id:  str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """환자 진단 이력 조회"""
    # Spring Boot → 공통 diagnosis 테이블에서 조회
    # module='eyes' 필터로 안과 데이터만 반환
    return {
        "patient_id": patient_id,
        "module":     "eyes",
        "message":    "Spring Boot /api/patients/{id}/diagnoses 에서 조회하세요",
    }


# ── SSE 이벤트 포맷터 ─────────────────────────────────────────

def _sse_event(event: str, data: dict) -> str:
    """SSE 형식 문자열 생성"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
