from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from MS.schemas import DiagnoseResponse, MultiDiagnoseResponse, QualityCheck, DiseaseCandidate
from MS.quality_check import check_quality
from MS.model import load_model, predict, DISEASE_CLASSES
from MS.main import build_report

router = APIRouter()

# ──────────────────────────────────────────────────────────────
# 통합 AI 서버(AI/main.py)가 이 router를 prefix="/ai" 로 mount함
# 프론트엔드 → Vite proxy /ai/* → localhost:8000/* → /skin/*
# ──────────────────────────────────────────────────────────────

@router.get("/skin/health")
def skin_health():
    return {"module": "skin", "display": "피부 질환 진단", "status": "ready", "classes": len(DISEASE_CLASSES)}


@router.post("/skin/diagnose", response_model=DiagnoseResponse)
async def skin_diagnose(
    image: UploadFile = File(...),
    patient_id: str = Form(None),
):
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="JPG 또는 PNG 파일만 업로드 가능합니다.")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다.")

    quality = check_quality(image_bytes)
    quality_obj = QualityCheck(**quality)

    if not quality["passed"]:
        return DiagnoseResponse(
            patient_id=patient_id,
            image_name=image.filename,
            quality_check=quality_obj,
            report=f"[이미지 품질 불량] {quality['warning']}",
            success=False,
            error=quality["warning"],
        )

    try:
        result = predict(image_bytes)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    from MS.gradcam import generate_gradcam_b64
    gradcam_b64 = generate_gradcam_b64(image_bytes, result["class_idx"])
    top3 = [DiseaseCandidate(**c) for c in result["top3"]]
    report = build_report(
        result["disease_ko"], result["disease_en"], result["confidence"],
        result["top3"], quality["passed"], quality["warning"],
    )

    return DiagnoseResponse(
        patient_id=patient_id,
        image_name=image.filename,
        quality_check=quality_obj,
        disease_ko=result["disease_ko"],
        disease_en=result["disease_en"],
        confidence=result["confidence"],
        top3=top3,
        gradcam_b64=gradcam_b64,
        report=report,
        success=True,
    )


@router.post("/skin/diagnose/multi", response_model=MultiDiagnoseResponse)
async def skin_diagnose_multi(
    images: list[UploadFile] = File(...),
    patient_id: str = Form(None),
):
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="한 번에 최대 10개 이미지까지 업로드 가능합니다.")

    results = []
    from MS.gradcam import generate_gradcam_b64

    for img_file in images:
        if img_file.content_type not in ("image/jpeg", "image/png"):
            results.append(DiagnoseResponse(
                image_name=img_file.filename,
                quality_check=QualityCheck(passed=False, sharpness_score=0, brightness_score=0, warning="지원하지 않는 형식"),
                report="지원하지 않는 이미지 형식입니다.",
                success=False, error="지원하지 않는 이미지 형식입니다.",
            ))
            continue

        image_bytes = await img_file.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            results.append(DiagnoseResponse(
                image_name=img_file.filename,
                quality_check=QualityCheck(passed=False, sharpness_score=0, brightness_score=0, warning="10MB 초과"),
                report="파일 크기가 10MB를 초과합니다.",
                success=False, error="파일 크기 초과",
            ))
            continue

        quality = check_quality(image_bytes)
        quality_obj = QualityCheck(**quality)
        if not quality["passed"]:
            results.append(DiagnoseResponse(
                patient_id=patient_id, image_name=img_file.filename,
                quality_check=quality_obj,
                report=f"[품질 불량] {quality['warning']}",
                success=False, error=quality["warning"],
            ))
            continue

        try:
            result = predict(image_bytes)
        except FileNotFoundError as e:
            raise HTTPException(status_code=503, detail=str(e))

        gradcam_b64 = generate_gradcam_b64(image_bytes, result["class_idx"])
        top3 = [DiseaseCandidate(**c) for c in result["top3"]]
        report = build_report(
            result["disease_ko"], result["disease_en"], result["confidence"],
            result["top3"], quality["passed"], quality["warning"],
        )
        results.append(DiagnoseResponse(
            patient_id=patient_id, image_name=img_file.filename,
            quality_check=quality_obj,
            disease_ko=result["disease_ko"], disease_en=result["disease_en"],
            confidence=result["confidence"], top3=top3,
            gradcam_b64=gradcam_b64, report=report, success=True,
        ))

    success_list = [r for r in results if r.success]
    diseases_found = list({r.disease_ko for r in success_list})
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