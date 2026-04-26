import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import DiagnoseResponse, MultiDiagnoseResponse, QualityCheck, DiseaseCandidate
from quality_check import check_quality
from model import load_model, predict, DISEASE_CLASSES

MODULE = "skin"

# 질환별 간략 설명 및 권고사항 (리포트 생성용)
DISEASE_INFO = {
    "광선각화증":   ("만성 자외선 노출로 인한 전암성 병변으로, 조기 치료가 중요합니다.",          "피부과 전문의 조기 방문을 권장합니다."),
    "기저세포암":   ("가장 흔한 피부암으로 천천히 성장하지만 조기 수술이 필요합니다.",            "즉시 피부과 또는 외과 전문의 진료를 받으세요."),
    "멜라닌세포모반": ("일반적인 점으로 대부분 양성이나 변화가 있을 시 조직검사가 필요합니다.",    "ABCDE 기준 변화 시 전문의 상담을 권장합니다."),
    "보웬병":      ("피부 내 편평세포암의 초기 단계로 치료하지 않으면 침습성 암으로 진행될 수 있습니다.", "피부과 전문의 진료 후 치료 계획을 세우세요."),
    "비립종":      ("피부 표면 아래 작은 케라틴 낭종으로 양성 병변입니다.",                    "미용 목적 제거가 필요한 경우 피부과 상담을 권장합니다."),
    "사마귀":      ("인유두종바이러스(HPV) 감염으로 인한 양성 증식으로 전염성이 있습니다.",       "피부과에서 냉동요법 또는 레이저 치료를 권장합니다."),
    "악성흑색종":   ("가장 위험한 피부암으로 즉각적인 조직검사와 수술이 필요합니다.",             "즉시 피부과 또는 종양외과 전문의 진료를 받으세요."),
    "지루각화증":   ("고령에서 흔한 양성 표피 종양으로 치료가 반드시 필요하지는 않습니다.",        "미용 또는 증상 관리 목적의 제거는 피부과 상담을 권장합니다."),
    "편평세포암":   ("자외선이나 만성 염증으로 인한 피부암으로 전이 가능성이 있습니다.",           "즉시 피부과 전문의 진료 및 조직검사를 받으세요."),
    "표피낭종":    ("피부 내 케라틴이 축적된 양성 낭종으로 감염 시 절개 배농이 필요합니다.",       "감염 또는 불편감이 있을 경우 피부과 진료를 받으세요."),
    "피부섬유종":   ("콜라겐 증식으로 생긴 양성 결절로 대부분 치료가 필요 없습니다.",             "크기 변화나 통증이 있을 시 전문의 상담을 권장합니다."),
    "피지샘증식증": ("피지샘이 비대해진 양성 병변으로 중년 이후에 흔히 발생합니다.",               "미용 목적 치료는 피부과에서 레이저 또는 전기소작술을 고려하세요."),
    "혈관종":      ("혈관이 과증식된 양성 종양으로 대부분 자연 소멸되거나 안정적입니다.",          "크기가 크거나 출혈이 있는 경우 피부과 또는 외과 상담을 권장합니다."),
    "화농 육아종": ("작은 혈관이 과증식한 양성 병변으로 출혈이 잦을 수 있습니다.",               "재발을 막기 위해 피부과에서 외과적 제거 또는 레이저 치료를 권장합니다."),
    "흑색점":      ("멜라닌 색소 침착으로 인한 양성 병변이나 흑색종과 감별이 중요합니다.",         "모양이나 색의 변화가 있을 시 피부과 전문의 확인을 권장합니다."),
}


