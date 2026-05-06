"""
피부 질환 의학 지식 DB 삽입 스크립트 (1회만 실행)

실행 방법:
    cd D:\MEDI-Zero\AI
    venv\Scripts\python -m MS.seed_knowledge

Gemini Flash로 15개 질환 × 4주제 = 60개 청크 자동 생성 후
gemini-embedding-001 RETRIEVAL_DOCUMENT로 벡터화 → medical_knowledge 삽입
"""

import io
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import vertexai
from vertexai.generative_models import GenerativeModel

from MS.rag_engine import insert_knowledge

# ── Vertex AI 초기화 ───────────────────────────────────
GCP_PROJECT  = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "asia-northeast3")
GCP_KEY      = os.getenv("GCP_KEY_PATH")

if not GCP_PROJECT:
    raise RuntimeError(".env에 GCP_PROJECT_ID가 없습니다.")
if GCP_KEY:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY

vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
llm = GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash-001"))

DISEASES = [
    "광선각화증 (Actinic Keratosis)",
    "기저세포암 (Basal Cell Carcinoma)",
    "멜라닌세포모반 (Melanocytic Nevus)",
    "보웬병 (Bowen's Disease)",
    "비립종 (Milia)",
    "사마귀 (Wart, HPV)",
    "악성흑색종 (Malignant Melanoma)",
    "지루각화증 (Seborrheic Keratosis)",
    "편평세포암 (Squamous Cell Carcinoma)",
    "표피낭종 (Epidermal Cyst)",
    "피부섬유종 (Dermatofibroma)",
    "피지샘증식증 (Sebaceous Hyperplasia)",
    "혈관종 (Hemangioma)",
    "화농 육아종 (Pyogenic Granuloma)",
    "흑색점 (Lentigo)",
]

TOPICS = [
    ("임상특징", "피부과 전문의 수준의 임상 특징, 육안 소견, ABCDE 기준(해당 시) 200자 이내로 서술"),
    ("진단기준", "진단 기준, 감별 진단이 필요한 유사 질환, 조직검사 소견 200자 이내로 서술"),
    ("치료가이드라인", "NCCN/AAD/BAD 가이드라인 기반 표준 치료 방법, 단계별 처치 200자 이내로 서술"),
    ("예후및추적관찰", "재발률, 악성화 위험도, 추적관찰 주기, 환자 교육 사항 200자 이내로 서술"),
]

PROMPT_TEMPLATE = """당신은 피부과 전문의입니다.
피부 질환 '{disease}'에 대해 '{topic}' 항목을 아래 지침에 따라 작성하세요.

지침: {instruction}

- 의학적으로 정확하고 간결하게 작성하세요.
- 출처 표기 없이 본문만 작성하세요.
- 한국어로 작성하세요."""


def generate_chunk(disease: str, topic: str, instruction: str) -> str:
    prompt = PROMPT_TEMPLATE.format(
        disease=disease, topic=topic, instruction=instruction
    )
    response = llm.generate_content(prompt)
    return response.text.strip()


def main():
    total   = len(DISEASES) * len(TOPICS)
    success = 0
    failed  = 0

    print(f"=== 피부 질환 지식 DB 삽입 시작 ===")
    print(f"대상: {len(DISEASES)}개 질환 × {len(TOPICS)}개 주제 = {total}개 청크\n")

    for i, disease in enumerate(DISEASES, 1):
        for topic, instruction in TOPICS:
            label = f"[{i:02d}/{len(DISEASES)}] {disease} — {topic}"
            try:
                print(f"생성 중: {label}")
                content = generate_chunk(disease, topic, instruction)
                source  = f"Gemini 생성 ({topic}) — {disease}"

                ok = insert_knowledge(content, source)
                if ok:
                    success += 1
                    print(f"  ✅ 삽입 완료 ({len(content)}자)")
                else:
                    failed += 1
                    print(f"  ❌ 삽입 실패")

                time.sleep(1)  # Vertex AI API rate limit 방지

            except Exception as e:
                failed += 1
                print(f"  ❌ 오류: {e}")
                time.sleep(2)

    print(f"\n=== 완료 ===")
    print(f"성공: {success} / 실패: {failed} / 전체: {total}")
    if failed == 0:
        print("✅ 모든 지식이 medical_knowledge에 삽입됐습니다.")
    else:
        print("⚠️  일부 실패. 위 로그를 확인 후 재실행하세요.")


if __name__ == "__main__":
    main()