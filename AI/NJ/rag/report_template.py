"""
진단 소견서 정형화 템플릿

구조 (매 호출마다 동일한 형식 보장):
  1. 핵심 수치 요약 및 CKD 단계 진단   ← 코드 생성
  2. 위험도 평가 및 원인 추정           ← LLM 생성
  3. 이상 소견 해석                     ← LLM 생성
  4. 치료 권고사항                      ← LLM 생성
     4-1. 약물 처방
     4-2. 생활 습관 및 비약물 치료
     4-3. 추적 검사 계획
  5. 종합 진단 소견                     ← LLM 생성 (폴백: 수치 기반 문장 자동 생성)
"""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

# ── 상수 ──────────────────────────────────────────────────────────
DIV  = "━" * 52
DIV2 = "─" * 52


def _wc_ljust(s: str, width: int) -> str:
    """한글 2바이트 문자를 고려한 left-justify (브라우저 monospace 기준)."""
    display = sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in s)
    return s + " " * max(0, width - display)

STAGE_META = {
    "Normal_Stage1": ("정상 / 1단계", "eGFR ≥ 90",  "정상 신기능",     "저위험"),
    "Stage2":        ("2단계",        "eGFR 60-89", "경미한 신기능 저하", "저위험"),
    "Stage3":        ("3단계",        "eGFR 30-59", "중등도 신기능 저하", "중위험"),
    "Stage4":        ("4단계",        "eGFR 15-29", "중증 신기능 저하",  "고위험"),
    "Stage5":        ("5단계",        "eGFR < 15",  "말기 신부전(ESRD)", "최고위험"),
}

# 핵심 수치 표시 순서 및 정상 범위
FIELD_META = [
    ("egfr", "eGFR",          "mL/min", "> 60"),
    ("sc",   "크레아티닌",    "mg/dL",  "0.7~1.2"),
    ("bu",   "BUN",           "mg/dL",  "7~20"),
    ("pot",  "칼륨(K+)",      "mEq/L",  "3.5~5.0"),
    ("bp",   "혈압",          "mmHg",   "< 130"),
    ("hemo", "헤모글로빈",    "g/dL",   "12~17"),
    ("al",   "알부민",        "g/dL",   "3.5~5.0"),
    ("bgr",  "혈당",          "mg/dL",  "70~140"),
    ("sod",  "나트륨(Na+)",   "mEq/L",  "136~145"),
]

COMORBID_LABELS = {
    "htn": "고혈압",
    "dm":  "당뇨",
    "pe":  "부종(부종)",
    "cad": "관상동맥질환",
    "ane": "빈혈",
}


# ── 섹션 1: 코드 생성 ─────────────────────────────────────────────

def _stage_visual(prediction: str) -> str:
    """CKD 단계 진행을 한 줄 텍스트로 시각화."""
    stages = ["Normal_Stage1", "Stage2", "Stage3", "Stage4", "Stage5"]
    labels = ["정상/1", "2단계", "3단계", "4단계", "5단계"]

    parts = []
    for s, l in zip(stages, labels):
        parts.append(f"[▶ {l} ◀]" if s == prediction else l)

    return "  " + " → ".join(parts)


