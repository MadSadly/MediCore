"""
AI/SH/rag/build_knowledge_graph.py
오프라인: medical_knowledge(eyes) 청크에서 Gemini Flash로 엔티티·관계 추출
→ entities.jsonl, graph.pkl(NetworkX), meta.json 저장

사용 전:
  1. chunk_and_embed 실행으로 DB 채워진 상태
  2. Gemini API 키 (예: GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수)

실행:
  cd D:\\MediCore\\AI
  python -m SH.rag.build_knowledge_graph
"""

from __future__ import annotations

import json
import os
import pickle
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import psycopg2
from dotenv import load_dotenv


_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_ROOT / ".env")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
GRAPH_PKL = DATA_DIR / "graph.pkl"
ENTITIES_JSONL = DATA_DIR / "entities.jsonl"
META_JSON = DATA_DIR / "meta.json"

MODULE_TAG = "eyes"
GEMINI_MODEL = "gemini-1.5-flash"
MAX_CONTENT_CHARS = 3500

EXTRACTION_PROMPT = """You are extracting a knowledge graph from ophthalmology guideline text.

Return VALID JSON ONLY. No markdown, no explanation.

Schema exactly:
{
  "entities": [
    {"id": "<lowercase_slug>", "type": "<disease|drug|procedure|finding|risk|stage|other>"}
  ],
  "relations": [
    {
      "from": "<entity_id>",
      "relation": "<predicate_snake_case>",
      "to": "<entity_id>",
      "source_chunk_id": <integer same as chunk_id below>
    }
  ]
}

Rules:
- Use English slug ids (e.g. glaucoma, topical_beta_blockers).
- relations[].source_chunk_id MUST equal the chunk_id given below.
- If nothing extractable: {{"entities": [], "relations": []}}

chunk_id={chunk_id}

text:
{text}
"""


def _configure_genai():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 또는 GOOGLE_API_KEY 를 .env 에 설정하세요.", file=sys.stderr)
        sys.exit(1)
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    return genai


def _strip_json_fence(text: str) -> str:
    s = (text or "").strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", s)
    if m:
        return m.group(1).strip()
    return s


def _is_rate_limit_error(exc: BaseException) -> bool:
    """429 · ResourceExhausted 등 할당량/속도 제한."""
    try:
        from google.api_core.exceptions import ResourceExhausted

        if isinstance(exc, ResourceExhausted):
            return True
    except ImportError:
        pass

    tn = type(exc).__name__.lower()
    if "resourceexhausted" in tn:
        return True
    blob = str(exc).lower()
    return (
        "429" in blob
        or "resource exhausted" in blob
        or "too many requests" in blob
        or ("quota" in blob and "exceed" in blob)
    )


def _extract_entities_json(genai_module, chunk_id: int, content: str) -> dict | None:
    model = genai_module.GenerativeModel(GEMINI_MODEL)
    body = content[:MAX_CONTENT_CHARS]
    prompt = EXTRACTION_PROMPT.format(chunk_id=chunk_id, text=body)
    max_attempts = 2  # 초기 1회 + rate limit 시 30초 후 1회 재시도

    for attempt in range(max_attempts):
        try:
            resp = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 2048,
                },
            )
            raw = getattr(resp, "text", None) or ""
            if not raw.strip() and resp.candidates:
                parts = getattr(resp.candidates[0].content, "parts", []) or []
                raw = "".join(getattr(p, "text", "") for p in parts)
            cleaned = _strip_json_fence(raw)
            return json.loads(cleaned)
        except Exception as e:
            if _is_rate_limit_error(e):
                print(
                    f"  ⏳ rate limit (chunk id={chunk_id}) "
                    f"attempt={attempt + 1}/{max_attempts}: {e}"
                )
                if attempt + 1 < max_attempts:
                    time.sleep(30.0)
                    continue
                print(f"  ⚠️ chunk id={chunk_id} 재시도 후 포기 · 스킵")
                return None
            print(f"  ⚠️ chunk id={chunk_id} 스킵: {e}")
            return None

    return None


