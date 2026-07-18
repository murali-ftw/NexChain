"""P3.3 RAG ingestion CLI entrypoint.

Run from repo root: python -m ai.rag.ingest
"""

from __future__ import annotations

from ai.rag import chunker, loader, vector_store


def run_ingestion() -> None:
    documents = loader.load_all_documents()
    print(f"Loaded {len(documents)} documents from {loader.INDEX_PATH}")

    total_chunks = 0
    for document in documents:
        chunks = chunker.chunk_document(document)
        vector_store.replace_document_chunks(document.doc_id, chunks)
        total_chunks += len(chunks)
        print(
            f"  [{document.doc_id:>2}] {document.title:<45} -> {len(chunks)} chunk(s)"
        )

    print(
        f"\nIngestion complete: {len(documents)} documents, {total_chunks} chunks, "
        f"{vector_store.count()} vectors in store at {vector_store.CHROMA_DIR}"
    )


if __name__ == "__main__":
    run_ingestion()
