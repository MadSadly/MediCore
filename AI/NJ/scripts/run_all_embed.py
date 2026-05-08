"""
6개 KDIGO 가이드라인 일괄 임베딩 — BGE-M3 모델을 한 번만 로드
"""
import sys
from pathlib import Path

GUIDELINES_DIR = Path(__file__).resolve().parents[1] / "guidelines"

PDFS = [
    "KDIGO-2024-CKD-Guideline.pdf",
    "KDIGO-2022-Diabetes-CKD-Guideline.pdf",
    "KDIGO-2021-Blood-Pressure-CKD-Guideline.pdf",
    "KDIGO-2017-CKD-MBD-Guideline.pdf",
    "KDIGO-2013-Lipids-Guideline.pdf",
    "chronic-kidney-disease-assessment-and-management-pdf-66143713055173.pdf",
]

if __name__ == "__main__":
    # chunk_and_embed 모듈을 임포트하면 BGE-M3가 로드됨 (1회)
    import NJ.scripts.chunk_and_embed as ce

    results = []
    for pdf_name in PDFS:
        pdf_path = GUIDELINES_DIR / pdf_name
        if not pdf_path.exists():
            print(f"\n[SKIP] 파일 없음: {pdf_path}")
            continue
        print(f"\n{'='*60}")
        print(f"처리 중: {pdf_name}")
        print("="*60)
        try:
            chunks = ce.load_and_split(str(pdf_path))
            if chunks:
                r = ce.store_chunks(chunks, pdf_name)
                results.append({"pdf": pdf_name, "chunks": r["chunk_count"], "ok": True})
            else:
                results.append({"pdf": pdf_name, "chunks": 0, "ok": False})
        except Exception as e:
            print(f"[ERROR] {pdf_name}: {e}")
            results.append({"pdf": pdf_name, "error": str(e), "ok": False})

    print("\n" + "="*60)
    print("전체 처리 결과")
    print("="*60)
    total = 0
    for r in results:
        status = "OK" if r.get("ok") else "FAIL"
        chunks = r.get("chunks", 0)
        total += chunks
        print(f"  [{status}] {r['pdf'][:50]} — {chunks}청크")
    print(f"\n  총 청크 수: {total}")
