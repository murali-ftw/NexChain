"""ChromaDB persistence: idempotent upsert + top-k similarity search.

Retrieval output matches the frozen kb_search contract (ai/contracts.py
KBHit): list of {content, source_doc, score}.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from ai.rag.chunker import Chunk
from ai.rag.embedder import embed_query, embed_texts

CHROMA_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION_NAME = "knowledge_base"


def _get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def chunk_id(chunk: Chunk) -> str:
    """Stable ID derived from source_path + chunk index (idempotency key)."""
    return f"{chunk.source_path}::{chunk.chunk_index}"


def replace_document_chunks(doc_id: int, chunks: list[Chunk]) -> int:
    """Replace all vectors for one document with a freshly chunked set.

    Deletes any existing vectors tagged with this doc_id first, so
    re-ingestion is idempotent even if the chunk count for a document
    changes between runs (not just same-ID overwrite).
    """
    collection = _get_collection()
    collection.delete(where={"doc_id": doc_id})
    if not chunks:
        return 0

    ids = [chunk_id(c) for c in chunks]
    documents = [c.content for c in chunks]
    embeddings = embed_texts(documents)
    metadatas = [
        {
            "doc_id": c.doc_id,
            "title": c.title,
            "section": c.section,
            "source_path": c.source_path,
            "chunk_index": c.chunk_index,
        }
        for c in chunks
    ]
    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return len(ids)


def count() -> int:
    return _get_collection().count()


def search(query: str, top_k: int = 4) -> list[dict[str, Any]]:
    """Top-k similarity search. Returns [{content, source_doc, score}, ...]."""
    collection = _get_collection()
    query_embedding = embed_query(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    hits: list[dict[str, Any]] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        hits.append(
            {
                "content": doc,
                "source_doc": meta.get("title", meta.get("source_path", "")),
                "score": round(1 - dist, 4),
            }
        )
    return hits