def build_section1(prediction: str, confidence: float, input_data: dict) -> str:
    """섹션 1: 핵심 수치 요약 + CKD 단계 시각화 (코드 생성, LLM 불필요)."""
    meta = STAGE_META.get(prediction, ("알 수 없음", "—", "—", "—"))

    # 수치 테이블 — 한글 2바이트 보정 패딩으로 정렬
    COL_NAME = 10   # 항목명 표시폭 (display units)
    COL_VAL  = 8    # 측정값
    COL_UNIT = 8    # 단위
    header = (
        f"  {_wc_ljust('항목', COL_NAME)}  "
        f"{_wc_ljust('측정값', COL_VAL)}  "
        f"{_wc_ljust('단위', COL_UNIT)}  정상 범위"
    )
    rows = [header, f"  {DIV2}"]
    for key, name, unit, normal in FIELD_META:
        val = input_data.get(key)
        if val is not None:
            val_str = f"{float(val):.1f}"
            rows.append(
                f"  {_wc_ljust(name, COL_NAME)}  "
                f"{_wc_ljust(val_str, COL_VAL)}  "
                f"{_wc_ljust(unit, COL_UNIT)}  {normal}"
            )

    table = "\n".join(rows)

    # 동반 증상
    comorbid = [
        label for key, label in COMORBID_LABELS.items()
        if input_data.get(key) in ("yes", True, "1", 1)
    ]
    comorbid_str = ", ".join(comorbid) if comorbid else "해당 없음"

    visual = _stage_visual(prediction)

    return (
        f"{table}\n\n"
        f"  동반 증상: {comorbid_str}\n\n"
        f"  CKD 단계 진행:\n{visual}\n\n"
        f"  진단 결과: {meta[0]}  ({meta[2]}, {meta[1]})\n"
        f"  위험 등급: {meta[3]}\n"
        f"  AI 신뢰도: {confidence * 100:.1f}%"
    )


# ── LLM 프롬프트 빌드 ─────────────────────────────────────────────

def build_llm_prompt(
    prediction: str,
    input_data: dict,
    contexts: list,
    query: str,
) -> str:
    """LLM에게 섹션 2~4를 채우도록 요청하는 구조화 프롬프트."""
    meta = STAGE_META.get(prediction, ("", "", "", ""))

    # 임상 수치 요약 (프롬프트용 한 줄)
    vals = []
    for key, name, unit, _ in FIELD_META:
        v = input_data.get(key)
        if v is not None:
            vals.append(f"{name} {float(v):.1f} {unit}")
    vals_str = " | ".join(vals) if vals else "수치 미입력"

    comorbid = [label for k, label in COMORBID_LABELS.items()
                if input_data.get(k) in ("yes", True, "1", 1)]
    comorbid_str = ", ".join(comorbid) if comorbid else "없음"

    # KDIGO 참고자료
    ctx_text = "\n\n".join(
        f"[참고자료 {i+1}] 출처: {c['source']}\n{c['content']}"
        for i, c in enumerate(contexts[:5])
    )

    clinical_q = query or f"{prediction} 단계 환자의 치료 계획"

    return (
        "[지시사항]\n"
        "반드시 한국어로만 작성하십시오. 영어·외국어 절대 금지.\n"
        "아래 KDIGO 가이드라인 참고자료만을 근거로 작성하십시오.\n"
        "추측이나 가이드라인에 없는 내용을 절대 작성하지 마십시오.\n\n"
        "[환자 임상 정보]\n"
        f"CKD 단계: {meta[0]} ({meta[2]}, {meta[1]})\n"
        f"임상 수치: {vals_str}\n"
        f"동반 증상: {comorbid_str}\n"
        f"임상 질문: {clinical_q}\n\n"
        "[KDIGO 가이드라인 참고자료]\n"
        f"{ctx_text}\n\n"
        "[작성 지시]\n"
        "아래 6개 항목 제목을 그대로 유지하며 내용을 한국어로 작성하시오.\n"
        "5번 항목은 반드시 자연스러운 문장 형식(단락)으로 상세하게 작성하시오. 항목 번호나 기호를 사용하지 말 것.\n\n"
        "2. 위험도 평가 및 원인 추정\n\n"
        "3. 이상 소견 해석\n\n"
        "4-1. 약물 처방\n\n"
        "4-2. 생활 습관 및 비약물 치료\n\n"
        "4-3. 추적 검사 계획\n\n"
        "5. 종합 진단 소견"
    )


# ── LangChain Pydantic 파서 ───────────────────────────────────────

