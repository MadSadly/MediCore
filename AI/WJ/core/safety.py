from __future__ import annotations

from WJ.schemas.response import SafetyAssessment

DISCLAIMER = (
    "이 결과는 AI 보조 도구의 출력이며, "
    "최종 진단은 영상의학과 전문의가 수행해야 합니다."
)


def apply_safety_check(classification: dict) -> tuple[SafetyAssessment, str]:
    """
    분류 결과에 신뢰도 기반 임상 권고를 적용.

    Args:
        classification: predict_tumor() 반환값
            {"prediction", "tumor_fraction", "tumor_probability", "normal_probability", "confidence"}
            confidence: 결정 경계 거리 기반 [0.5, 1.0] — 0.5에 가까울수록 판정 불확실

    Returns:
        (SafetyAssessment, disclaimer) 튜플
    """
    conf = classification["confidence"]
    pred = classification["prediction"]
    tumor_prob = classification["tumor_probability"]

    if conf < 0.85:
        assessment = SafetyAssessment(
            risk_level="high_uncertainty",
            clinical_action="전문의 검토 필수 (확신도 낮음)",
            requires_specialist_review=True,
        )
    elif pred == "Tumor" and conf < 0.95:
        assessment = SafetyAssessment(
            risk_level="moderate",
            clinical_action="추가 검사 권고",
            requires_specialist_review=True,
        )
    elif pred == "Normal" and tumor_prob > 0.05:
        assessment = SafetyAssessment(
            risk_level="low",
            clinical_action="정상이지만 추적 관찰 권고",
            requires_specialist_review=False,
        )
    else:
        assessment = SafetyAssessment(
            risk_level="low",
            clinical_action="결과 참고 가능",
            requires_specialist_review=False,
        )

    return assessment, DISCLAIMER
