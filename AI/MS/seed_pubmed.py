"""
PubMed 논문 + Gemini 임상 요약 기반 의학 지식 DB 삽입 스크립트 (1회만 실행)

실행 방법:
    cd D:\MEDI-Zero\AI
    venv\Scripts\python -m MS.seed_pubmed

동작:
    1. 15개 피부질환 × 3개 토픽 → PubMed에서 논문 abstract 수집
    2. Gemini Flash로 한국어 임상 요약 생성 (근거 수준 명시)
    3. gemini-embedding-001 RETRIEVAL_DOCUMENT로 벡터화
    4. medical_knowledge 테이블에 module_tag='skin', PMID 출처 포함 삽입

seed_knowledge.py(Gemini 합성 지식)와 함께 실행하면 RAG 품질이 극대화됩니다.
"""

import io
import json
import os
import ssl
import sys
import time
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
from pathlib import Path

# Windows cp949 터미널 한글/특수문자 깨짐 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 사내 프록시 환경 SSL 인증서 검증 우회
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import vertexai
from vertexai.generative_models import GenerativeModel

from MS.rag_engine import insert_knowledge

# ── Vertex AI 초기화 ──────────────────────────────────────────────────
GCP_PROJECT  = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "asia-northeast3")
GCP_KEY      = os.getenv("GCP_KEY_PATH")

if not GCP_PROJECT:
    raise RuntimeError(".env에 GCP_PROJECT_ID가 없습니다.")
if GCP_KEY:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY

vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
llm = GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

# ── 대상 질환 목록 ────────────────────────────────────────────────────
DISEASES = [
    ("광선각화증",   "Actinic Keratosis"),
    ("기저세포암",   "Basal Cell Carcinoma"),
    ("멜라닌세포모반", "Melanocytic Nevus"),
    ("보웬병",      "Bowen's Disease"),
    ("비립종",      "Milia"),
    ("사마귀",      "Wart HPV skin"),
    ("악성흑색종",   "Malignant Melanoma skin"),
    ("지루각화증",   "Seborrheic Keratosis"),
    ("편평세포암",   "Squamous Cell Carcinoma skin"),
    ("표피낭종",    "Epidermal Cyst skin"),
    ("피부섬유종",   "Dermatofibroma"),
    ("피지샘증식증", "Sebaceous Hyperplasia"),
    ("혈관종",      "Hemangioma skin"),
    ("화농 육아종",  "Pyogenic Granuloma"),
    ("흑색점",      "Lentigo skin"),
]

# 토픽별 PubMed 검색 키워드
SEARCH_TOPICS = [
    ("진단",   "diagnosis dermoscopy clinical features"),
    ("치료",   "treatment guidelines therapy"),
    ("예후",   "prognosis recurrence follow-up outcomes"),
]

MAX_PAPERS_PER_QUERY = 3   # 토픽당 최대 논문 수
NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


# ── PubMed API ────────────────────────────────────────────────────────
def pubmed_search(disease_en: str, topic_keywords: str) -> list[str]:
    query = f'"{disease_en}"[Title/Abstract] AND ({topic_keywords})[Title/Abstract]'
    params = urllib.parse.urlencode({
        "db":      "pubmed",
        "term":    query,
        "retmax":  MAX_PAPERS_PER_QUERY,
        "retmode": "json",
        "sort":    "relevance",
    })
    try:
        with urllib.request.urlopen(f"{NCBI_BASE}/esearch.fcgi?{params}", timeout=10, context=_SSL_CTX) as r:
            data = json.loads(r.read())
            return data["esearchresult"]["idlist"]
    except Exception as e:
        print(f"    PubMed 검색 오류: {e}")
        return []


