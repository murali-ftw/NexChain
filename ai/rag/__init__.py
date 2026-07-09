"""NexChain RAG ingestion pipeline (P3.3, Day 3).

Parses ai/knowledge_base/, chunks section-aware content, embeds with
sentence-transformers, and persists vectors to a local ChromaDB store.
Retrieval output shape matches the frozen kb_search contract
(ai/contracts.py KBHit: content, source_doc, score).
"""
