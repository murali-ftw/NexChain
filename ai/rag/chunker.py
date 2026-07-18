"""Section-aware chunking: 500-800 tokens per chunk with overlap.

Tokens are approximated by whitespace-split word count (no external
tokenizer dependency). Chunking respects paragraph boundaries first,
falling back to sentence boundaries only when a single paragraph alone
exceeds MAX_CHUNK_TOKENS, so a chunk never ends mid-sentence. Each
chunk's `section` metadata is the join of every distinct H2 heading its
content spans (in document order), not just the heading it starts in -
a chunk that crosses a heading boundary must say so, or downstream
citations (P3.4) would attribute content to the wrong section.
Overlap is carried between consecutive chunks of the same document only
and never crosses a document boundary, since chunking runs per-document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai.rag.loader import Document

TARGET_CHUNK_TOKENS = 650
MIN_CHUNK_TOKENS = 500
MAX_CHUNK_TOKENS = 800
OVERLAP_TOKENS = 100

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


@dataclass
class Chunk:
    doc_id: int
    title: str
    section: str
    source_path: str
    chunk_index: int
    content: str


@dataclass
class _Unit:
    text: str
    heading: str
    tokens: int


def _count_tokens(text: str) -> int:
    return len(text.split())


def _join_headings(units: list[_Unit]) -> str:
    """Unique headings spanned by these units, in first-seen order."""
    return " | ".join(dict.fromkeys(u.heading for u in units))


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text.strip()) if p.strip()]


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _build_units(document: Document) -> list[_Unit]:
    """Flatten a document's sections into paragraph-level units, falling
    back to sentence-level units only for paragraphs that alone exceed
    MAX_CHUNK_TOKENS."""
    units: list[_Unit] = []
    for section in document.sections:
        heading = section.heading or document.title
        for paragraph in _split_paragraphs(section.content):
            tokens = _count_tokens(paragraph)
            if tokens <= MAX_CHUNK_TOKENS:
                units.append(_Unit(text=paragraph, heading=heading, tokens=tokens))
            else:
                for sentence in _split_sentences(paragraph):
                    units.append(
                        _Unit(
                            text=sentence,
                            heading=heading,
                            tokens=_count_tokens(sentence),
                        )
                    )
    return units


def chunk_document(document: Document) -> list[Chunk]:
    units = _build_units(document)
    if not units:
        return []

    total_tokens = sum(u.tokens for u in units)

    # Whole document already fits one chunk: don't split it just because
    # it crosses TARGET_CHUNK_TOKENS - a single 500-800 token chunk (or a
    # legitimately shorter document) is the correct output.
    if total_tokens <= MAX_CHUNK_TOKENS:
        return [
            Chunk(
                doc_id=document.doc_id,
                title=document.title,
                section=_join_headings(units),
                source_path=document.source_path,
                chunk_index=0,
                content="\n\n".join(u.text for u in units),
            )
        ]

    # Pre-size chunks so the split is balanced instead of greedily maxing
    # out early chunks and leaving a tiny, sub-MIN final fragment: decide
    # how many chunks we need up front, then give every chunk but the
    # last a target of total/n_chunks tokens. The last chunk absorbs
    # whatever remains, which by construction lands close to the target
    # too.
    n_chunks = max(2, -(-total_tokens // TARGET_CHUNK_TOKENS))  # ceil
    per_chunk_target = max(
        MIN_CHUNK_TOKENS, min(MAX_CHUNK_TOKENS, -(-total_tokens // n_chunks))
    )

    chunks: list[Chunk] = []
    chunk_index = 0
    buffer: list[_Unit] = []
    buffer_tokens = 0
    remaining_chunks = n_chunks

    def flush() -> list[_Unit]:
        nonlocal chunk_index
        content = "\n\n".join(u.text for u in buffer)
        section = _join_headings(buffer)
        chunks.append(
            Chunk(
                doc_id=document.doc_id,
                title=document.title,
                section=section,
                source_path=document.source_path,
                chunk_index=chunk_index,
                content=content,
            )
        )
        chunk_index += 1
        # Carry trailing units worth ~OVERLAP_TOKENS into the next chunk,
        # never crossing into a different document (this function only
        # ever sees one document's units).
        carry: list[_Unit] = []
        carry_tokens = 0
        for u in reversed(buffer):
            if carry_tokens >= OVERLAP_TOKENS:
                break
            carry.insert(0, u)
            carry_tokens += u.tokens
        return carry

    for unit in units:
        # Once only the last chunk remains, stop flushing and let it
        # absorb everything left rather than risk a sub-MIN orphan tail.
        if (
            remaining_chunks > 1
            and buffer
            and buffer_tokens + unit.tokens > MAX_CHUNK_TOKENS
        ):
            carry = flush()
            remaining_chunks -= 1
            buffer = carry
            buffer_tokens = sum(u.tokens for u in buffer)
        buffer.append(unit)
        buffer_tokens += unit.tokens
        if remaining_chunks > 1 and buffer_tokens >= per_chunk_target:
            carry = flush()
            remaining_chunks -= 1
            buffer = carry
            buffer_tokens = sum(u.tokens for u in buffer)

    if buffer:
        flush()

    # Safety net only: if the final chunk still ended up tiny (unit-size
    # distribution defeated the balancing above) and folding it into its
    # predecessor would not blow past MAX_CHUNK_TOKENS, fold it in rather
    # than ship a fragment. Same document only - chunks is entirely this
    # document's chunks at this point.
    if len(chunks) > 1 and _count_tokens(chunks[-1].content) < MIN_CHUNK_TOKENS:
        last = chunks[-1]
        prev = chunks[-2]
        merged_tokens = _count_tokens(prev.content) + _count_tokens(last.content)
        if merged_tokens <= MAX_CHUNK_TOKENS:
            chunks.pop()
            merged_headings = dict.fromkeys(
                prev.section.split(" | ") + last.section.split(" | ")
            )
            chunks[-1] = Chunk(
                doc_id=prev.doc_id,
                title=prev.title,
                section=" | ".join(merged_headings),
                source_path=prev.source_path,
                chunk_index=prev.chunk_index,
                content=prev.content + "\n\n" + last.content,
            )

    return chunks