class ReportSections(BaseModel):
    sec2:  str = Field(default="", description="위험도 평가 및 원인 추정 내용 (한국어)")
    sec3:  str = Field(default="", description="이상 소견 해석 내용 (한국어)")
    sec41: str = Field(default="", description="약물 처방 내용 (한국어)")
    sec42: str = Field(default="", description="생활 습관 및 비약물 치료 내용 (한국어)")
    sec43: str = Field(default="", description="추적 검사 계획 내용 (한국어)")
    sec5:  str = Field(default="", description="종합 진단 소견 — 자연스러운 단락 형식, 항목 번호 없이 (한국어)")


def get_report_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=ReportSections)


_EARLY_STAGE_FOCUS = {
    "Normal_Stage1": (
        "이 환자는 신기능이 정상이거나 1단계입니다. "
        "치료 목표는 '진행 예방'과 '위험 요인 관리'입니다. "
        "약물 처방은 단백뇨·고혈압·당뇨 동반 여부에 따라 ACE억제제/ARB, SGLT2억제제 사용 기준을 구체적으로 작성하세요. "
        "추적 검사는 연 1회 기준으로 항목별 주기를 명시하세요."
    ),
    "Stage2": (
        "이 환자는 CKD 2단계(경도 신기능 저하)입니다. "
        "치료 목표는 '진행 억제'와 '심혈관 위험 감소'입니다. "
        "ACE억제제/ARB의 신장 보호 효과, SGLT2억제제 적응증, 혈압 목표(130/80 mmHg 미만)를 구체적으로 작성하세요. "
        "추적 검사는 6개월 주기 기준으로 항목별로 명시하세요."
    ),
    "Stage3": (
        "이 환자는 CKD 3단계(중등도 신기능 저하)입니다. "
        "합병증(빈혈, 대사성 산증, 골미네랄 이상, 고칼륨혈증) 관리가 핵심입니다. "
        "각 합병증에 대한 약물 기준(ESA, 철분제, 인결합제, 활성비타민D 등)과 시작 기준을 구체적으로 작성하세요. "
        "추적 검사는 3개월 주기 기준으로 항목별로 명시하세요."
    ),
}

_EARLY_STAGES = frozenset({"Normal_Stage1", "Stage2", "Stage3"})


def build_lc_prompt(
    prediction: str,
    input_data: dict,
    contexts: list,
    query: str,
    format_instructions: str,
) -> str:
    """LangChain PydanticOutputParser 전용 프롬프트 — JSON 형식으로 응답 요청."""
    meta = STAGE_META.get(prediction, ("", "", "", ""))

    vals = []
    for key, name, unit, _ in FIELD_META:
        v = input_data.get(key)
        if v is not None:
            vals.append(f"{name} {float(v):.1f} {unit}")
    vals_str = " | ".join(vals) if vals else "수치 미입력"

    comorbid = [label for k, label in COMORBID_LABELS.items()
                if input_data.get(k) in ("yes", True, "1", 1)]
    comorbid_str = ", ".join(comorbid) if comorbid else "없음"

    ctx_text = "\n\n".join(
        f"[참고자료 {i+1}] 출처: {c['source']}\n{c['content']}"
        for i, c in enumerate(contexts[:5])
    )

    clinical_q = query or f"{prediction} 단계 환자의 치료 계획"

    if prediction in _EARLY_STAGES:
        guideline_rule = (
            "아래 KDIGO 가이드라인 참고자료를 우선 근거로 활용하십시오.\n"
            "참고자료에 명시되지 않은 내용은 신장내과 표준 진료 지침을 보완하여 작성하십시오.\n"
            "단, 근거 없는 추측은 삼가고 구체적인 수치(목표 혈압, 약물 용량 기준, 검사 주기 등)를 반드시 포함하십시오.\n"
            "'가이드라인에 없다', '지침이 없다'는 표현은 절대 사용하지 마십시오.\n"
        )
        stage_focus = _EARLY_STAGE_FOCUS.get(prediction, "")
        stage_focus_block = f"\n[단계별 작성 방향]\n{stage_focus}\n" if stage_focus else ""
    else:
        guideline_rule = (
            "아래 KDIGO 가이드라인 참고자료만을 근거로 작성하십시오.\n"
            "추측이나 가이드라인에 없는 내용을 절대 작성하지 마십시오.\n"
        )
        stage_focus_block = ""

    return (
        "[지시사항]\n"
        "반드시 한국어로만 작성하십시오. 영어·외국어 절대 금지.\n"
        f"{guideline_rule}"
        f"{stage_focus_block}\n"
        "[환자 임상 정보]\n"
        f"CKD 단계: {meta[0]} ({meta[2]}, {meta[1]})\n"
        f"임상 수치: {vals_str}\n"
        f"동반 증상: {comorbid_str}\n"
        f"임상 질문: {clinical_q}\n\n"
        "[KDIGO 가이드라인 참고자료]\n"
        f"{ctx_text}\n\n"
        "[응답 형식]\n"
        f"{format_instructions}"
    )


