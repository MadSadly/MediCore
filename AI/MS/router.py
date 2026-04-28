from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from MS.schemas import DiagnoseResponse, MultiDiagnoseResponse, QualityCheck, DiseaseCandidate
from MS.pipeline import run_pipeline

router = APIRouter()


def _state_to_response(state: dict, image_name: str) -> DiagnoseResponse:
    """파이프라인 State → DiagnoseResponse 변환."""
    quality_obj = QualityCheck(
        passed=state["quality_passed"],
        sharpness_score=state["sharpness_score"],
        brightness_score=state["brightness_score"],
        warning=state.get("quality_warning"),
    )
    top3 = [DiseaseCandidate(**c) for c in state["top3"]] if state.get("top3") else None

    return DiagnoseResponse(
        patient_id=state.get("patient_id"),
        image_name=image_name,
        quality_check=quality_obj,
        disease_ko=state.get("disease_ko"),
        disease_en=state.get("disease_en"),
        confidence=state.get("confidence"),
        top3=top3,
        original_b64=state.get("original_b64"),
        gradcam_b64=state.get("gradcam_b64"),
        gradcam_explanation=state.get("gradcam_explanation"),
        report=state.get("report", ""),
        triage_level=state.get("triage_level"),
        triage_label=state.get("triage_label"),
        success=state.get("success", False),
        error=state.get("error"),
    )


@router.get("/skin/health")
def skin_health():
    from MS.model import DISEASE_CLASSES
    return {
        "module":  "skin",
        "display": "피부 질환 진단",
        "status":  "ready",
        "classes": len(DISEASE_CLASSES),
        "pipeline": "LangGraph",
    }


@router.post("/skin/diagnose", response_model=DiagnoseResponse)
async def skin_diagnose(
    image:      UploadFile = File(...),
    patient_id: str        = Form(None),
):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="JPG 또는 PNG 파일만 업로드 가능합니다.")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다.")

    try:
        state = run_pipeline(image_bytes, image.filename, patient_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"진단 파이프라인 오류: {e}")

    return _state_to_response(state, image.filename)


@router.post("/skin/diagnose/multi", response_model=MultiDiagnoseResponse)
async def skin_diagnose_multi(
    images:     list[UploadFile] = File(...),
    patient_id: str              = Form(None),
):
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="한 번에 최대 10개 이미지까지 업로드 가능합니다.")

    results = []
    for img_file in images:
        if img_file.content_type not in ("image/jpeg", "image/png"):
            results.append(DiagnoseResponse(
                image_name=img_file.filename,
                quality_check=QualityCheck(passed=False, sharpness_score=0, brightness_score=0,
                                           warning="지원하지 않는 형식"),
                report="지원하지 않는 이미지 형식입니다.",
                success=False, error="지원하지 않는 이미지 형식",
            ))
            continue

        image_bytes = await img_file.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            results.append(DiagnoseResponse(
                image_name=img_file.filename,
                quality_check=QualityCheck(passed=False, sharpness_score=0, brightness_score=0,
                                           warning="10MB 초과"),
                report="파일 크기가 10MB를 초과합니다.",
                success=False, error="파일 크기 초과",
            ))
            continue

        try:
            state = run_pipeline(image_bytes, img_file.filename, patient_id)
            results.append(_state_to_response(state, img_file.filename))
        except Exception as e:
            results.append(DiagnoseResponse(
                image_name=img_file.filename,
                quality_check=QualityCheck(passed=False, sharpness_score=0, brightness_score=0),
                report=f"처리 오류: {e}",
                success=False, error=str(e),
            ))

    success_list    = [r for r in results if r.success]
    diseases_found  = list({r.disease_ko for r in success_list if r.disease_ko})
    summary = (
        f"=== 통합 피부 AI 진단 리포트 ===\n"
        f"분석 이미지 수: {len(images)}장 / 성공: {len(success_list)}장\n"
        f"검출된 질환: {', '.join(diseases_found) if diseases_found else '없음'}\n"
        f"\n※ 각 환부별 상세 결과는 개별 리포트를 참조하세요.\n"
        f"※ 본 결과는 AI 보조 진단이며 최종 판단은 임상의가 내려야 합니다."
    )
    return MultiDiagnoseResponse(
        patient_id=patient_id,
        total_images=len(images),
        results=results,
        summary_report=summary,
    )