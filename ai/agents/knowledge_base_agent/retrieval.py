"""Thin retrieval boundary over the P3.3 vector store.

This is the swap point called out in the P3.4 spec: once Person 2's
`kb_search` MCP tool exists, replace the body of `retrieve()` with an
MCP client call. Its return shape already matches the frozen `KBHit`
contract (ai/contracts.py), so nothing above this function — the agent,
context assembly, or the prompt — needs to change.
"""

from __future__ import annotations

from ai.contracts import KBHit
from ai.rag import vector_store

DEFAULT_TOP_K = 4  # tech-req §6.3 default


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[KBHit]:
    """Top-k semantic retrieval for a natural-language policy question."""
    raw_hits = vector_store.search(query, top_k=top_k)
    return [KBHit(**hit) for hit in raw_hits]