# ── LLM 응답 파싱 (레거시 — LangChain 미사용 환경 호환) ────────────

_SECTION_PATTERNS = [
    ("sec2",  re.compile(r"2\s*[\.．]\s*위험도[^\n]*\n", re.IGNORECASE)),
    ("sec3",  re.compile(r"3\s*[\.．]\s*이상\s*소견[^\n]*\n", re.IGNORECASE)),
    ("sec41", re.compile(r"4[-‐]\s*1\s*[\.．]\s*약물[^\n]*\n", re.IGNORECASE)),
    ("sec42", re.compile(r"4[-‐]\s*2\s*[\.．]\s*생활[^\n]*\n", re.IGNORECASE)),
    ("sec43", re.compile(r"4[-‐]\s*3\s*[\.．]\s*추적[^\n]*\n", re.IGNORECASE)),
    ("sec5",  re.compile(r"5\s*[\.．]\s*종합[^\n]*\n?", re.IGNORECASE)),
]


def parse_llm_sections(raw: str) -> dict[str, str]:
    """LLM 출력에서 각 섹션 텍스트를 추출."""
    positions = []
    for name, pat in _SECTION_PATTERNS:
        m = pat.search(raw)
        if m:
            positions.append((m.start(), m.end(), name))

    positions.sort()

    result: dict[str, str] = {}
    for i, (start, end, name) in enumerate(positions):
        next_start = positions[i + 1][0] if i + 1 < len(positions) else len(raw)
        content = raw[end:next_start].strip()
        result[name] = content

    return result


# ── 폴백 섹션 (LLM 없을 때 규칙 기반) ────────────────────────────

_FALLBACK_RISK = {
    "Normal_Stage1": (
        "현재 신기능은 정상 범위이나 위험 요인(고혈압, 당뇨 등)이 존재하면 진행 위험이 있습니다.\n"
        "추정 원인: 유전적 소인, 초기 혈관 손상, 대사 이상 가능성."
    ),
    "Stage2": (
        "경미한 신기능 저하로 진행 위험이 낮으나 위험 요인 관리가 필요합니다.\n"
        "추정 원인: 고혈압성 신장 손상, 초기 당뇨 신증, 만성 신우신염 가능성."
    ),
    "Stage3": (
        "중등도 신기능 저하로 심혈관 합병증 및 진행 위험이 유의미합니다.\n"
        "추정 원인: 당뇨 신증, 고혈압성 신경화증, 사구체 신염 가능성."
    ),
    "Stage4": (
        "중증 신기능 저하로 투석 준비가 필요한 단계입니다.\n"
        "추정 원인: 진행된 당뇨 신증, 만성 고혈압성 신장 손상, 만성 사구체 신염 가능성."
    ),
    "Stage5": (
        "말기 신부전으로 즉각적인 신대체 요법이 필요합니다.\n"
        "추정 원인: 당뇨 신증, 고혈압성 신장 손상의 최종 단계 또는 급성 악화 가능성."
    ),
}

