"""
AI/SH/rag/chunk_and_embed.py
안과 CDSS — AAO 가이드라인 PDF 청킹 + pgvector 삽입

임베딩: Vertex AI gemini-embedding-001 (768차원, RETRIEVAL_DOCUMENT)

사용법:
  cd D:\\MediCore\\AI
  python -m SH.rag.chunk_and_embed

대상 파일:
  AI/SH/data/aao_guidelines/*.pdf (5개)

삽입 규칙:
  module_tag = 'eyes'  (CLAUDE.md + vectorGuide.md 필수)

사전 요건:
  MediCore/.env 에 DATABASE_URL, GCP_PROJECT_ID, GCP_LOCATION, GCP_KEY_PATH 등
"""

import os
import re
import psycopg2
from pathlib import Path

from dotenv import load_dotenv

from SH.rag.gemini_embeddings import (
    EMBEDDING_DIM,
    MODEL_NAME,
    embed_documents,
    ensure_vertex,
)

# ── 환경 설정 ─────────────────────────────────────────────────
_load_root = Path(__file__).resolve().parents[3]
load_dotenv(_load_root / ".env")

PDF_DIR = Path(__file__).resolve().parents[1] / "data" / "aao_guidelines"
MODULE_TAG = "eyes"

GEMINI_EMBED_BATCH = 8

# ── 질환 매핑 (파일명 → disease 태그) ────────────────────────
DISEASE_MAP = {
    "Diabetic Retinopathy":          "dr",
    "Age-Related Macular Degeneration": "amd",
    "Primary Open-Angle Glaucoma":   "glaucoma",
    "Cataract":                      "cataract",
    "Comprehensive Adult Medical":   "normal",
}

# ── 청킹 설정 ─────────────────────────────────────────────────
CHUNK_SIZE = 400   # 토큰 기준 (단어 수로 근사)
CHUNK_OVERLAP = 50


# ── PDF 텍스트 추출 ───────────────────────────────────────────

def extract_text_from_pdf(pdf_path: Path) -> str:
    """PyMuPDF로 PDF 텍스트 추출"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except ImportError:
        raise ImportError("PyMuPDF 필요: pip install pymupdf")


# ── 시맨틱 청킹 ────────────────────────────────────────────────

def semantic_chunk(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """섹션 구조 기반 시맨틱 청킹."""
    _ref_cut = re.search(
        r'(?mi)^(?:REFERENCES|LITERATURE\s+SEARCH)\s*$',
        text,
    )
    if _ref_cut:
        text = text[: _ref_cut.start()]

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    _ppp_headings = (
        r'BACKGROUND|DIAGNOSIS|TREATMENT|MANAGEMENT|'
        r'FOLLOW-UP|RECOMMENDATION|APPENDIX|TABLE'
    )
    section_pattern = re.compile(
        rf'\n(?=(?:{_ppp_headings})(?:\s|\n|$))',
        re.IGNORECASE | re.MULTILINE,
    )
    sections = section_pattern.split(text)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        words = section.split()

        if len(words) <= chunk_size:
            if len(words) >= 30:
                chunks.append(section)
        else:
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                if len(chunk_words) >= 30:
                    chunks.append(" ".join(chunk_words))

    return chunks


def detect_disease(filename: str) -> str:
    """파일명에서 질환 태그 감지"""
    for keyword, tag in DISEASE_MAP.items():
        if keyword.lower() in filename.lower():
            return tag
    return "general"


def insert_chunks(conn, chunks: list[dict]) -> int:
    """청크 임베딩 후 pgvector 삽입 (Gemini 768차원)."""
    texts = [c["content"] for c in chunks]
    print(f"  Gemini 임베딩 생성 중... ({len(texts)}개 청크)")

    all_embeddings = embed_documents(texts, batch_size=GEMINI_EMBED_BATCH)
    if len(all_embeddings) != len(texts):
        raise RuntimeError(f"임베딩 개수 불일치: got {len(all_embeddings)}, expected {len(texts)}")

    inserted = 0
    cursor = None
    try:
        cursor = conn.cursor()

        for chunk, embedding in zip(chunks, all_embeddings):
            cursor.execute(
                """
                INSERT INTO medical_knowledge
                    (module_tag, content, source, embedding, task_type)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    MODULE_TAG,
                    chunk["content"],
                    chunk["source"],
                    embedding,
                    "RETRIEVAL_DOCUMENT",
                ),
            )
            inserted += 1

        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()

    return inserted


def clear_existing(conn):
    """기존 eyes 데이터 삭제 (재실행 시 중복 방지)"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medical_knowledge WHERE module_tag = %s", (MODULE_TAG,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    print(f"  기존 데이터 삭제: {deleted}건")


def main():
    print("=" * 60)
    print("📚 AAO 가이드라인 청킹 + pgvector 삽입")
    print(f"   module_tag: {MODULE_TAG}")
    print("   임베딩: Vertex gemini-embedding-001 (768)")
    print("=" * 60)

    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ PDF 없음: {PDF_DIR}")
        return

    print(f"\n발견된 PDF: {len(pdf_files)}개")
    for f in pdf_files:
        print(f"  - {f.name}")

    yn = input(
        "\n기존 eyes 데이터를 삭제하고 재삽입합니다. 계속하시겠습니까? (y/n): "
    ).strip().lower()
    if yn != "y":
        print("취소되었습니다.")
        return

    print("\n🔧 Vertex Gemini 임베딩 초기화 중...")
    ensure_vertex()
    print(f"✅ 준비 완료 ({MODEL_NAME}, {EMBEDDING_DIM}차원)")

    conn = None
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL 미설정")
        conn = psycopg2.connect(db_url)
        print("✅ DB 연결 완료")

        print("\n🗑️  기존 eyes 데이터 초기화...")
        clear_existing(conn)

        total_inserted = 0

        for pdf_path in sorted(pdf_files):
            print(f"\n📄 처리 중: {pdf_path.name}")

            text = extract_text_from_pdf(pdf_path)
            print(f"  텍스트 추출: {len(text):,}자")

            disease = detect_disease(pdf_path.name)
            source = f"AAO PPP - {pdf_path.stem}"

            raw_chunks = semantic_chunk(text)
            print(f"  청크 수: {len(raw_chunks)}개")

            chunks = [
                {
                    "content": chunk,
                    "source": f"{source} | disease:{disease}",
                }
                for chunk in raw_chunks
            ]

            inserted = insert_chunks(conn, chunks)
            total_inserted += inserted
            print(f"  ✅ 삽입 완료: {inserted}개")

        print("\n" + "=" * 60)
        print(f"🎉 완료! 총 {total_inserted}개 청크 삽입")
        print(f"   module_tag: {MODULE_TAG}")
        print("=" * 60)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
