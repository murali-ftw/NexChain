"""Verification script for the P3.3 completion gate:
"All documents are indexed and retrievable."

Run: python ai/rag/verify_ingestion.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai.rag import loader, vector_store  # noqa: E402
from ai.rag.ingest import run_ingestion  # noqa: E402

PASS = "PASS"
FAIL = "FAIL"


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    ok = True

    section("1. Ingest (first run) + totals")
    run_ingestion()
    manifest = loader.parse_manifest()
    total_docs = len(manifest)
    total_chunks = vector_store.count()
    print(f"Total documents in manifest: {total_docs}")
    print(f"Total chunks/vectors in store: {total_chunks}")

    section("2 & 3. Per-document retrieval check")
    missing: list[str] = []
    for entry in manifest:
        query = entry.description or entry.title
        hits = vector_store.search(query, top_k=6)
        titles_hit = {h["source_doc"] for h in hits}
        found = entry.title in titles_hit
        status = PASS if found else FAIL
        if not found:
            missing.append(entry.title)
            ok = False
        print(
            f"[{status}] doc_id={entry.doc_id:>2} '{entry.title}' "
            f"query={query[:60]!r} -> hits: {sorted(titles_hit)}"
        )

    if missing:
        print(f"\nDocuments NOT retrievable: {missing}")
    else:
        print("\nAll documents are retrievable by at least one query.")

    section("4. Flagship query: 'HS code mismatch customs' -> Customs Hold SOP")
    hits = vector_store.search("HS code mismatch customs", top_k=4)
    top_titles = [h["source_doc"] for h in hits]
    customs_found = "Customs Hold SOP" in top_titles
    status = PASS if customs_found else FAIL
    if not customs_found:
        ok = False
    print(f"[{status}] Top {len(hits)} results: {top_titles}")
    for h in hits:
        print(f"   score={h['score']:.4f}  source_doc={h['source_doc']}")

    section("5. Idempotency check (re-run ingestion)")
    before = vector_store.count()
    run_ingestion()
    after = vector_store.count()
    idempotent = before == after
    status = PASS if idempotent else FAIL
    if not idempotent:
        ok = False
    print(f"[{status}] chunk count before={before}, after re-ingest={after}")

    section("RESULT")
    if ok:
        print("Completion gate MET: all documents indexed and retrievable.")
    else:
        print("Completion gate NOT met - see FAIL lines above.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