_FALLBACK_DRUG = {
    "Normal_Stage1": (
        "• 단백뇨 존재 시: ACE 억제제 또는 ARB 시작 고려\n"
        "• 고혈압 동반 시: 혈압 목표 130/80 mmHg 미만\n"
        "• 금기: NSAIDs 장기 복용 금지"
    ),
    "Stage2": (
        "• ACE 억제제 또는 ARB: 단백뇨 감소 및 신장 보호 목적으로 유지\n"
        "• 당뇨 동반 시: SGLT2 억제제 추가 고려 (eGFR ≥ 30 시)\n"
        "• 혈압 조절: 목표 130/80 mmHg 미만\n"
        "• 금기: 조영제 사용 전 사전 수화 필수, NSAIDs 금지"
    ),
    "Stage3": (
        "• ACE 억제제/ARB: 유지 (신장 보호 핵심 약물)\n"
        "• 당뇨 동반 시: SGLT2 억제제 유지, 메트포르민 용량 감량 검토\n"
        "• 인산염 상승 시: 인 결합제(탄산칼슘 등) 시작 고려\n"
        "• 빈혈(Hb < 10) 시: 조혈자극제(ESA) 시작 고려, 철분 보충 병행\n"
        "• 금기: NSAIDs 금지, 마그네슘 함유 제산제 주의\n"
        "• 용량 조절: eGFR에 따라 신독성 약물 용량 재검토 필요"
    ),
    "Stage4": (
        "• ACE 억제제/ARB: 유지 (고칼륨혈증 모니터링 필수)\n"
        "• 조혈자극제(ESA): 목표 Hb 10~11.5 g/dL 유지\n"
        "• 인 결합제: 적극적 사용 (세벨라머, 란타넘 탄산염 고려)\n"
        "• 활성 비타민 D(칼시트리올): PTH 조절 목적\n"
        "• 이뇨제: 부종 조절 (고용량 루프 이뇨제)\n"
        "• 중단 검토: 메트포르민, 일부 경구 혈당강하제\n"
        "• 금기: NSAIDs 절대 금지, 칼륨 보존 이뇨제 주의"
    ),
    "Stage5": (
        "• 투석 시작 후 약물 재조정 필수\n"
        "• 조혈자극제(ESA): 지속 (투석 환자 Hb 목표 10~11.5 g/dL)\n"
        "• 인 결합제: 지속적 사용\n"
        "• 혈압약: 투석 전후 혈압 변동에 따른 조절\n"
        "• 중단: 신장 배설 의존 약물 대부분 재검토\n"
        "• 금기: 신독성 약물 절대 금지, 고칼륨 식품·약물 금지"
    ),
}

_FALLBACK_LIFESTYLE = {
    "Normal_Stage1": (
        "• 저염식: 나트륨 2,300 mg/일 이하\n"
        "• 규칙적 유산소 운동: 주 5회, 30분 이상\n"
        "• 금연, 절주\n"
        "• 적정 체중 유지 (BMI 18.5~24.9)"
    ),
    "Stage2": (
        "• 저염식: 나트륨 2,000 mg/일 이하\n"
        "• 단백질: 0.8 g/kg/일 이하 권장\n"
        "• 규칙적 운동: 신장 건강에 적합한 강도로 유지\n"
        "• 금연 필수, 음주 제한"
    ),
    "Stage3": (
        "• 단백질 제한: 0.6~0.8 g/kg/일\n"
        "• 칼륨 제한: 칼륨 풍부 식품(바나나, 오렌지, 토마토) 제한\n"
        "• 인 제한: 유제품, 견과류, 가공식품 제한\n"
        "• 저염식: 나트륨 2,000 mg/일 이하\n"
        "• 수분 섭취: 부종 없을 시 정상 유지\n"
        "• 운동: 심혈관 적합 운동 (걷기, 수영)"
    ),
    "Stage4": (
        "• 단백질 엄격 제한: 0.6 g/kg/일\n"
        "• 칼륨 엄격 제한: 2,000 mg/일 이하\n"
        "• 인 엄격 제한: 식이 인 흡수 억제\n"
        "• 수분 제한: 부종·소변량에 따라 1,000~1,500 mL/일\n"
        "• 저염식: 나트륨 1,500 mg/일 이하\n"
        "• 투석 전 체력 유지를 위한 가벼운 운동 권장"
    ),
    "Stage5": (
        "• 투석 식이 지침 철저 준수\n"
        "• 수분 제한: 투석 간격에 따라 500~1,000 mL/일\n"
        "• 칼륨·인·나트륨 엄격 제한\n"
        "• 단백질: 투석 중 손실 보충을 위해 1.2 g/kg/일 이상 권장\n"
        "• 신장 재활(Renal Rehabilitation) 프로그램 참여 권장"
    ),
}

