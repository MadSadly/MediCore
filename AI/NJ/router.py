"""
신부전 진단 API 라우터
"""
import logging
from fastapi import APIRouter
from .schemas import (
    Alert,
    KidneyDiagnoseRequest,
    KidneyDiagnoseResponse,
    HealthResponse,
)
from .core import KidneyPredictor
from .rag import query_and_generate

logger = logging.getLogger("medicore.kidney")
router = APIRouter()

_predictor = None


def get_predictor() -> KidneyPredictor:
    global _predictor
    if _predictor is None:
        _predictor = KidneyPredictor()
    return _predictor


# ── 위험 알림 트리거 ───────────────────────────────────────────────────
def check_alerts(req: KidneyDiagnoseRequest, prediction: str) -> list[Alert]:
    alerts: list[Alert] = []

    # eGFR — 투석 기준 / 중증 저하
    if req.egfr is not None:
        if req.egfr < 15:
            alerts.append(Alert(
                level="critical", code="DIALYSIS_THRESHOLD",
                message=f"eGFR {req.egfr} mL/min — 투석 시작 기준 도달 (< 15), 즉시 신장내과 의뢰",
                marker="egfr",
            ))
        elif req.egfr < 30:
            alerts.append(Alert(
                level="warning", code="SEVERE_GFR_DECLINE",
                message=f"eGFR {req.egfr} mL/min — 중증 신기능 저하, 투석 접근로 조성 검토 필요",
                marker="egfr",
            ))

    # 칼륨 — 부정맥 위험
    if req.pot is not None:
        if req.pot >= 6.0:
            alerts.append(Alert(
                level="critical", code="HYPERKALEMIA_CRITICAL",
                message=f"칼륨 {req.pot} mEq/L — 생명 위협 수준 고칼륨혈증, 즉각 응급 처치 필요",
                marker="pot",
            ))
        elif req.pot >= 5.5:
            alerts.append(Alert(
                level="warning", code="HYPERKALEMIA",
                message=f"칼륨 {req.pot} mEq/L — 고칼륨혈증 위험, 부정맥 주의 및 식이 제한 필요",
                marker="pot",
            ))
        elif req.pot < 3.5:
            alerts.append(Alert(
                level="warning", code="HYPOKALEMIA",
                message=f"칼륨 {req.pot} mEq/L — 저칼륨혈증, 근육 약화·부정맥 위험",
                marker="pot",
            ))

    # BUN — 급성 악화 감지
    if req.bu is not None:
        if req.bu > 100:
            alerts.append(Alert(
                level="critical", code="CRITICAL_BUN",
                message=f"BUN {req.bu} mg/dL — 급성 악화 의심, 즉시 정밀 검사 필요",
                marker="bu",
            ))
        elif req.bu > 50:
            alerts.append(Alert(
                level="warning", code="ELEVATED_BUN",
                message=f"BUN {req.bu} mg/dL — 혈중 요소 질소 상승, 신장 부하 증가 상태",
                marker="bu",
            ))

    # 크레아티닌 — 신기능 저하 지표
    if req.sc is not None:
        if req.sc > 10:
            alerts.append(Alert(
                level="critical", code="CRITICAL_CREATININE",
                message=f"크레아티닌 {req.sc} mg/dL — 위험 수준, 즉시 신장내과 의뢰",
                marker="sc",
            ))
        elif req.sc > 4:
            alerts.append(Alert(
                level="warning", code="HIGH_CREATININE",
                message=f"크레아티닌 {req.sc} mg/dL — 중증 신기능 저하 지표",
                marker="sc",
            ))

    # 혈압 — 신기능 악화 촉진
    if req.bp is not None:
        if req.bp >= 180:
            alerts.append(Alert(
                level="critical", code="HYPERTENSIVE_CRISIS",
                message=f"혈압 {req.bp} mmHg — 고혈압 위기, 즉각 조치 필요",
                marker="bp",
            ))
        elif req.bp >= 140:
            alerts.append(Alert(
                level="warning", code="UNCONTROLLED_HTN",
                message=f"혈압 {req.bp} mmHg — 혈압 미조절, 신기능 악화 위험 증가",
                marker="bp",
            ))

    # 헤모글로빈 — 신성 빈혈
    if req.hemo is not None:
        if req.hemo < 8:
            alerts.append(Alert(
                level="critical", code="SEVERE_ANEMIA",
                message=f"헤모글로빈 {req.hemo} g/dL — 중증 빈혈, 수혈 고려",
                marker="hemo",
            ))
        elif req.hemo < 10:
            alerts.append(Alert(
                level="warning", code="ANEMIA",
                message=f"헤모글로빈 {req.hemo} g/dL — 신성 빈혈 의심, EPO 치료 고려",
                marker="hemo",
            ))

    # 조합 트리거: 고칼륨 + 중증 신기능 저하 → 응급 위험
    if (req.pot is not None and req.egfr is not None
            and req.pot >= 5.5 and req.egfr < 30):
        alerts.append(Alert(
            level="critical", code="HYPERKALEMIA_SEVERE_CKD",
            message=f"고칼륨혈증 ({req.pot} mEq/L) + 중증 신기능 저하 (eGFR {req.egfr}) — 응급 위험 조합",
            marker="pot+egfr",
        ))

    # 말기 신부전 단계
    if prediction == "Stage5":
        alerts.append(Alert(
            level="critical", code="ESRD",
            message="말기 신부전 (ESRD) — 투석 또는 신장이식 즉시 상담 필요",
            marker="stage",
        ))

    # critical 먼저, warning 다음 순으로 정렬
    alerts.sort(key=lambda a: (0 if a.level == "critical" else 1))
    return alerts