def pubmed_fetch(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    params = urllib.parse.urlencode({
        "db":      "pubmed",
        "id":      ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    })
    try:
        with urllib.request.urlopen(f"{NCBI_BASE}/efetch.fcgi?{params}", timeout=15, context=_SSL_CTX) as r:
            return _parse_pubmed_xml(r.read())
    except Exception as e:
        print(f"    PubMed fetch 오류: {e}")
        return []


def _parse_pubmed_xml(xml_data: bytes) -> list[dict]:
    results = []
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return results

    for article in root.findall(".//PubmedArticle"):
        try:
            pmid     = article.findtext(".//PMID", "")
            title    = article.findtext(".//ArticleTitle", "").strip()
            abstract = " ".join(
                t.text for t in article.findall(".//AbstractText") if t.text
            ).strip()

            if not pmid or not abstract:
                continue

            # 저자 (최대 3명 + et al.)
            authors = article.findall(".//Author")
            names = []
            for a in authors[:3]:
                ln = a.findtext("LastName", "")
                fn = a.findtext("ForeName", "")
                if ln:
                    names.append(f"{ln} {fn[:1]}".strip() if fn else ln)
            author_str = ", ".join(names)
            if len(authors) > 3:
                author_str += " et al."

            journal = (
                article.findtext(".//Journal/ISOAbbreviation")
                or article.findtext(".//Journal/Title", "")
            ).strip()

            year = (
                article.findtext(".//PubDate/Year")
                or (article.findtext(".//PubDate/MedlineDate") or "")[:4]
            )

            results.append({
                "pmid":     pmid,
                "title":    title,
                "abstract": abstract,
                "authors":  author_str,
                "journal":  journal,
                "year":     year,
            })
        except Exception:
            continue

    return results


# ── Gemini 임상 요약 ──────────────────────────────────────────────────
SUMMARIZE_PROMPT = """당신은 피부과 전문의입니다.
아래 PubMed 논문을 읽고 임상에서 바로 활용할 수 있는 핵심 정보를 한국어로 요약하세요.

질환명: {disease_ko}
논문 제목: {title}
Abstract: {abstract}

요약 지침:
- 첫 문장에 근거 수준을 명시하세요 (예: [RCT] / [코호트 연구] / [체계적 문헌고찰] / [증례 보고] 등)
- 진단 기준, 치료 방법, 예후 등 임상적으로 중요한 내용 위주로 작성
- 수치 데이터(민감도, 특이도, 생존율 등)가 있으면 반드시 포함
- 200자 이내 한국어로 간결하게 작성
- 출처 표기 없이 본문만 작성"""


def gemini_summarize(disease_ko: str, title: str, abstract: str) -> str:
    prompt = SUMMARIZE_PROMPT.format(
        disease_ko=disease_ko, title=title, abstract=abstract
    )
    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"    Gemini 요약 오류: {e}")
        return abstract[:300]


def _format_citation(paper: dict) -> str:
    return (
        f"{paper['authors']} ({paper['year']}). "
        f"{paper['title']}. "
        f"{paper['journal']}. "
        f"PMID: {paper['pmid']}"
    )


# ── 메인 ──────────────────────────────────────────────────────────────
def main():
    total_diseases = len(DISEASES)
    total_topics   = len(SEARCH_TOPICS)
    print("=== PubMed + Gemini 의학 지식 DB 삽입 시작 ===")
    print(f"대상: {total_diseases}개 질환 × {total_topics}개 토픽 × 최대 {MAX_PAPERS_PER_QUERY}편")
    print(f"최대 {total_diseases * total_topics * MAX_PAPERS_PER_QUERY}개 청크 삽입 예정\n")

    success  = 0
    failed   = 0
    skipped  = 0
    seen_pmids: set[str] = set()

    for i, (disease_ko, disease_en) in enumerate(DISEASES, 1):
        print(f"\n[{i:02d}/{total_diseases}] {disease_ko} ({disease_en})")

        for topic_ko, topic_keywords in SEARCH_TOPICS:
            print(f"  ▶ 토픽: {topic_ko}")

            pmids = pubmed_search(disease_en, topic_keywords)
            time.sleep(0.4)  # NCBI rate limit (초당 3회 이하)

            papers = pubmed_fetch(pmids)
            time.sleep(0.4)

            if not papers:
                print(f"    논문 없음 — 스킵")
                continue

            for paper in papers:
                if paper["pmid"] in seen_pmids:
                    skipped += 1
                    print(f"    PMID {paper['pmid']} — 중복 스킵")
                    continue
                seen_pmids.add(paper["pmid"])

                print(f"    PMID {paper['pmid']} — {paper['title'][:55]}...")

                summary  = gemini_summarize(disease_ko, paper["title"], paper["abstract"])
                citation = _format_citation(paper)
                content  = f"[{disease_ko}] {summary}"

                ok = insert_knowledge(content, citation)
                if ok:
                    success += 1
                    print(f"    ✅ 삽입 완료 ({len(content)}자)")
                else:
                    failed += 1
                    print(f"    ❌ 삽입 실패")

                time.sleep(1.5)  # Vertex AI API rate limit

    print(f"\n{'='*40}")
    print(f"완료 — 성공: {success} / 실패: {failed} / 중복 스킵: {skipped}")
    if failed == 0:
        print("✅ 모든 논문 지식이 medical_knowledge에 삽입됐습니다.")
    else:
        print("⚠️  일부 실패. 위 로그 확인 후 재실행하세요.")


if __name__ == "__main__":
    main()