_FALLBACK_FOLLOWUP = {
    "Normal_Stage1": (
        "• eGFR, 단백뇨, 혈압: 연 1회\n"
        "• 전해질(칼륨, 나트륨, 칼슘, 인): 연 1회\n"
        "• 혈당(당뇨 동반 시): 3개월마다"
    ),
    "Stage2": (
        "• eGFR, 단백뇨, 혈압: 6개월마다\n"
        "• 전해질: 6개월마다\n"
        "• 혈당(당뇨 동반 시): 3개월마다"
    ),
    "Stage3": (
        "• eGFR, 크레아티닌, BUN: 3개월마다\n"
        "• 칼륨, 나트륨, 칼슘, 인: 3개월마다\n"
        "• 헤모글로빈(빈혈 평가): 3개월마다\n"
        "• PTH, 비타민 D: 6개월마다\n"
        "• 단백뇨(소변 알부민/크레아티닌 비): 3개월마다"
    ),
    "Stage4": (
        "• eGFR, 크레아티닌, BUN: 1~3개월마다\n"
        "• 전해질(칼륨, 칼슘, 인): 1~3개월마다\n"
        "• 헤모글로빈: 1개월마다\n"
        "• PTH, 비타민 D: 3개월마다\n"
        "• 투석 접근로 평가: 즉시 시작\n"
        "• 신장이식 상담: 해당 시 진행"
    ),
    "Stage5": (
        "• 투석 적절도(Kt/V) 평가: 월 1회\n"
        "• 전해질, 헤모글로빈: 월 1회\n"
        "• PTH, 칼슘, 인: 3개월마다\n"
        "• 심혈관 평가(심초음파): 연 1회\n"
        "• 투석 접근로 기능 평가: 정기적"
    ),
}


