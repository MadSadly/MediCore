from __future__ import annotations

import logging
import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from WJ.graph.workflow import run_diagnosis
from WJ.schemas.response import DiagnoseResponse, ErrorResponse

logger = logging.getLogger("medicore.brain")

router = APIRouter(prefix="/ai/brain", tags=["brain-tumor"])

_ALLOWED_EXTENSIONS = {".nii", ".nii.gz"}


def _validate_extension(filename: str) -> None:
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in _ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NIfTI 파일만 허용됩니다 (.nii, .nii.gz). 받은 파일: {filename}",
        )


@router.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 파일 형식"},
        422: {"model": ErrorResponse, "description": "처리 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    summary="뇌종양 진단",
    description=(
        "NIfTI (.nii / .nii.gz) 파일을 업로드하면 "
        "3D DenseNet121 분류 → RAG 검색 → Gemini 리포트 생성 결과를 반환합니다. "
        "AI 보조 도구이며 최종 진단은 전문의가 수행해야 합니다."
    ),
)
async def diagnose(
    file: UploadFile = File(..., description="T1-weighted MRI NIfTI 파일"),
    skull_strip: bool = Query(False, description="True면 HD-BET skull stripping 먼저 수행 (OASIS, HCP 등 raw MRI 입력 시)"),
) -> DiagnoseResponse:
    _validate_extension(file.filename)

    # 업로드 파일을 임시 경로에 저장
    suffix = ".nii.gz" if file.filename.lower().endswith(".nii.gz") else ".nii"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="빈 파일입니다.",
            )
        tmp.write(contents)
        tmp.flush()
        tmp.close()

        logger.info(f"진단 시작 | 파일: {file.filename} | 크기: {len(contents):,} bytes | skull_strip: {skull_strip}")
        response = run_diagnosis(tmp.name, skull_strip=skull_strip)
        logger.info(
            f"진단 완료 | 판정: {response.classification.prediction} "
            f"| 확신도: {response.classification.confidence:.1%} "
            f"| 처리시간: {response.metadata.get('processing_time_ms', '?')}ms"
        )
        return response

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"워크플로우 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"예상치 못한 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다. 관리자에게 문의하세요.",
        )
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


@router.get("/health", summary="뇌종양 모듈 헬스체크")
def health() -> dict:
    return {"module": "brain", "status": "ok"}
