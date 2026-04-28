"""
LangGraph 기반 피부 질환 진단 파이프라인

노드 흐름:
  quality_check → classify → (gradcam + rag 병렬) → gradcam_explain → report → END
  quality_check 실패 시 → END (에러 반환)
"""

import base64
import io
import logging
from typing import Optional, Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END

from MS.quality_check import check_quality
from MS.model import load_model, predict
from MS.gradcam import generate_gradcam_b64
from MS.rag_engine import retrieve_knowledge
from MS.report_generator import explain_gradcam, generate_report

logger = logging.getLogger("medicore.skin.pipeline")


# ── State 정의 ─────────────────────────────────────────
class SkinDiagnosisState(TypedDict):
    # 입력
    image_bytes: bytes
    patient_id:  Optional[str]
    image_name:  str

    # 품질 검사
    quality_passed:    bool
    quality_warning:   Optional[str]
    sharpness_score:   float
    brightness_score:  float

    # 분류 결과
    disease_ko:  Optional[str]
    disease_en:  Optional[str]
    confidence:  Optional[float]
    top3:        Optional[list]
    class_idx:   Optional[int]
    _tensor:     Any   # torch.Tensor (내부 전달용)
    _pil_img:    Any   # PIL.Image   (내부 전달용)

    # GradCAM
    original_b64:       Optional[str]  # 원본 이미지 base64
    gradcam_b64:        Optional[str]  # 히트맵 오버레이 base64
    gradcam_explanation: Optional[str]  # Gemini Vision 판단 근거

    # RAG
    knowledge_chunks: list[str]

    # 최종 리포트
    report:        str
    triage_level:  Optional[str]
    triage_label:  Optional[str]

    # 상태
    success: bool
    error:   Optional[str]


# ── Triage 매핑 ────────────────────────────────────────
_TRIAGE = {
    "악성흑색종":   ("RED",    "🔴 즉시 전원 권고"),
    "기저세포암":   ("RED",    "🔴 즉시 전원 권고"),
    "편평세포암":   ("RED",    "🔴 즉시 전원 권고"),
    "보웬병":      ("RED",    "🔴 즉시 전원 권고"),
    "광선각화증":   ("YELLOW", "🟡 빠른 처치 필요"),
    "화농 육아종":  ("YELLOW", "🟡 빠른 처치 필요"),
    "멜라닌세포모반": ("GREEN",  "🟢 정기 관찰"),
    "흑색점":      ("GREEN",  "🟢 정기 관찰"),
}
_DEFAULT_TRIAGE = ("GREEN", "🟢 일반")


# ── 유틸 ───────────────────────────────────────────────
def _pil_to_b64(pil_img) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── 노드 함수 ──────────────────────────────────────────
def quality_check_node(state: SkinDiagnosisState) -> dict:
    result = check_quality(state["image_bytes"])
    return {
        "quality_passed":   result["passed"],
        "quality_warning":  result.get("warning"),
        "sharpness_score":  result["sharpness_score"],
        "brightness_score": result["brightness_score"],
    }


def classify_node(state: SkinDiagnosisState) -> dict:
    try:
        result = predict(state["image_bytes"])
        return {
            "disease_ko": result["disease_ko"],
            "disease_en": result["disease_en"],
            "confidence": result["confidence"],
            "top3":       result["top3"],
            "class_idx":  result["class_idx"],
            "_tensor":    result["tensor"],
            "_pil_img":   result["pil_img"],
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e), "report": str(e)}


def gradcam_node(state: SkinDiagnosisState) -> dict:
    try:
        gradcam_b64 = generate_gradcam_b64(state["image_bytes"], state["class_idx"])
        original_b64 = _pil_to_b64(state["_pil_img"])
        return {"gradcam_b64": gradcam_b64, "original_b64": original_b64}
    except Exception as e:
        logger.warning(f"GradCAM 생성 실패: {e}")
        return {"gradcam_b64": None, "original_b64": None}