def _build_comprehensive_fallback(
    prediction: str,
    confidence: float,
    input_data: dict,
    contexts: list,
) -> str:
    """수치 기반 자연어 종합 소견 단락 생성 (LLM 폴백)."""
    meta = STAGE_META.get(prediction, ("알 수 없음", "—", "—", "—"))
    stage_label, egfr_range, desc, risk = meta

    # 기본 문장
    lines = [
        f"본 환자는 AI 진단 모델(신뢰도 {confidence * 100:.1f}%)에 의해 "
        f"만성 신장질환(CKD) {stage_label}로 진단되었으며, "
        f"{desc} 상태에 해당합니다({egfr_range})."
    ]

    # 수치별 소견 문장
    egfr = input_data.get("egfr")
    sc   = input_data.get("sc")
    bu   = input_data.get("bu")
    pot  = input_data.get("pot")
    bp   = input_data.get("bp")
    hemo = input_data.get("hemo")

    if egfr is not None:
        lines.append(
            f"신사구체여과율(eGFR)은 {float(egfr):.1f} mL/min으로 "
            + ("정상 범위에 있으나 지속적인 모니터링이 필요합니다." if float(egfr) >= 60
               else "중등도 이상의 신기능 저하를 시사하며 정기 추적이 권고됩니다." if float(egfr) >= 30
               else "중증 신기능 저하 수준으로 투석 준비를 포함한 적극적 관리가 필요합니다.")
        )

    if sc is not None:
        sc_f = float(sc)
        if sc_f > 4:
            lines.append(f"혈중 크레아티닌은 {sc_f:.1f} mg/dL로 중증 상승 소견을 보이며 즉각적인 신장내과 평가가 필요합니다.")
        elif sc_f > 1.2:
            lines.append(f"혈중 크레아티닌은 {sc_f:.1f} mg/dL로 정상 상한을 초과하여 신기능 저하를 반영합니다.")

    if bu is not None:
        bu_f = float(bu)
        if bu_f > 50:
            lines.append(f"혈중 요소 질소(BUN) {bu_f:.1f} mg/dL는 단백질 대사 부산물 축적을 나타내며, 신장 내 여과 기능이 현저히 저하된 상태임을 시사합니다.")

    if pot is not None:
        pot_f = float(pot)
        if pot_f >= 5.5:
            lines.append(f"칼륨 농도 {pot_f:.1f} mEq/L는 고칼륨혈증 범위로, 심장 부정맥 위험이 높아 즉각적인 전해질 교정이 필요합니다.")
        elif pot_f < 3.5:
            lines.append(f"칼륨 농도 {pot_f:.1f} mEq/L는 저칼륨혈증 범위로, 근육 약화 및 부정맥 예방을 위한 보충이 필요합니다.")

    if bp is not None:
        bp_f = float(bp)
        if bp_f >= 180:
            lines.append(f"수축기 혈압 {bp_f:.0f} mmHg는 고혈압 위기 수준으로 즉각적인 강압 치료가 요구됩니다.")
        elif bp_f >= 140:
            lines.append(f"수축기 혈압 {bp_f:.0f} mmHg는 목표 혈압(130 mmHg 미만)을 초과하여 신기능 악화를 가속화할 수 있으므로 적극적 혈압 조절이 필요합니다.")

    if hemo is not None:
        hemo_f = float(hemo)
        if hemo_f < 8:
            lines.append(f"헤모글로빈 {hemo_f:.1f} g/dL는 중증 빈혈에 해당하며, 수혈 또는 조혈자극제 투여를 즉시 고려하여야 합니다.")
        elif hemo_f < 10:
            lines.append(f"헤모글로빈 {hemo_f:.1f} g/dL는 신성 빈혈 범위로, 조혈자극제(ESA) 및 철분 보충 치료 계획이 필요합니다.")

    # 동반 질환
    comorbid = [label for k, label in COMORBID_LABELS.items()
                if input_data.get(k) in ("yes", True, "1", 1)]
    if comorbid:
        lines.append(
            f"동반 질환으로 {', '.join(comorbid)}이(가) 확인되었으며, "
            "이는 신기능 저하의 진행을 가속화하는 주요 위험 요인으로 반드시 병행 관리가 필요합니다."
        )

    # 단계별 종합 처치 방향
    treatment_map = {
        "Normal_Stage1": (
            "현재 신기능이 정상 범위이므로 정기 추적과 위험 요인(혈압·혈당·단백뇨) 조절을 통해 "
            "만성 신장질환으로의 진행을 예방하는 데 치료 목표를 두어야 합니다."
        ),
        "Stage2": (
            "ACE 억제제 또는 ARB를 통한 신장 보호 치료를 지속하고, "
            "6개월 주기의 정기 검사를 통해 진행 여부를 면밀히 감시하는 것이 권고됩니다."
        ),
        "Stage3": (
            "중등도 신기능 저하 단계로 약물 치료와 함께 단백질·칼륨·인 식이 제한이 필수적이며, "
            "3개월마다 정밀 추적 검사를 시행하여 합병증(빈혈, 대사성 산증, 골질환)을 조기 발견해야 합니다."
        ),
        "Stage4": (
            "중증 신기능 저하로 신대체 요법(투석 또는 신장이식)을 위한 준비 단계에 있습니다. "
            "투석 접근로 조성을 포함한 신대체 요법 계획을 수립하고, "
            "신장내과 전문의와의 긴밀한 협진이 반드시 필요합니다."
        ),
        "Stage5": (
            "말기 신부전(ESRD) 단계로 생명 유지를 위한 신대체 요법(혈액투석, 복막투석, 또는 신장이식)이 "
            "즉각적으로 시작되어야 하며, 종합적인 다학제 접근을 통한 환자 관리가 요구됩니다."
        ),
    }
    lines.append(treatment_map.get(prediction, "담당 신장내과 전문의의 종합적 판단에 따른 치료 계획이 필요합니다."))

    return " ".join(lines)


