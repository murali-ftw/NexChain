# RAG Ingestion Pipeline (P3.3, Day 3)

Indexes `ai/knowledge_base/` into a local ChromaDB vector store: parse
-> chunk -> embed -> store with source metadata. Retrieval primitives
only — no LLM answer generation (that's P3.4, Day 4).

## How to run

```bash
# from repo root, with deps from requirements.txt installed
python -m ai.rag.ingest
python ai/rag/verify_ingestion.py
```

Ingestion is idempotent: re-running `ingest.py` replaces each
document's vectors (deletes by `doc_id`, then re-upserts) instead of
duplicating them, so the total chunk count is stable across runs.

## Phase 1 findings this pipeline builds against

Cross-referenced against Person 2's work on `dev` before starting
(commits `e411bfd`, `3590ef1`):

- **`knowledge_documents` / `knowledge_chunks` Postgres tables already
  exist** (`db/migrations/001_init_schema.sql`, matches
  `docs/06_backend_schema.md` §2.11-2.12). They are **not** written by
  this pipeline — P3.3 scope is ChromaDB only, per the task spec. That
  table's `knowledge_chunks.chunk_index` is a *different* metadata
  layer (a SQL mirror of vector DB entries) from the vector-store
  metadata this pipeline writes, which follows
  `docs/02_technical_requirements.md` §6 exactly:
  `doc_id, title, section, source_path` (per chunk).
- **`kb_search` (Person 2, MCP)** is still an unimplemented stub in
  `ai/contracts.py` (`KBHit = {content, source_doc, score}`). No live
  MCP server exists yet. This pipeline's `vector_store.search()`
  returns that exact shape so it's a drop-in match once Person 2 wires
  the MCP tool up to it (or an equivalent).
- **No vector store existed anywhere in the repo.** ChromaDB is
  created locally at `ai/chroma_db/` (already gitignored) per the
  decision rule in the task: absence of Person 2's work in this area
  does not block Day 3.

## Design notes

- **Manifest**: `loader.py` parses `ai/knowledge_base/INDEX.md`'s
  table (doc_id, title, doc_type, source_path, description) as the
  authoritative document list — not a directory scan — so ingestion
  stays in sync with what P3.2 declared ready.
- **Chunking**: `chunker.py` splits each H2 section into paragraph-level
  units first (word count as a token proxy — no extra tokenizer
  dependency); a paragraph is only broken further, into sentence-level
  units, if it alone exceeds `MAX_CHUNK_TOKENS` (800), so a chunk never
  ends mid-sentence. For documents whose total content already fits in
  800 tokens, chunking short-circuits to a single chunk. Longer
  documents get their chunk count decided up front
  (`TARGET_CHUNK_TOKENS` = 650) and are sized toward that target rather
  than greedily filled, with the last flushed unit(s) worth ~100 tokens
  (`OVERLAP_TOKENS`) carried into the next chunk; a final undersized
  trailing chunk (< `MIN_CHUNK_TOKENS`, 500) is merged into its
  predecessor if that stays within 800 tokens. Each chunk's `section`
  metadata is the join of every H2 heading it spans, so section context
  survives chunk boundaries. A short document (total < 500 tokens)
  yields one undersized chunk — unavoidable, noted rather than padded.
- **Embedding**: `embedder.py` uses `sentence-transformers`
  (`all-MiniLM-L6-v2`), loaded once via `lru_cache`. No external LLM
  API calls.
- **Store**: `vector_store.py` uses a `PersistentClient` at
  `ai/chroma_db/` with cosine distance; `search()` converts Chroma's
  distance to a similarity score (`1 - distance`) and maps results to
  the `KBHit` shape, using each chunk's `title` as `source_doc`.
- **IDs**: `f"{source_path}::{chunk_index}"` — stable across runs as
  long as chunk boundaries for a document don't shift; `chunk.py`'s
  windowing is deterministic for unchanged source content.

## Files

| File | Responsibility |
|---|---|
| `loader.py` | Parse `INDEX.md` manifest + split each doc into H1/H2 sections |
| `chunker.py` | Section-aware 500-800 token chunking with overlap |
| `embedder.py` | sentence-transformers embeddings |
| `vector_store.py` | ChromaDB persistence, idempotent replace-per-doc, top-k search |
| `ingest.py` | CLI entrypoint running the full pipeline |
| `verify_ingestion.py` | Completion-gate proof: totals, per-doc retrieval, flagship query, idempotency |
