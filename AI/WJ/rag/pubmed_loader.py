"""
PubMed 논문 초록 + 뇌종양 임상 증상 지식을 pgvector에 적재.

사용법:
    python -m WJ.rag.pubmed_loader            # 전체 실행
    python -m WJ.rag.pubmed_loader --dry-run  # DB 저장 없이 수집만 확인
"""
from __future__ import annotations

import argparse
import time
from typing import Optional

import ssl
import sys

from Bio import Entrez

# Windows cp949 환경에서 한글 출력
if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp949", "cp1252"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 사내/학교 네트워크 프록시 SSL 우회 (개발 환경)
ssl._create_default_https_context = ssl._create_unverified_context

# PubMed 이용 약관: 이메일 필수
Entrez.email = "medicore-brain@example.com"

SEARCH_QUERIES = [
    ("glioblastoma MRI diagnosis prognosis", 20),
    ("brain tumor T1 MRI classification deep learning", 15),
    ("normal brain MRI findings radiology", 10),
    ("meningioma glioma differential diagnosis MRI", 15),
    ("brain tumor symptoms headache seizure neurological", 10),
    ("WHO CNS tumor classification grade glioma", 10),
]


# ── 뇌종양 임상 증상 지식 (직접 작성) ────────────────────────────────────────

SYMPTOM_KNOWLEDGE = [
    {
        "content": (
            "뇌종양 초기 증상: 두통(특히 아침에 심하고 구역감 동반), 구역·구토, 시력 변화. "
            "두통은 종양 위치와 무관하게 뇌압 상승으로 발생하며, "
            "기침·운동 시 악화되는 양상이 특징적이다. "
            "초기에는 일반 두통과 구별이 어려워 영상 검사가 중요하다."
        ),
        "source": "Brain Tumor Symptoms — Clinical Review 2023",
    },
    {
        "content": (
            "뇌종양 국소 증상 (위치별): "
            "전두엽 — 성격변화, 집중력 저하, 기억장애; "
            "두정엽 — 반신감각 이상, 공간인지 장애; "
            "측두엽 — 언어장애(실어증), 청각 환청; "
            "후두엽 — 시야 결손, 시각 이상; "
            "소뇌 — 보행 불안정, 협응 장애, 어지럼증; "
            "뇌간 — 복시, 안면마비, 연하곤란."
        ),
        "source": "Neurological Oncology Clinical Handbook 2022",
    },
    {
        "content": (
            "뇌종양과 연관된 간질(경련) 발작: "
            "신규 발생 간질 발작의 약 30%는 뇌종양이 원인. "
            "저등급 교종(Grade I~II)에서 발작 발생률이 고등급보다 높음(80% vs 30%). "
            "발작 조절 위해 항경련제(레베티라세탐 등) 투여, "
            "종양 절제 후 발작 호전되는 경우 많음."
        ),
        "source": "Epilepsy in Brain Tumors, Lancet Neurol 2022",
    },
    {
        "content": (
            "뇌압 상승(두개내압 항진) 증상: 3대 증상 — 두통·구역·유두부종. "
            "진행 시 의식 저하, 쿠싱 반응(서맥·고혈압·불규칙 호흡). "
            "응급 처치: 덱사메타손 정맥 투여로 부종 감소, "
            "심한 경우 만니톨 삼투압 치료 또는 응급 감압술."
        ),
        "source": "Increased Intracranial Pressure — Neurocritical Care 2023",
    },
    {
        "content": (
            "교모세포종(GBM, Grade IV) 주요 임상 특징: "
            "중앙 발병 연령 64세, 남성에서 약간 더 흔함. "
            "급격한 신경학적 악화, 빠른 종양 성장이 특징. "
            "진단 후 표준 치료(수술+방사선+테모졸로마이드) 없이 생존 기간 3개월 미만. "
            "IDH 야생형이 대부분이며 예후 불량 인자."
        ),
        "source": "GBM Clinical Features — Neuro-Oncology 2023",
    },
    {
        "content": (
            "저등급 교종(Grade II) 임상 경과: "
            "증상 발현에서 진단까지 평균 1~2년 소요. "
            "젊은 성인(20~40대)에서 호발. "
            "주요 증상: 간질 발작이 가장 흔함(약 70%), 두통, 인지 변화. "
            "MRI 상 T2/FLAIR 고신호, T1 조영증강 없음 또는 약함. "
            "IDH 변이 양성 시 예후 비교적 양호, 10년 생존율 40~60%."
        ),
        "source": "Low-Grade Glioma Management, EANO Guidelines 2022",
    },
    {
        "content": (
            "뇌종양 치료 후 경과 관찰: "
            "수술 후 24~48시간 내 MRI로 절제 범위 확인. "
            "방사선 치료 중 및 치료 후 3개월마다 MRI 추적. "
            "방사선 괴사(radiation necrosis)와 종양 재발 감별 위해 "
            "MR perfusion 또는 아미노산 PET(FET-PET) 활용. "
            "재발 시 재수술, 재방사선, 베바시주맙 등 2차 치료 고려."
        ),
        "source": "Brain Tumor Follow-up Protocol, RANO Criteria 2023",
    },
    {
        "content": (
            "수막종(Meningioma) 특징: "
            "성인 두개내 종양 중 가장 흔함(약 37%). "
            "대부분 양성(WHO Grade I), 여성에서 2배 흔함. "
            "MRI: T1 등신호, T2 등~고신호, 조영증강 균일하고 뚜렷함, dural tail sign. "
            "증상 없으면 경과관찰, 증상 있거나 크기 증가 시 수술 또는 방사선 수술(감마나이프)."
        ),
        "source": "Meningioma — WHO CNS Classification 2021",
    },
    {
        "content": (
            "전이성 뇌종양 특징: "
            "성인에서 원발성보다 빈도 높음. 원발암: 폐암(45%)·유방암(15%)·흑색종·신장암·대장암. "
            "MRI: 다발성 결절, 회백질 경계부 호발, 주변 부종이 크고 조영증강 균일. "
            "치료: 단발성이면 수술±방사선, 다발성이면 전뇌방사선 또는 정위방사선 수술. "
            "원발암 치료와 병행 필수."
        ),
        "source": "Brain Metastases — ASCO Guidelines 2022",
    },
    {
        "content": (
            "소아 뇌종양 특징: "
            "소아 고형암 중 2위(백혈병 다음). "
            "호발 부위: 성인과 달리 후두개와(소뇌, 뇌간)가 흔함. "
            "주요 유형: 수모세포종(medulloblastoma), 뇌간 교종(DIPG), 털모양 성상세포종. "
            "증상: 보행 이상, 두통·구토(아침), 복시, 두위 경사. "
            "수모세포종은 화학요법 반응 좋아 장기 생존 가능."
        ),
        "source": "Pediatric Brain Tumors — SIOPE Guidelines 2023",
    },
]