def rag_node(state: SkinDiagnosisState) -> dict:
    query  = f"{state['disease_ko']} 피부 병변 임상 특징 치료"
    chunks = retrieve_knowledge(query, top_k=3)
    return {"knowledge_chunks": chunks}


def gradcam_explain_node(state: SkinDiagnosisState) -> dict:
    if not state.get("gradcam_b64"):
        return {"gradcam_explanation": "GradCAM 이미지를 생성하지 못해 분석을 수행할 수 없습니다."}
    explanation = explain_gradcam(
        state["gradcam_b64"],
        state["disease_ko"],
        state["confidence"],
    )
    return {"gradcam_explanation": explanation}


def report_node(state: SkinDiagnosisState) -> dict:
    report = generate_report(
        disease_ko=state["disease_ko"],
        disease_en=state["disease_en"],
        confidence=state["confidence"],
        top3=state["top3"],
        knowledge_chunks=state.get("knowledge_chunks", []),
        gradcam_explanation=state.get("gradcam_explanation", ""),
        quality_warning=state.get("quality_warning"),
    )
    level, label = _TRIAGE.get(state["disease_ko"], _DEFAULT_TRIAGE)
    return {
        "report":       report,
        "triage_level": level,
        "triage_label": label,
        "success":      True,
        "error":        None,
    }


# ── 조건 분기 ─────────────────────────────────────────
def _route_quality(state: SkinDiagnosisState) -> str:
    return "classify" if state["quality_passed"] else END


def _route_classify(state: SkinDiagnosisState) -> str:
    return END if not state.get("success", True) and state.get("error") else "gradcam_and_rag"


# ── 그래프 빌드 ────────────────────────────────────────
def build_pipeline() -> StateGraph:
    graph = StateGraph(SkinDiagnosisState)

    graph.add_node("quality_check",    quality_check_node)
    graph.add_node("classify",         classify_node)
    graph.add_node("gradcam",          gradcam_node)
    graph.add_node("rag",              rag_node)
    graph.add_node("gradcam_explain",  gradcam_explain_node)
    graph.add_node("report",           report_node)

    graph.set_entry_point("quality_check")

    graph.add_conditional_edges(
        "quality_check",
        _route_quality,
        {"classify": "classify", END: END},
    )
    graph.add_conditional_edges(
        "classify",
        _route_classify,
        {"gradcam_and_rag": "gradcam", END: END},
    )

    # gradcam, rag 병렬 실행 → 둘 다 끝나면 gradcam_explain
    graph.add_edge("gradcam", "rag")
    graph.add_edge("rag",     "gradcam_explain")
    graph.add_edge("gradcam_explain", "report")
    graph.add_edge("report",  END)

    return graph.compile()


# 싱글톤 파이프라인
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        load_model()  # 서버 시작 시 모델 사전 로드
        _pipeline = build_pipeline()
        logger.info("LangGraph 피부 진단 파이프라인 초기화 완료")
    return _pipeline


def run_pipeline(
    image_bytes: bytes,
    image_name:  str,
    patient_id:  Optional[str] = None,
) -> SkinDiagnosisState:
    pipeline = get_pipeline()

    initial_state: SkinDiagnosisState = {
        "image_bytes":       image_bytes,
        "patient_id":        patient_id,
        "image_name":        image_name,
        "quality_passed":    False,
        "quality_warning":   None,
        "sharpness_score":   0.0,
        "brightness_score":  0.0,
        "disease_ko":        None,
        "disease_en":        None,
        "confidence":        None,
        "top3":              None,
        "class_idx":         None,
        "_tensor":           None,
        "_pil_img":          None,
        "original_b64":      None,
        "gradcam_b64":       None,
        "gradcam_explanation": None,
        "knowledge_chunks":  [],
        "report":            "",
        "triage_level":      None,
        "triage_label":      None,
        "success":           False,
        "error":             None,
    }

    return pipeline.invoke(initial_state)