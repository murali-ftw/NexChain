"""P3.4 completion-gate evaluation.

Runs the curated question set (test_questions.py) through the
Knowledge Base Agent and reports, per question: the answer, the cited
sources, and whether the result counts as a pass (non-empty sources
that actually match the expected document, and the agent didn't
abstain).

Run from repo root:
    python -m ai.agents.knowledge_base_agent.eval

Gate (docs/team_plan.md P3.4): at least 10 of the questions must pass.
"""

from __future__ import annotations

import re
import time
from typing import cast

from ai.agents.knowledge_base_agent.agent import KnowledgeBaseResult, retrieve_and_assemble
from ai.agents.knowledge_base_agent.agent import answer_policy_question
from ai.agents.knowledge_base_agent.test_questions import TEST_QUESTIONS
from ai.contracts import Source
from ai.llm_client import LLMConfigError, LLMProviderError

GATE_THRESHOLD = 10

# Test-harness pacing only (not agent/provider logic — llm_client.py is
# untouched): keeps this eval's sequential LLM calls from tripping
# free-tier rate limits on their own.
SLEEP_BETWEEN_QUESTIONS_SECONDS = 2.5
MAX_RATE_LIMIT_RETRIES = 3
BACKOFF_BASE_SECONDS = 5.0

# llm_client.py wraps provider exceptions into a plain string message, so
# any retry-after hint has to be recovered from that text rather than a
# structured response object. Covers both a raw "Retry-After" style value
# and Gemini's "...Please retry in 28.5s" phrasing.
_RETRY_AFTER_RE = re.compile(r"retry[ _-]?after[\"'\s:]*([\d.]+)", re.IGNORECASE)
_RETRY_IN_RE = re.compile(r"retry in ([\d.]+)", re.IGNORECASE)


def _is_rate_limited(exc: Exception) -> bool:
    text = str(exc)
    return "429" in text or "Too Many Requests" in text or "RESOURCE_EXHAUSTED" in text


def _extract_retry_after_seconds(exc: Exception) -> float | None:
    text = str(exc)
    for pattern in (_RETRY_AFTER_RE, _RETRY_IN_RE):
        match = pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def _answer_with_rate_limit_retry(question: str) -> KnowledgeBaseResult:
    """Retry/backoff wrapper around answer_policy_question, for 429s only.

    Honors a retry-after value parsed out of the provider error text if
    one is present, else falls back to exponential backoff, for a
    bounded number of attempts. Any non-rate-limit failure, or exhausting
    the retries, re-raises so the caller's existing SKIPPED handling
    takes over.
    """
    last_exc: Exception | None = None
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return answer_policy_question(question)
        except (LLMConfigError, LLMProviderError) as exc:
            if not _is_rate_limited(exc) or attempt == MAX_RATE_LIMIT_RETRIES:
                raise
            last_exc = exc
            wait = _extract_retry_after_seconds(exc)
            if wait is None:
                wait = BACKOFF_BASE_SECONDS * (2**attempt)
            print(
                f"  Rate limited (attempt {attempt + 1}/{MAX_RATE_LIMIT_RETRIES}); "
                f"waiting {wait:.1f}s before retry..."
            )
            time.sleep(wait)
    assert last_exc is not None  # loop always returns or raises before falling through
    raise last_exc


def _source_matches(sources: list[Source], expected_keywords: list[str]) -> bool:
    if not sources:
        return False
    haystacks = [f"{s.document_name} {s.snippet or ''}".lower() for s in sources]
    return any(keyword.lower() in haystack for haystack in haystacks for keyword in expected_keywords)


def run() -> None:
    passed = 0
    llm_unavailable = False

    for i, case in enumerate(TEST_QUESTIONS, start=1):
        question = str(case["question"])
        expected_keywords = cast("list[str]", case["expected_doc_keywords"])
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Q: {question}")

        try:
            result: KnowledgeBaseResult = _answer_with_rate_limit_retry(question)
        except (LLMConfigError, LLMProviderError) as exc:
            llm_unavailable = True
            hits, assembled = retrieve_and_assemble(question)
            print(f"  LLM call failed: {exc}")
            print(
                f"  Retrieval/assembly OK without the LLM: {len(hits)} chunk(s) retrieved, "
                f"{len(assembled.used_hits)} source-doc(s) after assembly: "
                f"{[h.source_doc for h in assembled.used_hits]}"
            )
            print("  SKIPPED (needs a working LLM provider to grade pass/fail)")
            if i < len(TEST_QUESTIONS):
                time.sleep(SLEEP_BETWEEN_QUESTIONS_SECONDS)
            continue

        has_sources = bool(result.sources)
        source_ok = _source_matches(result.sources, expected_keywords)
        ok = has_sources and source_ok and not result.abstained

        print(f"  Answer: {result.answer[:300]}")
        print(f"  Sources: {[s.document_name for s in result.sources]}")
        print("  PASS" if ok else "  FAIL")

        if ok:
            passed += 1

        if i < len(TEST_QUESTIONS):
            time.sleep(SLEEP_BETWEEN_QUESTIONS_SECONDS)

    print(f"\n{'=' * 60}")
    if llm_unavailable:
        print(
            "EVAL INCOMPLETE: one or more questions could not be graded because no "
            "working LLM provider is configured.\n"
            "Set LLM_PRIMARY_API_KEY (with LLM_PRIMARY_PROVIDER=gemini and "
            "LLM_PRIMARY_MODEL=<model>) in ai/.env, then re-run:\n"
            "    python -m ai.agents.knowledge_base_agent.eval"
        )
    print(
        f"Gate: {passed}/{len(TEST_QUESTIONS)} questions passed "
        f"(need >= {GATE_THRESHOLD} with a relevant answer + correct source)."
    )
    print("GATE MET" if passed >= GATE_THRESHOLD else "GATE NOT MET")


if __name__ == "__main__":
    run()
