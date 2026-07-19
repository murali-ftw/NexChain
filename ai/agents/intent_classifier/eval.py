"""P3.7 completion-gate evaluation.

Runs the curated question set (test_questions.py) through the intent
classifier and reports, per question: expected vs actual
RoutingCategory, which layer resolved it (rules/LLM), and whether it
counts as a pass. Only ambiguous questions ever reach the LLM — rule-
resolved questions cost zero API calls, so a full run of 20 questions
should make far fewer than 20 calls.

Run from repo root:
    python -m ai.agents.intent_classifier.eval
    python -m ai.agents.intent_classifier.eval --ids 4,10,14,20   # targeted re-run

Gate (docs/team_plan.md P3.7): at least 18 of 20 questions must route
to the correct RoutingCategory.
"""

from __future__ import annotations

import argparse
import re
import time

from ai.agents.intent_classifier.classifier import IntentResult, classify
from ai.agents.intent_classifier.test_questions import GATE_THRESHOLD, TEST_QUESTIONS

SLEEP_BETWEEN_LLM_CALLS_SECONDS = 2.5
MAX_RATE_LIMIT_RETRIES = 3
BACKOFF_BASE_SECONDS = 5.0

_RETRY_AFTER_RE = re.compile(r"retry[ _-]?after[\"'\s:]*([\d.]+)", re.IGNORECASE)
_RETRY_IN_RE = re.compile(r"retry in ([\d.]+)", re.IGNORECASE)


def _is_rate_limited(text: str) -> bool:
    return "429" in text or "Too Many Requests" in text or "RESOURCE_EXHAUSTED" in text


def _extract_retry_after_seconds(text: str) -> float | None:
    for pattern in (_RETRY_AFTER_RE, _RETRY_IN_RE):
        match = pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def _classify_with_rate_limit_retry(question: str) -> IntentResult:
    """classify() never raises — LLM failures come back as IntentResult.error
    — so retry-on-429 has to inspect the returned error text and re-call,
    rather than catching an exception like the KB/SQL agents' evals do."""
    result = classify(question)
    for attempt in range(MAX_RATE_LIMIT_RETRIES):
        if (
            result.resolved_by != "llm"
            or not result.error
            or not _is_rate_limited(result.error)
        ):
            return result
        wait = _extract_retry_after_seconds(result.error)
        if wait is None:
            wait = BACKOFF_BASE_SECONDS * (2**attempt)
        print(
            f"  Rate limited (attempt {attempt + 1}/{MAX_RATE_LIMIT_RETRIES}); "
            f"waiting {wait:.1f}s before retry..."
        )
        time.sleep(wait)
        result = classify(question)
    return result


def run(only_ids: set[int] | None = None) -> None:
    """Run the eval. `only_ids` (1-based question numbers) restricts the run
    to a subset, for cheap targeted re-runs after a rules/prompt fix."""
    cases = (
        list(enumerate(TEST_QUESTIONS, start=1))
        if only_ids is None
        else [(i, c) for i, c in enumerate(TEST_QUESTIONS, start=1) if i in only_ids]
    )
    total_run = len(cases)
    passed = 0
    rules_count = 0
    llm_count = 0
    category_stats: dict[str, list[int]] = {}

    for n, (i, case) in enumerate(cases, start=1):
        question = case["question"]
        expected = case["expected_category"]
        print(f"\n[{n}/{total_run}] (#{i}) Q: {question}")

        result = _classify_with_rate_limit_retry(question)
        resolved_by_llm = result.resolved_by == "llm"
        if resolved_by_llm:
            llm_count += 1
        else:
            rules_count += 1

        actual = result.routing_category.value if result.routing_category else None
        ok = actual == expected

        print(
            f"  resolved_by={result.resolved_by} intent={result.intent} routing_category={actual}"
        )
        if result.error:
            print(f"  error: {result.error}")
        print("  PASS" if ok else f"  FAIL (expected {expected}, got {actual})")

        stats = category_stats.setdefault(expected, [0, 0])
        stats[1] += 1
        if ok:
            passed += 1
            stats[0] += 1

        if resolved_by_llm and n < total_run:
            time.sleep(SLEEP_BETWEEN_LLM_CALLS_SECONDS)

    print(f"\n{'=' * 60}")
    print("Per-category breakdown:")
    for category in sorted(category_stats):
        cat_passed, cat_total = category_stats[category]
        print(f"  {category:18} {cat_passed}/{cat_total}")

    print(f"\nOverall: {passed}/{total_run} passed this run.")
    print(
        f"Resolved by rules (0 API calls): {rules_count}. Resolved by LLM: {llm_count}."
    )
    if only_ids is None:
        print(f"Gate: {passed}/{len(TEST_QUESTIONS)} (need >= {GATE_THRESHOLD})")
        print("GATE MET" if passed >= GATE_THRESHOLD else "GATE NOT MET")


def _parse_ids(raw: str) -> set[int]:
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help="Comma-separated 1-based question numbers to re-run (e.g. 4,10,14,20). "
        "Omit to run the full set.",
    )
    args = parser.parse_args()
    run(only_ids=_parse_ids(args.ids) if args.ids else None)
