"""P3.5/P3.6 completion-gate evaluation.

Runs the curated question set (test_questions.py) through the
Text-to-SQL Agent and reports, per question: the generated SQL and
whether the result counts as a pass (validator PASS + the expected
tables were touched). There is no live DB (Person 2's MCP `db_query`
is still a stub), so this grades generation + validation correctness,
not execution results.

Run from repo root:
    python -m ai.agents.text_to_sql_agent.eval

Gate (docs/team_plan.md P3.6): at least 15 of the 20 questions must
generate correct, validated SQL. P3.5 owns proving the code-path this
gate measures; live-DB execution is a separate, later verification.
"""

from __future__ import annotations

import re
import time

from ai.agents.text_to_sql_agent.agent import TextToSQLResult, generate_sql
from ai.agents.text_to_sql_agent.test_questions import TEST_QUESTIONS
from ai.llm_client import LLMConfigError, LLMProviderError

GATE_THRESHOLD = 15

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


def _generate_with_rate_limit_retry(question: str) -> TextToSQLResult:
    """Retry/backoff wrapper around generate_sql, for 429s only.

    Honors a retry-after value parsed out of the provider error text if
    one is present, else falls back to exponential backoff, for a
    bounded number of attempts. Any non-rate-limit failure, or exhausting
    the retries, re-raises so the caller's existing SKIPPED handling
    takes over.
    """
    last_exc: Exception | None = None
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return generate_sql(question)
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


def run() -> None:
    passed = 0
    llm_unavailable = False

    for i, case in enumerate(TEST_QUESTIONS, start=1):
        question = str(case["question"])
        expected_tables = set(case["expected_tables"])  # type: ignore[arg-type]
        expects_join = case["expects_join"]
        expects_aggregation = case["expects_aggregation"]
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Q: {question}")

        try:
            result = _generate_with_rate_limit_retry(question)
        except (LLMConfigError, LLMProviderError) as exc:
            llm_unavailable = True
            print(f"  LLM call failed: {exc}")
            print("  SKIPPED (needs a working LLM provider to grade pass/fail)")
            if i < len(TEST_QUESTIONS):
                time.sleep(SLEEP_BETWEEN_QUESTIONS_SECONDS)
            continue

        tables_ok = expected_tables <= set(result.tables)
        ok = result.valid and not result.abstained and tables_ok

        print(f"  SQL: {result.sql}")
        print(
            f"  valid={result.valid} abstained={result.abstained} attempts={result.attempts} "
            f"tables={result.tables} (expected join={expects_join}, aggregation={expects_aggregation})"
        )
        if not result.valid:
            print(f"  reason: {result.reason}")
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
            "    python -m ai.agents.text_to_sql_agent.eval"
        )
    print(
        f"Gate: {passed}/{len(TEST_QUESTIONS)} questions passed "
        f"(need >= {GATE_THRESHOLD} with valid, allowlisted, correctly-tabled SQL)."
    )
    print("GATE MET" if passed >= GATE_THRESHOLD else "GATE NOT MET")


if __name__ == "__main__":
    run()