def build_fallback_sections(
    prediction: str,
    contexts: list,
    confidence: float = 0.0,
    input_data: dict | None = None,
) -> dict[str, str]:
    """LLM 없이 규칙 기반으로 섹션 2~5 생성 (폴백)."""
    if input_data is None:
        input_data = {}

    # KDIGO 발췌를 섹션 3에 추가
    relevant = [c for c in contexts if float(c.get("score", 0)) >= 0.4]
    excerpt = ""
    if relevant:
        excerpt = "\n\n  [KDIGO 가이드라인 발췌]\n" + "\n".join(
            f"  • {c['content'][:150].strip()}" for c in relevant[:3]
        )

    return {
        "sec2":  _FALLBACK_RISK.get(prediction, "위험도 평가를 위한 충분한 정보가 없습니다."),
        "sec3":  "임상 수치에 기반한 소견은 위 핵심 수치 요약을 참고하십시오." + excerpt,
        "sec41": _FALLBACK_DRUG.get(prediction, "담당 의사와 상의하여 결정하십시오."),
        "sec42": _FALLBACK_LIFESTYLE.get(prediction, "담당 의사와 상의하여 결정하십시오."),
        "sec43": _FALLBACK_FOLLOWUP.get(prediction, "담당 의사와 상의하여 결정하십시오."),
        "sec5":  _build_comprehensive_fallback(prediction, confidence, input_data, contexts),
    }


# ── 최종 소견서 조립 ──────────────────────────────────────────────

def assemble_report(
    section1: str,
    sections: dict[str, str],
    doctor_name: str = "",
    department: str = "신장내과",
) -> str:
    """모든 섹션을 합쳐 최종 소견서 문자열을 반환."""

    def _sec(content: str) -> str:
        """섹션 내용을 들여쓰기 처리."""
        lines = content.strip().splitlines()
        return "\n".join(f"  {l}" if l.strip() else "" for l in lines)

    dept_str = f"담당과: {department}" + (f"  담당의: {doctor_name}" if doctor_name else "")

    report = "\n".join([
        DIV,
        f"  진 단 소 견 서",
        f"  {dept_str}",
        DIV,
        "",
        "1. 핵심 수치 요약 및 CKD 단계 진단",
        "",
        _sec(section1),
        "",
        DIV,
        "",
        "2. 위험도 평가 및 원인 추정",
        "",
        _sec(sections.get("sec2", "—")),
        "",
        DIV,
        "",
        "3. 이상 소견 해석",
        "",
        _sec(sections.get("sec3", "—")),
        "",
        DIV,
        "",
        "4. 치료 권고사항",
        "",
        "  4-1. 약물 처방",
        "",
        _sec(sections.get("sec41", "—")),
        "",
        "  4-2. 생활 습관 및 비약물 치료",
        "",
        _sec(sections.get("sec42", "—")),
        "",
        "  4-3. 추적 검사 계획",
        "",
        _sec(sections.get("sec43", "—")),
        "",
        DIV,
        "",
        "5. 종합 진단 소견",
        "",
        _sec(sections.get("sec5", "—")),
        "",
        DIV,
        "  ※ 본 소견서는 AI 보조 의견이며 최종 진단과 처방은 담당의가 결정합니다.",
        DIV,
    ])

    return report
