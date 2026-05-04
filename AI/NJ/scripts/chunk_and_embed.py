"""
신부전 가이드라인 청킹 + BGE-M3 임베딩 + medical_knowledge 적재
"""

import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

import psycopg2
from psycopg2.extras import execute_values
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from FlagEmbedding import FlagModel

load_dotenv()

# ── DB 설정 ──────────────────────────────────────────────────
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "medizerodb",
    "user": "medizero",
    "password": "testpassword",
}

MODULE_TAG  = "kidney"
CHUNK_SIZE  = 800
CHUNK_OVERLAP = 100

# ── BGE-M3 로드 ──────────────────────────────────────────────
print("🔄 BGE-M3 로드 중... (첫 실행 시 2.3GB 다운로드)")
embedding_model = FlagModel(
    "BAAI/bge-m3",
    use_fp16=True,
    query_instruction_for_retrieval=(
        "Represent this medical query for searching relevant passages: "
    )
)
print("✅ BGE-M3 로드 완료\n")


def embed_batch(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    """배치 임베딩"""
    embeddings = embedding_model.encode(
        texts,
        batch_size=batch_size,
        max_length=8192,
    )
    return embeddings.tolist()


def load_and_split(pdf_path: str, max_pages: int = None) -> list[str]:
    """PDF 로드 + 청킹"""
    print(f"📖 PDF 로드: {pdf_path}")
    start = time.time()

    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    if max_pages:
        pages = pages[:max_pages]
        print(f"   ⚠️  테스트 모드: 앞 {max_pages}페이지만")

    full_text = "\n".join([p.page_content for p in pages])

    print(f"   페이지 수: {len(pages)}")
    print(f"   전체 문자 수: {len(full_text):,}")
    print(f"   로드 시간: {time.time() - start:.2f}초")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ".", " ", ""]
    )
    chunks = splitter.split_text(full_text)

    print(f"\n✂️  청킹 완료")
    print(f"   청크 수: {len(chunks)}")
    print(f"   평균 크기: {sum(len(c) for c in chunks)/len(chunks):.0f}자")

    return chunks


def store_chunks(chunks: list[str], source_name: str) -> dict:
    """임베딩 + DB 저장"""
    print(f"\n🔮 임베딩 시작 ({len(chunks)}개 청크)")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 기존 데이터 삭제 (재실행 대비)
    cur.execute(
        "DELETE FROM medical_knowledge WHERE source = %s AND module_tag = %s",
        (source_name, MODULE_TAG)
    )
    conn.commit()

    # 배치 임베딩
    embed_start = time.time()
    embeddings = embed_batch(chunks, batch_size=16)
    embed_time = time.time() - embed_start

    print(f"   임베딩 완료: {embed_time:.2f}초")
    print(f"   청크당 평균: {embed_time/len(chunks)*1000:.1f}ms")

    # DB 저장
    rows = [
        (chunk, source_name, MODULE_TAG, emb)
        for chunk, emb in zip(chunks, embeddings)
    ]

    store_start = time.time()
    execute_values(
        cur,
        """INSERT INTO medical_knowledge
           (content, source, module_tag, embedding)
           VALUES %s""",
        rows,
        template="(%s, %s, %s, %s::vector)"
    )
    conn.commit()
    store_time = time.time() - store_start

    print(f"   DB 저장: {store_time:.2f}초")

    cur.close()
    conn.close()

    return {
        "chunk_count": len(chunks),
        "embed_time": embed_time,
        "embed_avg_ms": embed_time / len(chunks) * 1000,
        "store_time": store_time,
    }


