"""
AI/SH/router.py
안과 CDSS — FastAPI 라우터 · POST /sh/analyze (SSE) · POST /sh/analyze/sync (Spring JSON)
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

import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Any

from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .schemas.request import AnalysisRequest
from .schemas.response import (
    EmergencyAlert, ErrorCode,
    CitationSource,
)
from .core.quality_check import check_image_quality, check_post_inference_quality
from .core.model import eye_model, OODInferenceError
from .core.gradcam import gradcam_engine
from .rag.retriever import hybrid_retriever
from .rag.graph_rag import graph_builder, graph_retriever
from .llm.report_generator import generate_report_stream


# ── 보안 ─────────────────────────────────────────────────────
security = HTTPBearer()

router = APIRouter(prefix="/sh", tags=["안과 진단"])


# ── Lifespan (서버 시작 시 모델 워밍업) ──────────────────────
@asynccontextmanager
async def lifespan(app):
    """FastAPI Lifespan: Cold Start 방지"""
    try:
        eye_model.load()
        print("✅ EyeModel 워밍업 완료")
    except Exception as e:
        print(f"⚠️ EyeModel 워밍업 실패: {e}")
    try:
        hybrid_retriever.load()
        print("✅ HybridRetriever (BGE-M3) 워밍업 완료")
    except Exception as e:
        print(f"⚠️ HybridRetriever 워밍업 실패: {e}")
    try:
        graph_builder.load()
        print("✅ GraphBuilder 캐시 초기화 완료")
    except Exception as e:
        print(f"⚠️ GraphBuilder 초기화 실패: {e}")
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


@router.post("/analyze/sync")
async def analyze_sync(
    file:              UploadFile = File(...),
    patient_id:        str        = Form(...),
    patient_age:       int        = Form(None),
    has_diabetes:      bool       = Form(False),
    has_hypertension:  bool       = Form(False),
    clinical_note:     str        = Form(None),
    credentials:       HTTPAuthorizationCredentials = Depends(security),
):
    """
    Spring Boot `EyeDiagnosisService` 호환: 동기 단일 JSON.
    SSE `/sh/analyze` 와 동일 파이프라인(품질 → DL → RAG → 소견서).
    """
    request = AnalysisRequest(
        patient_id=patient_id,
        patient_age=patient_age,
        has_diabetes=has_diabetes,
        has_hypertension=has_hypertension,
        clinical_note=clinical_note,
    )
    image_bytes = await file.read()
    status, body = await _run_sync_analysis(request, image_bytes, file.filename)
    return JSONResponse(status_code=status, content=body)


async def _run_sync_analysis(
    request: AnalysisRequest,
    image_bytes: bytes,
    filename: str,
) -> tuple[int, dict[str, Any]]:
    """
    (HTTP 상태코드, 본문). 성공 시 Spring이 파싱하는 필드 포함.
    실패 시 {\"error_code\", \"message\", \"session_id\"(선택)}.
    """
    session_id = request.request_id

    quality_result, img_bgr = check_image_quality(image_bytes, filename)
    if not quality_result.is_valid:
        return 400, {
            "error_code": quality_result.error_code,
            "message":    quality_result.rejection_reason or "이미지 검증 실패",
            "session_id": session_id,
        }

    assert img_bgr is not None

    try:
        dl_result, emergency, inference_time_ms = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: eye_model.predict(
                img_bgr,
                patient_age=request.patient_age,
                has_diabetes=request.has_diabetes,
                has_hypertension=request.has_hypertension,
            ),
        )
    except OODInferenceError as e:
        return 400, {
            "error_code": ErrorCode.IMAGE_NOT_FUNDUS,
            "message":    str(e),
            "session_id": session_id,
        }
    except Exception as e:
        return 500, {
            "error_code": ErrorCode.MODEL_INFERENCE_FAILED,
            "message":    f"모델 추론 실패: {str(e)}",
            "session_id": session_id,
        }

    gradcam_b64 = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: gradcam_engine.generate(
            img_bgr,
            dl_result.primary_disease.disease_id,
        ),
    )

    citations = await _retrieve_rag(
        disease_name=dl_result.primary_disease.disease_name,
        stage=dl_result.stage.stage if dl_result.stage else 0,
    )

    report_text = ""
    try:
        async for text in generate_report_stream(
            dl_result=dl_result,
            emergency=emergency,
            citations=citations,
            clinical_note=request.clinical_note,
        ):
            report_text += text
            await asyncio.sleep(0)
    except Exception as e:
        print(f"⚠️ 소견서 생성 실패(sync): {e}")

    dl_dump = dl_result.model_dump()
    dl_dump["gradcam_base64"] = gradcam_b64

    ts = datetime.now(timezone.utc).isoformat()
    qs = quality_result.quality_score
    quality_out: float | None = float(qs) if qs is not None else None

    return 200, {
        "session_id":        session_id,
        "dl_result":        dl_dump,
        "emergency":        emergency.model_dump(),
        "report":           report_text,
        "inference_time_ms": float(inference_time_ms),
        "quality_score":    quality_out,
        "timestamp":        ts,
    }


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

    max_confidence = float(dl_result.primary_disease.confidence)
    is_fundus, rejection_reason = check_post_inference_quality(max_confidence)
    if not is_fundus:
        yield _sse_event("error", {
            "error_code": ErrorCode.IMAGE_NOT_FUNDUS,
            "message":    rejection_reason or "",
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

    try:
        async for text in generate_report_stream(
            dl_result=dl_result,
            emergency=emergency,
            citations=citations,
            clinical_note=request.clinical_note,
        ):
            yield _sse_event("report_chunk", {
                "session_id": session_id,
                "data":       text,
            })
            await asyncio.sleep(0)
    except Exception as e:
        print(f"⚠️ 소견서 생성 실패: {e}")
        yield _sse_event("error", {
            "error_code": ErrorCode.LLM_GENERATION_FAILED,
            "message":    "소견서 생성에 실패했습니다.",
            "session_id": session_id,
        })

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
    Hybrid RAG (Dense + BM25 → RRF) 및 Graph 기반 재정렬.
    pgvector `module_tag = 'eyes'` 필터 필수 (CLAUDE.md 규칙).
    """

    def _sync() -> list[CitationSource]:
        assert graph_builder.module_tag == "eyes"
        q = f"{disease_name} Stage {stage} 치료 가이드라인"
        rows = hybrid_retriever.search(
            query=q,
            disease_name=disease_name,
            stage=stage,
        )
        rows = graph_retriever.refine(
            rows,
            disease_name=disease_name,
            stage=stage,
        )
        out: list[CitationSource] = []
        for r in rows:
            out.append(
                CitationSource(
                    title=r.get("title") or disease_name,
                    content=(r.get("content") or "")[:500],
                    source=r.get("source") or "AAO PPP",
                    page=r.get("page"),
                )
            )
        return out

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _sync)
    except Exception as e:
        print(f"⚠️ RAG 검색 실패: {e}")
        return []


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
