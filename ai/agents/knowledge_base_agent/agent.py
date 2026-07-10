"""P3.4 Knowledge Base Agent.

Pipeline: semantic retrieval -> context assembly -> grounded answer
generation -> sourced result. Returns a plain result object; the
LangGraph node that drops this into CoPilotState.kb_result is P3.8,
not this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.agents.knowledge_base_agent.prompts import NO_EVIDENCE_ANSWER, build_prompt
from ai.agents.knowledge_base_agent.retrieval import DEFAULT_TOP_K, retrieve
from ai.contracts import KBHit, Source
from ai.llm_client import generate

# Token budget for assembled context (whitespace-word count, matching the
# approximation ai/rag/chunker.py already uses for the same purpose — no
# extra tokenizer dependency). At the default top_k=4 with 500-800 token
# chunks, retrieval alone can return ~2000-3200 tokens, so this budget is
# tight enough to actually exercise the truncation path.
MAX_CONTEXT_TOKENS = 1800

# Sources carry a short excerpt, not the full chunk.
SNIPPET_CHARS = 280


def _count_tokens(text: str) -> int:
    return len(text.split())


@dataclass
class AssembledContext:
    text: str
    used_hits: list[KBHit] = field(default_factory=list)


def assemble_context(hits: list[KBHit], max_tokens: int = MAX_CONTEXT_TOKENS) -> AssembledContext:
    """Merge same-document chunks, drop exact duplicates, and cap the
    result to a token budget by keeping the highest-scoring documents
    first (truncating the last one included if it would overflow)."""
    if not hits:
        return AssembledContext(text="", used_hits=[])

    groups: dict[str, list[KBHit]] = {}
    for hit in hits:
        groups.setdefault(hit.source_doc, []).append(hit)

    merged: list[KBHit] = []
    for source_doc, doc_hits in groups.items():
        ranked = sorted(doc_hits, key=lambda h: -h.score)
        seen_content: list[str] = []
        for h in ranked:
            if h.content not in seen_content:
                seen_content.append(h.content)
        merged.append(
            KBHit(
                content="\n\n".join(seen_content),
                source_doc=source_doc,
                score=ranked[0].score,
            )
        )
    merged.sort(key=lambda h: -h.score)

    blocks: list[str] = []
    used_hits: list[KBHit] = []
    total_tokens = 0
    for hit in merged:
        block = f"[Source: {hit.source_doc}]\n{hit.content}"
        block_tokens = _count_tokens(block)

        if total_tokens + block_tokens > max_tokens:
            remaining = max_tokens - total_tokens
            if remaining < 20:  # not enough room left for a meaningful excerpt
                break
            words = block.split()[:remaining]
            blocks.append(" ".join(words) + " ...[truncated]")
            used_hits.append(hit)
            break

        blocks.append(block)
        used_hits.append(hit)
        total_tokens += block_tokens

    return AssembledContext(text="\n\n---\n\n".join(blocks), used_hits=used_hits)


@dataclass
class KnowledgeBaseResult:
    answer: str
    sources: list[Source]
    abstained: bool = False


def retrieve_and_assemble(
    question: str, top_k: int = DEFAULT_TOP_K
) -> tuple[list[KBHit], AssembledContext]:
    """Retrieval + assembly only, exposed separately so callers (eval.py)
    can verify this half of the pipeline even if the LLM call fails."""
    hits = retrieve(question, top_k=top_k)
    assembled = assemble_context(hits)
    return hits, assembled


def answer_policy_question(question: str, top_k: int = DEFAULT_TOP_K) -> KnowledgeBaseResult:
    """Answer a natural-language policy question, grounded only in
    retrieved knowledge-base context, with sources preserved.

    If retrieval finds nothing relevant, the agent abstains explicitly
    rather than fabricating an answer — an empty source list is only
    ever paired with `abstained=True`.
    """
    hits, assembled = retrieve_and_assemble(question, top_k=top_k)
    if not hits:
        return KnowledgeBaseResult(answer=NO_EVIDENCE_ANSWER, sources=[], abstained=True)

    prompt = build_prompt(question, assembled.text)
    answer_text = generate(prompt)

    sources = [
        Source(
            document_name=hit.source_doc,
            snippet=hit.content[:SNIPPET_CHARS].strip(),
            score=hit.score,
        )
        for hit in assembled.used_hits
    ]
    return KnowledgeBaseResult(answer=answer_text.strip(), sources=sources, abstained=False)
