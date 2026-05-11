"""
AI/SH/rag/build_knowledge_graph.py
오프라인: medical_knowledge(eyes) 청크에서 Gemini Flash로 엔티티·관계 추출
→ entities.jsonl, graph.pkl(NetworkX), meta.json 저장

사용 전:
  1. chunk_and_embed 실행으로 DB 채워진 상태
  2. Vertex AI용 GCP 설정 (.env: 프로젝트·리전·GOOGLE_APPLICATION_CREDENTIALS 등)

실행:
  cd D:\\MediCore\\AI
  python -m SH.rag.build_knowledge_graph
"""

from __future__ import annotations

import json
import os
import pickle
import random
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
GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_CONTENT_CHARS = 3500

EXTRACTION_PROMPT = """Extract a clinical knowledge graph from the ophthalmology guideline text.

[STRICT INSTRUCTIONS]
1. Return VALID JSON ONLY. No markdown, no ```json, no preamble, no explanation.
2. Extract ONLY the TOP 15 most clinically significant entities and relations.
3. Ensure ALL JSON braces and brackets are properly closed.
4. If nothing is extractable, return: {"entities": [], "relations": []}

[SCHEMA]
{
  "entities": [
    {"id": "lowercase_slug", "type": "disease|drug|procedure|finding|risk|stage|other"}
  ],
  "relations": [
    {
      "from": "entity_id",
      "relation": "predicate_snake_case",
      "to": "entity_id",
      "source_chunk_id": CHUNK_ID_PLACEHOLDER
    }
  ]
}

[RULES]
- IDs must be lowercase snake_case (e.g., "wet_amd", "anti_vegf").
- source_chunk_id MUST BE EXACTLY: CHUNK_ID_PLACEHOLDER
- Output: JSON object only. No comments, no trailing text.

Text to process:
TEXT_PLACEHOLDER
"""


def _configure_genai():
    from SH.llm.vertex_client import _init_vertex

    _init_vertex()
    return None


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
    from vertexai.generative_models import (
        GenerativeModel,
        GenerationConfig,
        HarmBlockThreshold,
        HarmCategory,
        SafetySetting,
    )

    model = GenerativeModel(GEMINI_MODEL)
    body = content[:MAX_CONTENT_CHARS]
    prompt = (
        EXTRACTION_PROMPT.replace("CHUNK_ID_PLACEHOLDER", str(chunk_id))
        .replace("TEXT_PLACEHOLDER", body)
    )
    safety_settings = [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
    max_attempts = 4
    base = 30.0

    for attempt in range(max_attempts):
        try:
            resp = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                ),
                safety_settings=safety_settings,
            )
            raw = getattr(resp, "text", None) or ""
            if not raw.strip() and resp.candidates:
                parts = getattr(resp.candidates[0].content, "parts", []) or []
                raw = "".join(getattr(p, "text", "") for p in parts)
            try:
                import json_repair

                return json_repair.loads(raw)
            except Exception:
                cleaned = _strip_json_fence(raw)
                return json.loads(cleaned)
        except Exception as e:
            # 1. API 할당량 초과(Rate Limit)인 경우: 재시도 로직
            if _is_rate_limit_error(e):
                if attempt + 1 < max_attempts:
                    jitter = random.uniform(0, 10)
                    wait = min(base * (2**attempt) + jitter, 300.0)
                    print(
                        f"\n  ⏳ rate limit (chunk id={chunk_id}) "
                        f"attempt={attempt + 1}/{max_attempts} · {wait:.1f}s 대기",
                        flush=True,
                    )
                    time.sleep(wait)
                    continue
                print(f"\n  ⚠️ chunk id={chunk_id} 재시도 후 포기 · 스킵")
                return None
            
            # 2. 그 외 에러(JSON 파싱 에러 등): 상세 로그 출력 후 스킵
            print(f"\n  ⚠️ chunk id={chunk_id} 스킵 발생")
            print(f"     에러 내용: {e}")
            
            # 로컬 변수에 raw가 존재한다면 (모델 응답은 받았으나 파싱에 실패한 경우) 출력
            # 'raw' 변수가 할당되기 전(API 호출 자체 실패) 에러가 날 수도 있으므로 체크함
            raw_text = locals().get('raw', 'N/A (응답 없음)')
            print(f"     모델 응답(Raw): {repr(raw_text)[:200]}...") # 앞부분 200자만 출력
            
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


def _check_integrity(processed_ids: set[int], db_chunk_ids: set[int]) -> None:
    """JSONL chunk_id와 DB id 집합 불일치 시 경고 로그."""
    only_in_jsonl = processed_ids - db_chunk_ids
    only_in_db = db_chunk_ids - processed_ids
    if only_in_jsonl:
        print(
            f"⚠️  [무결성] JSONL에만 있고 DB에 없는 chunk_id {len(only_in_jsonl)}개: "
            f"{sorted(only_in_jsonl)[:10]}{'...' if len(only_in_jsonl) > 10 else ''}",
            file=sys.stderr,
        )
    if only_in_db:
        print(
            f"ℹ️  [무결성] DB에 있으나 미처리 chunk_id {len(only_in_db)}개 "
            f"(이번 실행에서 처리 예정)"
        )


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL 미설정", file=sys.stderr)
        sys.exit(1)

    _configure_genai()

    conn = psycopg2.connect(db_url)
    try:
        chunks = fetch_chunks(conn)
    finally:
        conn.close()

    processed_ids, G, edge_ctr = _load_processed_from_entities_jsonl()
    db_chunk_ids = {cid for cid, _, _ in chunks}
    _check_integrity(processed_ids, db_chunk_ids)

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

            payload = _extract_entities_json(None, cid, content)
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
