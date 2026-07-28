"""P3.3 RAG ingestion CLI entrypoint.

Run from repo root: python -m ai.rag.ingest
"""

from __future__ import annotations

import logging
import time

from ai.logging_setup import configure_logging
from ai.rag import chunker, loader, vector_store

logger = logging.getLogger(__name__)


def run_ingestion() -> None:
    logger.info("lifecycle event=starting service=rag_ingest")
    started = time.perf_counter()
    documents = loader.load_all_documents()
    print(f"Loaded {len(documents)} documents from {loader.INDEX_PATH}")

    total_chunks = 0
    try:
        for document in documents:
            chunks = chunker.chunk_document(document)
            vector_store.replace_document_chunks(document.doc_id, chunks)
            total_chunks += len(chunks)
            # DEBUG: one line per document — a full ingestion run touches every
            # KB document, so INFO here would be exactly the noisy per-loop
            # logging this stack otherwise avoids. The friendly per-document
            # progress line below stays on stdout for a human watching the run.
            logger.debug(
                "rag_ingest doc_id=%s title=%s chunk_count=%d",
                document.doc_id,
                document.title,
                len(chunks),
            )
            print(
                f"  [{document.doc_id:>2}] {document.title:<45} -> {len(chunks)} chunk(s)"
            )
    except Exception:
        logger.exception(
            "lifecycle event=failed service=rag_ingest duration_ms=%.1f",
            (time.perf_counter() - started) * 1000,
        )
        raise

    duration_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "lifecycle event=completed service=rag_ingest document_count=%d "
        "chunk_count=%d vector_count=%d duration_ms=%.1f",
        len(documents),
        total_chunks,
        vector_store.count(),
        duration_ms,
    )
    print(
        f"\nIngestion complete: {len(documents)} documents, {total_chunks} chunks, "
        f"{vector_store.count()} vectors in store at {vector_store.CHROMA_DIR}"
    )


if __name__ == "__main__":
    configure_logging("rag_ingest")
    run_ingestion()