def measure_storage() -> dict:
    """저장소 크기 측정"""
    print(f"\n💾 저장소 크기 측정")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            pg_size_pretty(pg_total_relation_size('medical_knowledge')),
            pg_total_relation_size('medical_knowledge'),
            pg_size_pretty(pg_relation_size('medical_knowledge')),
            pg_size_pretty(pg_indexes_size('medical_knowledge')),
            pg_indexes_size('medical_knowledge')
    """)
    total_p, total_b, table_p, idx_p, idx_b = cur.fetchone()

    cur.execute(
        "SELECT COUNT(*) FROM medical_knowledge WHERE module_tag = %s",
        (MODULE_TAG,)
    )
    count = cur.fetchone()[0]

    print(f"   kidney 청크 수: {count}")
    print(f"   전체 크기: {total_p}")
    print(f"   테이블 크기: {table_p}")
    print(f"   인덱스 크기: {idx_p}")

    cur.close()
    conn.close()

    return {
        "chunk_count": count,
        "total_size_pretty": total_p,
        "total_size_bytes": total_b,
        "index_size_pretty": idx_p,
        "index_size_bytes": idx_b,
    }


def measure_search(num_queries: int = 20) -> dict:
    """검색 성능 측정"""
    print(f"\n🔍 검색 성능 측정 ({num_queries}회)")

    queries = [
        "만성 신부전 초기 증상",
        "CKD 4단계 치료",
        "투석 시작 시기",
        "단백뇨 관리",
        "GFR 감소 대응",
        "신부전 식이요법",
        "크레아티닌 정상 범위",
        "고혈압 신장 질환",
        "당뇨병성 신증",
        "신장 이식 기준",
    ]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    times = []

    for i in range(num_queries):
        query = queries[i % len(queries)]
        q_emb = embedding_model.encode(query).tolist()

        start = time.time()
        cur.execute("""
            SELECT id, content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM medical_knowledge
            WHERE module_tag = %s
            ORDER BY embedding <=> %s::vector
            LIMIT 5
        """, (q_emb, MODULE_TAG, q_emb))
        cur.fetchall()
        times.append((time.time() - start) * 1000)

    cur.close()
    conn.close()

    import statistics
    result = {
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }

    print(f"   평균: {result['avg_ms']:.2f}ms")
    print(f"   중앙값: {result['median_ms']:.2f}ms")
    print(f"   최소/최대: {result['min_ms']:.2f} / {result['max_ms']:.2f}ms")

    return result


def show_sample(query: str = "CKD 3단계 치료 가이드라인"):
    """샘플 검색 결과"""
    print(f"\n📋 샘플 검색: '{query}'")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    q_emb = embedding_model.encode(query).tolist()

    cur.execute("""
        SELECT content, 1 - (embedding <=> %s::vector) AS sim, source
        FROM medical_knowledge
        WHERE module_tag = %s
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """, (q_emb, MODULE_TAG, q_emb))

    for i, (content, sim, source) in enumerate(cur.fetchall(), 1):
        print(f"\n   [{i}] 유사도: {sim:.3f} | 출처: {source}")
        print(f"       {content[:200]}...")

    cur.close()
    conn.close()


def main(pdf_path: str, max_pages: int = None):
    print("=" * 60)
    print("🏥 신부전 가이드라인 청킹 + 실측")
    print("=" * 60)

    chunks = load_and_split(pdf_path, max_pages=max_pages)
    if not chunks:
        print("❌ 청크 없음")
        return

    source_name = Path(pdf_path).name
    proc_result = store_chunks(chunks, source_name)
    size_result = measure_storage()
    search_result = measure_search(num_queries=20)
    show_sample()

    # 보고서 저장
    report = {
        "source": source_name,
        "module_tag": MODULE_TAG,
        "embedding_model": "BGE-M3 (1024차원)",
        "chunk_config": {
            "size": CHUNK_SIZE,
            "overlap": CHUNK_OVERLAP
        },
        "processing": proc_result,
        "storage": size_result,
        "search": search_result,
    }

    with open("measurement_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("📤 팀 공유용 요약 (Slack에 복붙)")
    print("=" * 60)
    print(f"""
[신부전 가이드라인 실측 결과] kidney 담당: 김남준
- 가이드라인: {source_name}
- 임베딩 모델: BGE-M3 (1024차원)
- 청크 수: {size_result['chunk_count']}
- 전체 크기: {size_result['total_size_pretty']}
- 인덱스 크기: {size_result['index_size_pretty']}
- 평균 검색 시간: {search_result['avg_ms']:.2f}ms
- 최대 검색 시간: {search_result['max_ms']:.2f}ms
- 임베딩 시간/청크: {proc_result['embed_avg_ms']:.1f}ms
""")

    print("✅ measurement_report.json 저장 완료")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python chunk_and_embed.py <PDF경로> [max_pages]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"❌ 파일 없음: {pdf_path}")
        sys.exit(1)

    max_pages = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    main(pdf_path, max_pages=max_pages)