def _apply_payload_to_graph(
    G: nx.MultiDiGraph,
    payload: dict,
    *,
    fallback_chunk_id: int,
    _edge_ctr: list[int],
):
    ents = payload.get("entities") or []
    rels = payload.get("relations") or []

    for ent in ents:
        try:
            eid = str(ent.get("id", "")).strip()
            etype = str(ent.get("type", "other")).strip() or "other"
            if not eid:
                continue
            if eid in G.nodes:
                G.nodes[eid]["types"] = G.nodes[eid].get("types") or []
                if etype not in G.nodes[eid]["types"]:
                    G.nodes[eid]["types"].append(etype)
                chs = G.nodes[eid].get("source_chunk_ids")
                if chs is not None and fallback_chunk_id not in chs:
                    chs.append(int(fallback_chunk_id))
            else:
                G.add_node(
                    eid,
                    types=[etype],
                    source_chunk_ids=[fallback_chunk_id],
                )
        except Exception:
            continue

    for rel in rels:
        try:
            frm = str(rel.get("from", "")).strip()
            to = str(rel.get("to", "")).strip()
            rel_type = str(rel.get("relation", "related")).strip() or "related"
            scid = rel.get("source_chunk_id")
            if scid is None:
                scid = fallback_chunk_id
            sid = int(scid)
            if not frm or not to:
                continue
            # 엔티지 정의 없더라도 엣지로 노드 존재 보장
            if frm not in G:
                G.add_node(frm, types=[], source_chunk_ids=[sid])
            if to not in G:
                G.add_node(to, types=[], source_chunk_ids=[sid])
            _edge_ctr[0] += 1
            G.add_edge(
                frm,
                to,
                key=_edge_ctr[0],
                relation=rel_type,
                source_chunk_id=sid,
            )
        except Exception:
            continue


def fetch_chunks(conn) -> list[tuple[int, str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, content, source
            FROM medical_knowledge
            WHERE module_tag = %s
            ORDER BY id
            """,
            (MODULE_TAG,),
        )
        rows = cur.fetchall()
    return [(int(r[0]), str(r[1] or ""), str(r[2] or "")) for r in rows]


def _load_processed_from_entities_jsonl() -> tuple[set[int], nx.MultiDiGraph, list[int]]:
    """기존 JSONL에서 처리된 chunk_id 집합 + 그래프 리플레이."""
    ids: set[int] = set()
    G = nx.MultiDiGraph()
    edge_ctr: list[int] = [0]

    if not ENTITIES_JSONL.exists():
        return ids, G, edge_ctr

    with ENTITIES_JSONL.open("r", encoding="utf-8") as fin:
        for lineno, raw in enumerate(fin, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                cid = int(obj["chunk_id"])
                ids.add(cid)
                payload = obj.get("payload")
                if isinstance(payload, dict):
                    _apply_payload_to_graph(G, payload, fallback_chunk_id=cid, _edge_ctr=edge_ctr)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
                print(f"⚠️  entities.jsonl 스킵 (line {lineno}): {e}", file=sys.stderr)

    return ids, G, edge_ctr


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL 미설정", file=sys.stderr)
        sys.exit(1)

    genai_module = _configure_genai()

    conn = psycopg2.connect(db_url)
    try:
        chunks = fetch_chunks(conn)
    finally:
        conn.close()

    processed_ids, G, edge_ctr = _load_processed_from_entities_jsonl()
    resumed_n = len(processed_ids)

    print(f"📄 청크 {len(chunks)}건 (DB) · 이미 처리된 청크 {resumed_n}개 스킵")
    print(f"   모델={GEMINI_MODEL}")

    chunks_extracted_prev = resumed_n

    mode = "a" if resumed_n > 0 else "w"
    with ENTITIES_JSONL.open(mode, encoding="utf-8") as fout:
        for idx, (cid, content, source) in enumerate(chunks):
            if cid in processed_ids:
                print(f"  skip {idx + 1}/{len(chunks)} id={cid} (already in jsonl)", end="\r")
                continue

            payload = _extract_entities_json(genai_module, cid, content)
            if payload is None:
                continue
            line = json.dumps(
                {"chunk_id": cid, "source": source, "payload": payload},
                ensure_ascii=False,
            )
            fout.write(line + "\n")
            fout.flush()
            processed_ids.add(cid)
            _apply_payload_to_graph(G, payload, fallback_chunk_id=cid, _edge_ctr=edge_ctr)
            print(f"  ok {idx + 1}/{len(chunks)} id={cid}", end="\r")
            time.sleep(1.0)
        print()

    with GRAPH_PKL.open("wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)

    try:
        with ENTITIES_JSONL.open(encoding="utf-8") as fcount:
            jsonl_lines = sum(1 for line in fcount if line.strip())
    except OSError:
        jsonl_lines = chunks_extracted_prev

    utc_now = datetime.now(timezone.utc).isoformat()
    meta = {
        "generated_at_utc": utc_now,
        "module_tag": MODULE_TAG,
        "model": GEMINI_MODEL,
        "chunk_total_in_db": len(chunks),
        "chunks_resume_skipped": resumed_n,
        "chunks_extracted_ok": jsonl_lines,
        "chunks_new_this_run_approx": jsonl_lines - chunks_extracted_prev,
        "nodes": int(G.number_of_nodes()),
        "edges": int(G.number_of_edges()),
    }
    with META_JSON.open("w", encoding="utf-8") as mf:
        json.dump(meta, mf, ensure_ascii=False, indent=2)

    print(f"✅ 저장: {GRAPH_PKL}")
    print(f"✅ 저장: {ENTITIES_JSONL}")
    print(f"✅ 저장: {META_JSON}")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
