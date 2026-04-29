"""
AI/SH/rag/chunk_and_embed.py
안과 CDSS — AAO 가이드라인 PDF 청킹 + pgvector 삽입

사용법:
  cd D:\\MediCore\\AI
  python -m SH.rag.chunk_and_embed

대상 파일:
  AI/SH/data/aao_guidelines/*.pdf (5개)

삽입 규칙:
  module_tag = 'eyes'  (CLAUDE.md + vectorGuide.md 필수)
"""

import os
import re
import psycopg2
from pathlib import Path

from dotenv import load_dotenv
from FlagEmbedding import BGEM3FlagModel

# ── 환경 설정 ─────────────────────────────────────────────────
_load_root = Path(__file__).resolve().parents[3]
load_dotenv(_load_root / ".env")

PDF_DIR    = Path(__file__).resolve().parents[1] / "data" / "aao_guidelines"
MODULE_TAG = "eyes"

# ── 질환 매핑 (파일명 → disease 태그) ────────────────────────
DISEASE_MAP = {
    "Diabetic Retinopathy":          "dr",
    "Age-Related Macular Degeneration": "amd",
    "Primary Open-Angle Glaucoma":   "glaucoma",
    "Cataract":                      "cataract",
    "Comprehensive Adult Medical":   "normal",
}

# ── 청킹 설정 ─────────────────────────────────────────────────
CHUNK_SIZE    = 400   # 토큰 기준 (단어 수로 근사)
CHUNK_OVERLAP = 50


# ── PDF 텍스트 추출 ───────────────────────────────────────────

def extract_text_from_pdf(pdf_path: Path) -> str:
    """PyMuPDF로 PDF 텍스트 추출"""
    try:
        import fitz  # PyMuPDF
        doc  = fitz.open(str(pdf_path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except ImportError:
        raise ImportError("PyMuPDF 필요: pip install pymupdf")


# ── 시맨틱 청킹 ───────────────────────────────────────────────

def semantic_chunk(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    섹션 구조 기반 시맨틱 청킹
    1. 헤딩/섹션 경계 우선 분할
    2. 너무 긴 섹션은 단어 단위로 추가 분할
    3. 너무 짧은 청크는 다음과 병합
    """
    # REFERENCES / LITERATURE SEARCH 이후(참고문헌·검색전랠) 버림 — RAG 노이즈·중복 배제
    _ref_cut = re.search(
        r'(?mi)^(?:REFERENCES|LITERATURE\s+SEARCH)\s*$',
        text,
    )
    if _ref_cut:
        text = text[: _ref_cut.start()]

    # 불필요한 공백 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # AAO PPP 헤딩 기준 섹션 분할
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
            if len(words) >= 30:  # 너무 짧은 청크 제외
                chunks.append(section)
        else:
            # 긴 섹션 슬라이딩 윈도우 분할
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                if len(chunk_words) >= 30:
                    chunks.append(" ".join(chunk_words))

    return chunks


# ── 질환 태그 감지 ────────────────────────────────────────────

def detect_disease(filename: str) -> str:
    """파일명에서 질환 태그 감지"""
    for keyword, tag in DISEASE_MAP.items():
        if keyword.lower() in filename.lower():
            return tag
    return "general"


# ── pgvector 삽입 ─────────────────────────────────────────────

def insert_chunks(conn, chunks: list[dict], model: BGEM3FlagModel):
    """청크 임베딩 후 pgvector 삽입"""
    cursor = conn.cursor()

    texts = [c["content"] for c in chunks]
    print(f"  임베딩 생성 중... ({len(texts)}개 청크)")

    # BGE-M3 배치 임베딩
    batch_size = 32
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = model.encode(batch, batch_size=batch_size)['dense_vecs']
        all_embeddings.extend(embeddings)
        print(f"    {min(i + batch_size, len(texts))}/{len(texts)} 완료", end="\r")

    print()

    # DB 삽입
    inserted = 0
    for chunk, embedding in zip(chunks, all_embeddings):
        cursor.execute("""
            INSERT INTO medical_knowledge
                (module_tag, content, source, embedding)
            VALUES (%s, %s, %s, %s)
        """, (
            MODULE_TAG,
            chunk["content"],
            chunk["source"],
            embedding.tolist(),
        ))
        inserted += 1

    conn.commit()
    cursor.close()
    return inserted


# ── 중복 방지 ─────────────────────────────────────────────────

def clear_existing(conn):
    """기존 eyes 데이터 삭제 (재실행 시 중복 방지)"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medical_knowledge WHERE module_tag = %s", (MODULE_TAG,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    print(f"  기존 데이터 삭제: {deleted}건")


# ── 메인 ─────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("📚 AAO 가이드라인 청킹 + pgvector 삽입")
    print(f"   module_tag: {MODULE_TAG}")
    print("=" * 60)

    # PDF 파일 확인
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ PDF 없음: {PDF_DIR}")
        return

    print(f"\n발견된 PDF: {len(pdf_files)}개")
    for f in pdf_files:
        print(f"  - {f.name}")

    # BGE-M3 모델 로드
    print("\n🔧 BGE-M3 모델 로드 중...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("✅ 모델 로드 완료")

    # DB 연결
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    print("✅ DB 연결 완료")

    # 기존 eyes 데이터 초기화
    print("\n🗑️  기존 eyes 데이터 초기화...")
    clear_existing(conn)

    # PDF별 처리
    total_inserted = 0

    for pdf_path in sorted(pdf_files):
        print(f"\n📄 처리 중: {pdf_path.name}")

        # 텍스트 추출
        text = extract_text_from_pdf(pdf_path)
        print(f"  텍스트 추출: {len(text):,}자")

        # 질환 태그
        disease = detect_disease(pdf_path.name)
        source  = f"AAO PPP - {pdf_path.stem}"

        # 청킹
        raw_chunks = semantic_chunk(text)
        print(f"  청크 수: {len(raw_chunks)}개")

        # 메타데이터 포함 청크 구성
        chunks = [
            {
                "content": chunk,
                "source":  f"{source} | disease:{disease}",
            }
            for chunk in raw_chunks
        ]

        # 삽입
        inserted = insert_chunks(conn, chunks, model)
        total_inserted += inserted
        print(f"  ✅ 삽입 완료: {inserted}개")

    conn.close()

    print("\n" + "=" * 60)
    print(f"🎉 완료! 총 {total_inserted}개 청크 삽입")
    print(f"   module_tag: {MODULE_TAG}")
    print(f"   다음: retriever.py로 Hybrid RAG 구성")
    print("=" * 60)


if __name__ == "__main__":
    main()
