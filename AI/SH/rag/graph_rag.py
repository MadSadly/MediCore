"""
AI/SH/rag/graph_rag.py
NetworkX 그래프(pkl 로드) + 질환/Stage 시드 후 BFS로 관련 청크 id 수집
→ Hybrid 검색 결과를 그래프 근처 청크 우선 재정렬.
graph.pkl 없거나 로드 실패 시 Hybrid 순서 유지 (폴백).
"""

from __future__ import annotations

import pickle
from collections import deque
from pathlib import Path
from typing import Any

import networkx as nx


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
GRAPH_PKL = _DATA_DIR / "graph.pkl"

MAX_BFS_DEPTH = 4


# 한국어 질환명(DL 결과) ↔ 그래프 엔티티 id에 쓰이는 영문 토큰 힌트
_KO_HINTS: dict[str, tuple[str, ...]] = {
    "정상": ("normal", "healthy", "screening"),
    "녹내장": ("glaucoma", "iop", "intraocular", "trabecular", "optic"),
    "백내장": ("cataract", "lens", "phaco"),
    "당뇨망막병증": ("diabetic", "retinopathy", "anti-vegf", "macular_edema"),
    "황반변성": ("amd", "macular", "neovascular", "drusen"),
}

_GRAPH_CACHE: nx.MultiDiGraph | None = None
_GRAPH_TRIED = False


def _get_graph_optional() -> nx.MultiDiGraph | None:
    """graph.pkl 미존재/손상 시 None → Hybrid 순서 유지."""
    global _GRAPH_CACHE, _GRAPH_TRIED
    if _GRAPH_TRIED:
        return _GRAPH_CACHE
    _GRAPH_TRIED = True
    if not GRAPH_PKL.exists():
        return None
    try:
        with GRAPH_PKL.open("rb") as f:
            g = pickle.load(f)
        if not isinstance(g, nx.MultiDiGraph):
            return None
        _GRAPH_CACHE = g
        return _GRAPH_CACHE
    except Exception:
        return None


def _seed_nodes(graph: nx.MultiDiGraph, disease_name: str, stage: int) -> list[str]:
    """질환명·stage 토큰이 노드 문자열과 겹치는 노드를 후보 시드로."""
    name_l = disease_name.strip().lower()
    needles: set[str] = set()
    for ko, ents in _KO_HINTS.items():
        if ko in disease_name:
            needles.update(e.lower() for e in ents)
    needles.update(
        [
            name_l.replace(" ", "_"),
            f"stage_{stage}",
            f"stage {stage}",
            str(stage),
        ]
    )

    seeds: list[str] = []
    for nid in graph.nodes():
        lowered = nid.lower()
        hit = False
        for n in needles:
            if len(n) >= 3 and (n in lowered or lowered in n):
                hit = True
                break
        if not hit and name_l:
            tokens = "".join(filter(str.isalpha, name_l.split()[0])).lower()
            if len(tokens) >= 3 and tokens in lowered:
                hit = True
        if hit:
            seeds.append(str(nid))
    out: list[str] = []
    seen = set()
    for s in seeds:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _multisource_bfs_reachable(ug: nx.Graph, seeds: list[str], max_depth: int) -> dict[str, int]:
    dist: dict[str, int] = {}
    dq: deque[str] = deque()
    for s in seeds:
        if s in ug.nodes:
            dist[s] = 0
            dq.append(s)
    while dq:
        u = dq.popleft()
        du = dist[u]
        if du >= max_depth:
            continue
        for v in ug.neighbors(u):
            nd = du + 1
            if nd > max_depth:
                continue
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                dq.append(v)
    return dist


def _ordered_chunk_ids_from_subgraph(G: nx.MultiDiGraph, reached: dict[str, int]) -> list[int]:
    """방문 노드 부근 관계선의 source_chunk_id를 거리 순으로 정렬하여 중복 제거."""
    pairs: list[tuple[int, int]] = []

    for u, v, _, data in G.edges(keys=True, data=True):
        cid = data.get("source_chunk_id")
        if cid is None:
            continue
        du = reached.get(u)
        dv = reached.get(v)
        if du is None and dv is None:
            continue
        try:
            i = int(cid)
        except (TypeError, ValueError):
            continue
        cand: list[int] = []
        ru = reached.get(u)
        rv = reached.get(v)
        if ru is not None:
            cand.append(int(ru))
        if rv is not None:
            cand.append(int(rv))
        if not cand:
            continue
        d = min(cand)
        pairs.append((d, i))

    pairs.sort(key=lambda x: (x[0], x[1]))
    out: list[int] = []
    seen: set[int] = set()
    for _, cid in pairs:
        if cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


class GraphBuilder:
    """모듈 메타."""

    _module_tag = "eyes"

    def load(self) -> None:
        return

    @property
    def module_tag(self) -> str:
        return self._module_tag


graph_builder = GraphBuilder()


class GraphRetriever:
    """Hybrid 결과 행(dict, id키) 순서를 그래프 기준으로 재조정."""

    def refine(
        self,
        rows: list[dict[str, Any]],
        *,
        disease_name: str,
        stage: int,
    ) -> list[dict[str, Any]]:
        if not rows:
            return rows

        G = _get_graph_optional()
        if G is None or G.number_of_nodes() == 0:
            return rows

        seeds = _seed_nodes(G, disease_name, stage)
        if not seeds:
            return rows

        ug = G.to_undirected()
        reached = _multisource_bfs_reachable(ug, seeds, MAX_BFS_DEPTH)
        chunk_order = _ordered_chunk_ids_from_subgraph(G, reached)
        if not chunk_order:
            return rows

        rank_map = {cid: i for i, cid in enumerate(chunk_order)}
        big = len(chunk_order) + 99

        def sort_key(r: dict[str, Any]) -> tuple[int, int]:
            rid = r.get("id")
            try:
                ri = int(rid) if rid is not None else -1
            except (TypeError, ValueError):
                return big, 0
            return (rank_map.get(ri, big), ri)

        return sorted(rows, key=sort_key)


graph_retriever = GraphRetriever()