# ── 라우터 ─────────────────────────────────────────────────────────────
@router.get("/ai/kidney/health", response_model=HealthResponse)
def kidney_health():
    try:
        get_predictor()
        loaded = True
    except Exception:
        loaded = False
    return HealthResponse(
        module="kidney",
        status="ready" if loaded else "model_not_found",
        model_loaded=loaded,
    )


@router.post("/ai/kidney/diagnose", response_model=KidneyDiagnoseResponse)
async def kidney_diagnose(req: KidneyDiagnoseRequest):
    # 1. TabNet 예측
    predictor     = get_predictor()
    clinical_data = req.dict(exclude={"query"}, exclude_none=False)
    dl_result     = predictor.predict(clinical_data)
    prediction    = dl_result["prediction"]

    logger.info(f"신부전 예측: {prediction} (신뢰도: {dl_result['confidence']:.3f})")

    # 2. 위험 알림 트리거
    alerts = check_alerts(req, prediction)
    if alerts:
        levels = [a.level for a in alerts]
        logger.warning(f"알림 발생 {len(alerts)}건 — {levels}")

    # 3. RAG + 소견서
    query      = req.query or f"{prediction} 단계의 치료 방향은?"
    rag_result = query_and_generate(
        query,
        prediction,
        confidence = dl_result["confidence"],
        input_data = req.dict(exclude={"query"}),
    )

    # 4. 피처 기여도
    try:
        feature_importance = predictor.explain(clinical_data)
    except Exception as e:
        logger.warning(f"피처 기여도 계산 실패: {e}")
        feature_importance = None

    return KidneyDiagnoseResponse(
        module             = "kidney",
        prediction         = prediction,
        confidence         = dl_result["confidence"],
        description        = dl_result["description"],
        severity           = dl_result["severity"],
        dialysis_required  = dl_result["dialysis_required"],
        probabilities      = dl_result["probabilities"],
        alerts             = alerts,
        rag_answer         = rag_result["answer"],
        rag_sources        = rag_result["sources"],
        feature_importance = feature_importance,
    )