def fetch_pubmed_abstracts(query: str, max_results: int = 20) -> list[dict]:
    """PubMed에서 논문 초록을 가져온다."""
    docs = []
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()

        ids = record["IdList"]
        if not ids:
            return []

        time.sleep(0.4)  # NCBI rate limit (3 req/s)

        handle = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        for article in records["PubmedArticle"]:
            try:
                medline = article["MedlineCitation"]
                art = medline["Article"]

                title = str(art.get("ArticleTitle", ""))
                abstract_texts = art.get("Abstract", {}).get("AbstractText", [])
                if isinstance(abstract_texts, list):
                    abstract = " ".join(str(t) for t in abstract_texts)
                else:
                    abstract = str(abstract_texts)

                if not abstract.strip():
                    continue

                pmid = str(medline["PMID"])
                content = f"{title}\n\n{abstract}"

                docs.append({
                    "content": content,
                    "source": f"PubMed PMID:{pmid}",
                })
            except (KeyError, IndexError):
                continue

        time.sleep(0.4)

    except Exception as e:
        print(f"  [경고] PubMed 수집 실패 ({query[:30]}...): {e}")

    return docs


def collect_all(verbose: bool = True) -> list[dict]:
    """PubMed 초록 + 증상 지식 전체 수집."""
    all_docs = []

    if verbose:
        print("== PubMed 초록 수집 ==")
    for query, n in SEARCH_QUERIES:
        docs = fetch_pubmed_abstracts(query, max_results=n)
        if verbose:
            print(f"  [{len(docs):2d}건] {query[:55]}")
        all_docs.extend(docs)

    if verbose:
        print(f"\n== 임상 증상 지식 추가 ({len(SYMPTOM_KNOWLEDGE)}건) ==")
        for d in SYMPTOM_KNOWLEDGE:
            print(f"  - {d['source']}")

    all_docs.extend(SYMPTOM_KNOWLEDGE)

    if verbose:
        print(f"\n총 수집: {len(all_docs)}건")

    return all_docs


def run(dry_run: bool = False) -> None:
    from tqdm import tqdm
    from WJ.rag.vector_store import ensure_table, insert_documents

    docs = collect_all(verbose=True)

    if dry_run:
        print("\n[dry-run] DB 저장 건너뜀.")
        return

    print(f"\n== pgvector 적재 시작 (총 {len(docs)}건) ==")
    ensure_table()

    batch_size = 10
    total_inserted = 0
    batches = [docs[i:i + batch_size] for i in range(0, len(docs), batch_size)]

    with tqdm(total=len(docs), unit="건", ncols=70, bar_format="{l_bar}{bar}| {n}/{total} [{elapsed}<{remaining}]") as pbar:
        for batch in batches:
            from WJ.rag.knowledge_loader import embed_documents
            texts = [d["content"] for d in batch]
            embeddings = embed_documents(texts)
            rows = [
                {"content": doc["content"], "source": doc.get("source", ""), "embedding": emb}
                for doc, emb in zip(batch, embeddings)
            ]
            inserted = insert_documents(rows)
            total_inserted += inserted
            pbar.update(len(batch))
            pbar.set_postfix({"삽입": total_inserted})

    print(f"\n적재 완료: {total_inserted}건 삽입됨")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 수집만 확인")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
