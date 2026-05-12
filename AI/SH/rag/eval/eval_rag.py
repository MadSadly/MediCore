"""
AI/SH/rag/eval/eval_rag.py
안과 CDSS — Hybrid RAG + Graph RAG 통합 평가 스크립트

실행 방법:
  # DB 연결 전 (Mock 모드)
  python -m SH.rag.eval.eval_rag

  # DB 연결 후 (실제 모드) — chunk_and_embed + build_knowledge_graph 완료 후
  USE_REAL_RETRIEVER=1 python -m SH.rag.eval.eval_rag

평가 지표:
  [Hybrid RAG]
  - Hit Rate@3      : 상위 3개 중 관련 문서 1개 이상 포함 여부
  - Precision@3     : 상위 3개 중 관련 문서 비율
  - MRR             : 첫 번째 관련 문서 순위의 역수 평균
  - Disease Match@3 : 반환 문서 source 태그가 질환과 일치하는 비율

  [Graph RAG]
  - Seed Node Hit   : 질환명 → 시드 노드 발견율
  - BFS Reach Count : graph_rag.MAX_BFS_DEPTH BFS 도달 노드 수
  - Rerank Delta    : Graph 전후 상위 문서 순위 변화
  - Multi-hop Hit   : 복합 질환 케이스에서 연결 추론 성공 여부

담당: 홍승현 (SH) / module: eyes
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

# 프로젝트 루트 .env 로드
_ROOT = Path(__file__).resolve().parents[4]
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

USE_REAL = os.getenv("USE_REAL_RETRIEVER", "0").strip() == "1"

# ── 실제 / Mock 검색기 선택 ───────────────────────────────────

if USE_REAL:
    try:
        from SH.rag.retriever import hybrid_retriever
        from SH.rag.graph_rag import (
            graph_retriever,
            graph_builder,
            _seed_nodes,
            _get_graph_optional,
        )
        hybrid_retriever.load()
        graph_builder.load()
        print("✅ 실제 Retriever 로드 완료")
    except Exception as e:
        print(f"❌ Retriever 로드 실패: {e}", file=sys.stderr)
        print("   Mock 모드로 전환합니다.")
        USE_REAL = False

# ── 테스트 쿼리셋 ─────────────────────────────────────────────
# (disease_name, stage, query, expected_keywords, disease_tag, allowed_tags)
# disease_tag / allowed_tags: source의 "disease:xxx"; MULTIHOP만 allowed_tags로 다중 허용
TEST_QUERIES: list[tuple[str, int, str, list[str], str, Optional[list[str]]]] = [
    # ── 난이도 하: 단일 질환 명확한 치료 (BM25 보강 효과 검증) ──
    (
        "녹내장", 2,
        "녹내장 Stage 2 안압 하강 1차 치료제",
        ["IOP", "prostaglandin", "프로스타글란딘", "topical", "intraocular"],
        "glaucoma",
        None,
    ),
    (
        "백내장", 1,
        "초기 백내장 수술 적응증과 기준",
        ["phacoemulsification", "IOL", "cataract", "lens", "visual acuity"],
        "cataract",
        None,
    ),
    (
        "황반변성", 2,
        "습성 황반변성 주사 치료 가이드라인",
        ["anti-VEGF", "ranibizumab", "bevacizumab", "aflibercept", "neovascular"],
        "amd",
        None,
    ),

    # ── 난이도 중: 특정 시술 (Dense 의미 검색 효과 검증) ──────
    (
        "당뇨망막병증", 3,
        "증식성 당뇨망막병증 PRP 범망막광응고술 시행 기준",
        ["photocoagulation", "PRP", "neovascularization", "proliferative"],
        "dr",
        None,
    ),
    (
        "녹내장", 3,
        "진행성 녹내장 수술적 치료 트라베쿨렉토미 적응증",
        ["trabeculectomy", "MIGS", "surgical", "glaucoma drainage"],
        "glaucoma",
        None,
    ),

    # ── 난이도 상: Multi-hop 복합 추론 (Graph RAG 핵심 검증) ──
    (
        "당뇨망막병증", 2,
        "당뇨 동반 녹내장 환자 베타차단제 금기 약물",
        ["beta-blocker", "베타차단제", "contraindication", "masking", "timolol"],
        "dr",
        ["dr", "glaucoma"],
    ),
]

MULTIHOP_IDX = 5  # TEST_QUERIES에서 multi-hop 케이스 인덱스


# ── Mock 검색기 (DB 연결 전 구조 검증용) ──────────────────────

def _mock_hybrid_search(
    query: str,
    disease_name: str,
    stage: int,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """실제 hybrid_retriever.search() 인터페이스와 동일한 반환 구조."""
    # 실제 source 필드 형식: "AAO PPP - Diabetic Retinopathy PPP_... | disease:dr"
    mock_db = [
        {"id": 1,  "content": "Prostaglandin analogs are first-line therapy for IOP reduction in glaucoma.", "source": "AAO PPP - Primary Open-Angle Glaucoma PPP_2026 | disease:glaucoma", "title": "Glaucoma PPP", "page": None},
        {"id": 2,  "content": "Topical beta-blockers reduce intraocular pressure effectively.", "source": "AAO PPP - Primary Open-Angle Glaucoma PPP_2026 | disease:glaucoma", "title": "Glaucoma PPP", "page": None},
        {"id": 3,  "content": "Phacoemulsification with IOL implantation is the standard cataract surgery.", "source": "AAO PPP - Cataract in the Adult Eye PPP_7.9.25 | disease:cataract", "title": "Cataract PPP", "page": None},
        {"id": 4,  "content": "Anti-VEGF therapy with ranibizumab or bevacizumab for neovascular AMD.", "source": "AAO PPP - Age-Related Macular Degeneration PPP_Dec 2025 | disease:amd", "title": "AMD PPP", "page": None},
        {"id": 5,  "content": "Panretinal photocoagulation (PRP) for proliferative diabetic retinopathy.", "source": "AAO PPP - Diabetic Retinopathy PPP_8.4.25 | disease:dr", "title": "DR PPP", "page": None},
        {"id": 6,  "content": "Beta-blocker contraindication in diabetic patients due to masking hypoglycemia symptoms.", "source": "AAO PPP - Diabetic Retinopathy PPP_8.4.25 | disease:dr", "title": "DR PPP", "page": None},
        {"id": 7,  "content": "Trabeculectomy and MIGS for advanced glaucoma surgical treatment.", "source": "AAO PPP - Primary Open-Angle Glaucoma PPP_2026 | disease:glaucoma", "title": "Glaucoma PPP", "page": None},
    ]
    q_lower = query.lower()
    dn_lower = disease_name.lower()

    scored = []
    for doc in mock_db:
        score = 0
        c = doc["content"].lower()
        s = doc["source"].lower()
        for word in q_lower.split() + dn_lower.split():
            if len(word) >= 3 and word in c:
                score += 1
        scored.append((score, doc))

    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:top_k]]


def _mock_graph_refine(
    rows: list[dict[str, Any]],
    disease_name: str,
    stage: int,
) -> list[dict[str, Any]]:
    """Graph RAG mock: multi-hop 케이스에서만 재정렬 시뮬레이션."""
    if "녹내장" in disease_name or "당뇨" in disease_name:
        # beta-blocker 관련 문서를 상위로 올리는 시뮬레이션
        priority = [r for r in rows if "beta" in r.get("content", "").lower()
                    or "contraindication" in r.get("content", "").lower()]
        others = [r for r in rows if r not in priority]
        return priority + others
    return rows


# ── 유틸 함수 ─────────────────────────────────────────────────

def _is_relevant(doc: dict[str, Any], keywords: list[str]) -> bool:
    """content에 expected_keywords 중 하나라도 포함되면 관련 문서."""
    content = doc.get("content", "").lower()
    return any(kw.lower() in content for kw in keywords)


def _disease_tag_match(
    doc: dict[str, Any],
    expected_tag: str,
    allowed_tags: Optional[list[str]] = None,
) -> bool:
    """source 필드에서 'disease:xxx' 파싱 후 태그 일치 검사."""
    source = doc.get("source", "")
    if "disease:" not in source:
        return False
    tag = source.split("disease:")[-1].strip().split()[0].lower()
    if allowed_tags:
        return tag in [t.lower() for t in allowed_tags]
    return tag == expected_tag.lower()


def _compute_metrics(
    results: list[dict[str, Any]],
    keywords: list[str],
    disease_tag: str,
    allowed_tags: Optional[list[str]] = None,
) -> dict[str, float]:
    """Hit Rate@3, Precision@3, MRR, Disease Match@3 계산."""
    k = len(results)
    if k == 0:
        return {"hit_rate": 0.0, "precision": 0.0, "mrr": 0.0, "disease_match": 0.0}

    relevant_count = 0
    disease_match_count = 0
    first_hit_rank = None

    for rank, doc in enumerate(results, 1):
        if _is_relevant(doc, keywords):
            relevant_count += 1
            if first_hit_rank is None:
                first_hit_rank = rank
        if _disease_tag_match(doc, disease_tag, allowed_tags):
            disease_match_count += 1

    return {
        "hit_rate":     1.0 if relevant_count > 0 else 0.0,
        "precision":    relevant_count / k,
        "mrr":          1.0 / first_hit_rank if first_hit_rank else 0.0,
        "disease_match": disease_match_count / k,
    }


def _rerank_delta(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    keywords: list[str],
) -> int:
    """Graph rerank 전후 첫 번째 관련 문서 순위 변화 (음수 = 개선)."""
    def first_hit_rank(docs):
        for i, d in enumerate(docs, 1):
            if _is_relevant(d, keywords):
                return i
        return len(docs) + 1

    return first_hit_rank(after) - first_hit_rank(before)


# ── 그래프 메트릭 ─────────────────────────────────────────────

def _eval_graph_metrics(disease_name: str, stage: int) -> dict[str, Any]:
    """Seed Node Hit, BFS Reach Count 측정 (실제 모드 전용)."""
    if not USE_REAL:
        return {"seed_count": "N/A (Mock)", "bfs_reach": "N/A (Mock)"}
    try:
        G = _get_graph_optional()
        if G is None:
            return {"seed_count": 0, "bfs_reach": 0, "note": "graph.pkl 없음"}
        seeds = _seed_nodes(G, disease_name, stage)
        from SH.rag.graph_rag import MAX_BFS_DEPTH, _multisource_bfs_reachable
        ug = G.to_undirected()
        reached = _multisource_bfs_reachable(ug, seeds, MAX_BFS_DEPTH)
        return {"seed_count": len(seeds), "bfs_reach": len(reached)}
    except Exception as e:
        return {"seed_count": "err", "bfs_reach": str(e)}


# ── 메인 평가 루프 ────────────────────────────────────────────

def evaluate():
    mode_label = "🔴 실제 DB" if USE_REAL else "🟡 Mock"
    print("=" * 65)
    print(f"  안과 CDSS RAG 파이프라인 평가  [{mode_label}]")
    print("=" * 65)

    total = len(TEST_QUERIES)
    hybrid_results_all: list[dict] = []
    graph_results_all:  list[dict] = []

    for idx, (disease, stage, query, keywords, tag, allowed_tags) in enumerate(
        TEST_QUERIES, 1
    ):
        label = "[Multi-hop]" if idx - 1 == MULTIHOP_IDX else ""
        print(f"\n[{idx}/{total}] {label} {query[:55]}...")
        print(f"  질환: {disease} Stage {stage} | 기대 태그: {tag}")

        # ── Hybrid RAG ────────────────────────────────────────
        t0 = time.perf_counter()
        if USE_REAL:
            hybrid_docs = hybrid_retriever.search(
                query=query, disease_name=disease, stage=stage, top_k=3
            )
        else:
            hybrid_docs = _mock_hybrid_search(query, disease, stage, top_k=3)
        hybrid_ms = (time.perf_counter() - t0) * 1000

        h_metrics = _compute_metrics(hybrid_docs, keywords, tag, allowed_tags)

        # ── Graph RAG ─────────────────────────────────────────
        t1 = time.perf_counter()
        if USE_REAL:
            graph_docs = graph_retriever.refine(
                hybrid_docs, disease_name=disease, stage=stage
            )
        else:
            graph_docs = _mock_graph_refine(hybrid_docs, disease, stage)
        graph_ms = (time.perf_counter() - t1) * 1000

        g_metrics = _compute_metrics(graph_docs, keywords, tag, allowed_tags)
        delta = _rerank_delta(hybrid_docs, graph_docs, keywords)
        gm = _eval_graph_metrics(disease, stage)

        hybrid_results_all.append(h_metrics)
        graph_results_all.append({**g_metrics, "delta": delta})

        # 출력
        print(f"  Hybrid  | Hit@3:{h_metrics['hit_rate']:.0%}  "
              f"P@3:{h_metrics['precision']:.2f}  "
              f"MRR:{h_metrics['mrr']:.2f}  "
              f"DMatch:{h_metrics['disease_match']:.0%}  "
              f"({hybrid_ms:.0f}ms)")
        print(f"  Graph   | Hit@3:{g_metrics['hit_rate']:.0%}  "
              f"P@3:{g_metrics['precision']:.2f}  "
              f"MRR:{g_metrics['mrr']:.2f}  "
              f"DMatch:{g_metrics['disease_match']:.0%}  "
              f"({graph_ms:.0f}ms)  "
              f"순위변화: {'+' if delta > 0 else ''}{delta}")
        print(f"  Graph 구조 | 시드:{gm['seed_count']}개  BFS도달:{gm['bfs_reach']}개")

        # 반환 문서 미리보기
        print("  반환 문서 (Hybrid):")
        for r, doc in enumerate(hybrid_docs, 1):
            mark = "✅" if _is_relevant(doc, keywords) else "❌"
            print(f"    {r}. {mark} {doc.get('content','')[:70]}...")

    # ── 최종 리포트 ───────────────────────────────────────────
    def avg(lst, key): return sum(r[key] for r in lst) / len(lst)

    print("\n" + "=" * 65)
    print("  📊 최종 평가 리포트")
    print("=" * 65)
    print(f"  {'지표':<20} {'Hybrid RAG':>12} {'Graph RAG':>12} {'목표':>8}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*8}")
    print(f"  {'Hit Rate@3':<20} {avg(hybrid_results_all,'hit_rate'):>11.1%} {avg(graph_results_all,'hit_rate'):>11.1%} {'≥85%':>8}")
    print(f"  {'Precision@3':<20} {avg(hybrid_results_all,'precision'):>11.1%} {avg(graph_results_all,'precision'):>11.1%} {'≥67%':>8}")
    print(f"  {'MRR':<20} {avg(hybrid_results_all,'mrr'):>11.2f} {avg(graph_results_all,'mrr'):>11.2f} {'≥0.70':>8}")
    print(f"  {'Disease Match@3':<20} {avg(hybrid_results_all,'disease_match'):>11.1%} {avg(graph_results_all,'disease_match'):>11.1%} {'≥70%':>8}")

    deltas = [r["delta"] for r in graph_results_all]
    improved = sum(1 for d in deltas if d < 0)
    print(f"\n  Graph RAG 순위 개선 쿼리: {improved}/{total}개")

    multihop = graph_results_all[MULTIHOP_IDX]
    print(f"  Multi-hop 추론 성공: {'✅' if multihop['hit_rate'] > 0 else '❌'} "
          f"(순위변화: {multihop['delta']})")

    print("=" * 65)

    if not USE_REAL:
        print("\n⚠️  Mock 모드 결과입니다. 실제 측정은 아래 명령어로 실행하세요:")
        print("   USE_REAL_RETRIEVER=1 python -m SH.rag.eval.eval_rag")


if __name__ == "__main__":
    evaluate()
