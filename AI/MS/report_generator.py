import os
import base64
import logging
from typing import Optional

logger = logging.getLogger("medicore.skin.report")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-001")

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        try:
            from vertexai.generative_models import GenerativeModel
            _llm = GenerativeModel(GEMINI_MODEL)
        except Exception as e:
            logger.warning(f"Gemini 모델 로드 실패: {e}")
    return _llm


def explain_gradcam(
    gradcam_b64: str,
    disease_ko: str,
    confidence: float,
) -> str:
    """Grad-CAM 히트맵 이미지를 Gemini Vision으로 분석해 판단 근거를 언어화."""
    llm = _get_llm()
    if llm is None:
        return "GradCAM 분석을 수행할 수 없습니다. (Vertex AI 미설정)"

    try:
        from vertexai.generative_models import Part, Image as GeminiImage

        image_bytes = base64.b64decode(gradcam_b64)
        image_part  = Part.from_data(data=image_bytes, mime_type="image/png")

        prompt = f"""당신은 피부과 AI 진단 보조 시스템의 설명 모듈입니다.

아래 이미지는 EfficientNet-B4 모델이 '{disease_ko}'를 {confidence:.1f}% 신뢰도로 예측할 때
Grad-CAM으로 시각화한 결과입니다.
빨간색/주황색 영역이 모델이 집중한 부위이고, 파란색은 집중하지 않은 부위입니다.

피부과 임상 관점에서 다음 두 가지를 3문장 이내로 간결하게 서술하세요:
1. 모델이 집중한 부위 (색상 기준으로 구체적으로)
2. 그 부위가 '{disease_ko}' 진단에서 갖는 임상적 의미

전문 의학 용어를 사용하되 짧고 명확하게 작성하세요."""

        response = llm.generate_content([image_part, prompt])
        return response.text.strip()

    except Exception as e:
        logger.warning(f"GradCAM 설명 생성 실패: {e}")
        return f"모델이 {disease_ko} 특징적 병변 부위에 집중하여 판단했습니다."


def generate_report(
    disease_ko: str,
    disease_en: str,
    confidence: float,
    top3: list[dict],
    knowledge_chunks: list[str],
    gradcam_explanation: str,
    quality_warning: Optional[str] = None,
) -> str:
    """RAG 문서 + GradCAM 설명을 바탕으로 Gemini Flash 임상 리포트 생성."""
    llm = _get_llm()
    if llm is None:
        return _fallback_report(disease_ko, disease_en, confidence, top3, quality_warning)

    top3_text = "\n".join(
        f"  {i+1}. {c['disease_ko']} ({c['disease_en']}): {c['confidence']:.1f}%"
        for i, c in enumerate(top3)
    )
    knowledge_text = "\n\n".join(knowledge_chunks) if knowledge_chunks else "검색된 지식 없음"
    quality_note   = f"\n[이미지 품질 경고] {quality_warning}\n" if quality_warning else ""

    prompt = f"""당신은 피부과 AI 진단 보조 시스템입니다.
아래 정보를 바탕으로 임상의가 참고할 수 있는 진단 리포트를 작성하세요.

{quality_note}
[AI 진단 결과]
- 주요 진단: {disease_ko} ({disease_en})
- 신뢰도: {confidence:.1f}%
- 감별 진단 Top3:
{top3_text}

[AI 판단 근거 (Grad-CAM 분석)]
{gradcam_explanation}

[관련 의학 지식 (RAG 검색 결과)]
{knowledge_text}

위 정보를 종합해 아래 형식으로 리포트를 작성하세요.
각 항목은 2~4문장으로 간결하게 작성하세요.

[트리아지 등급]
(RED/YELLOW/GREEN 중 선택 및 근거)

[진단 소견]
(AI 판단 근거와 임상 특징 요약)

[감별 진단 고려사항]
(Top3 질환 간 감별 포인트)

[권고 처치]
(즉각적 처치 및 전문의 의뢰 여부)

[참고 가이드라인]
(관련 국제 가이드라인 명시)

※ 본 결과는 AI 보조 진단이며 최종 판단은 임상의가 내려야 합니다."""

    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.warning(f"리포트 생성 실패: {e}")
        return _fallback_report(disease_ko, disease_en, confidence, top3, quality_warning)


def _fallback_report(
    disease_ko: str,
    disease_en: str,
    confidence: float,
    top3: list[dict],
    quality_warning: Optional[str],
) -> str:
    """Gemini 호출 실패 시 기본 리포트."""
    top3_lines = "\n".join(
        f"  {i+1}. {c['disease_ko']} ({c['disease_en']}): {c['confidence']:.1f}%"
        for i, c in enumerate(top3)
    )
    quality_note = f"\n[이미지 품질 경고] {quality_warning}\n" if quality_warning else ""
    return (
        f"=== 피부 AI 진단 리포트 ===\n"
        f"{quality_note}"
        f"\n[진단 결과]\n"
        f"  질환명: {disease_ko} ({disease_en})\n"
        f"  신뢰도: {confidence:.1f}%\n"
        f"\n[감별 진단 Top3]\n{top3_lines}\n"
        f"\n※ 본 결과는 AI 보조 진단이며 최종 판단은 임상의가 내려야 합니다."
    )