def build_report(
    disease_ko: str,
    disease_en: str,
    confidence: float,
    top3: list,
    quality_passed: bool,
    quality_warning: str | None,
) -> str:
    desc, recommendation = DISEASE_INFO.get(disease_ko, ("알 수 없는 질환입니다.", "전문의 진료를 받으세요."))
    top3_lines = "\n".join(
        f"  {i+1}. {c['disease_ko']} ({c['disease_en']}): {c['confidence']}%"
        for i, c in enumerate(top3)
    )
    quality_note = ""
    if not quality_passed and quality_warning:
        quality_note = f"\n[이미지 품질 경고] {quality_warning}\n"

    return (
        f"=== 피부 AI 진단 리포트 ===\n"
        f"{quality_note}"
        f"\n[진단 결과]\n"
        f"  질환명: {disease_ko} ({disease_en})\n"
        f"  판독 신뢰도: {confidence:.1f}%\n"
        f"\n[감별 진단 Top 3]\n{top3_lines}\n"
        f"\n[질환 설명]\n  {desc}\n"
        f"\n[권고사항]\n  {recommendation}\n"
        f"\n※ 본 결과는 AI 보조 진단이며 최종 판단은 임상의가 내려야 합니다."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 워커 시작 시 모델 사전 로드 (첫 요청 지연 방지)
    try:
        load_model()
    except FileNotFoundError as e:
        print(f"[WARN] 모델 미로드: {e}")
    yield


app = FastAPI(title="MEDI-Zero AI Server [skin]", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "module": MODULE}


@app.get("/ai/skin/health")
def module_health():
    return {"module": MODULE, "display": "피부 질환 진단", "status": "ready", "classes": len(DISEASE_CLASSES)}


@app.post("/ai/skin/diagnose", response_model=DiagnoseResponse)
async def diagnose(
    image: UploadFile = File(...),
    patient_id: str = Form(None),
):
    """단일 환부 이미지 진단 (SKN-01 ~ SKN-06, SKN-09)"""
    # 파일 형식 검사
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="JPG 또는 PNG 파일만 업로드 가능합니다.")

    image_bytes = await image.read()

    # 파일 크기 제한 10MB (SKN-01)
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다.")

    # 이미지 품질 검사 (SKN-09)
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

    # AI 추론
    try:
        result = predict(image_bytes)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Grad-CAM 생성 (SKN-05) - import 여기서 해야 모델 로드 이후 사용 가능
    from gradcam import generate_gradcam_b64
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


@app.post("/ai/skin/diagnose/multi", response_model=MultiDiagnoseResponse)
async def diagnose_multi(
    images: list[UploadFile] = File(...),
    patient_id: str = Form(None),
):
    """다중 환부 이미지 순차 진단 후 통합 리포트 생성 (SKN-08)"""
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="한 번에 최대 10개 이미지까지 업로드 가능합니다.")

    results = []
    from gradcam import generate_gradcam_b64

    for img_file in images:
        if img_file.content_type not in ("image/jpeg", "image/png"):
            results.append(DiagnoseResponse(
                image_name=img_file.filename,
                quality_check=QualityCheck(passed=False, sharpness_score=0, brightness_score=0,
                                           warning="지원하지 않는 형식"),
                report="지원하지 않는 이미지 형식입니다.",
                success=False,
                error="지원하지 않는 이미지 형식입니다.",
            ))
            continue

        image_bytes = await img_file.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            results.append(DiagnoseResponse(
                image_name=img_file.filename,
                quality_check=QualityCheck(passed=False, sharpness_score=0, brightness_score=0,
                                           warning="10MB 초과"),
                report="파일 크기가 10MB를 초과합니다.",
                success=False,
                error="파일 크기 초과",
            ))
            continue

        quality = check_quality(image_bytes)
        quality_obj = QualityCheck(**quality)

        if not quality["passed"]:
            results.append(DiagnoseResponse(
                patient_id=patient_id,
                image_name=img_file.filename,
                quality_check=quality_obj,
                report=f"[품질 불량] {quality['warning']}",
                success=False,
                error=quality["warning"],
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
            patient_id=patient_id,
            image_name=img_file.filename,
            quality_check=quality_obj,
            disease_ko=result["disease_ko"],
            disease_en=result["disease_en"],
            confidence=result["confidence"],
            top3=top3,
            gradcam_b64=gradcam_b64,
            report=report,
            success=True,
        ))

    # 통합 리포트 생성
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
