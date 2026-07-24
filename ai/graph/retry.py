"""Shared per-node retry wrapper enforcing MAX_RETRIES_PER_NODE (ai/contracts.py §7).

One retry per node, then the node degrades gracefully (its result field
carries an error) rather than crashing the graph — matching tech-req §7
("report a clear 'service unavailable' status rather than crashing") and
the frozen retry policy. A non-retryable failure (e.g. ToolNotFound — no
such order/tracking number) does not get the second attempt; retrying a
guaranteed failure would just waste the node's one retry.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

from ai.contracts import MAX_RETRIES_PER_NODE
from ai.llm_client import LLMConfigError, LLMProviderError
from ai_service.tools.errors import ToolError

T = TypeVar("T")

_RETRYABLE_EXCEPTIONS = (LLMProviderError, LLMConfigError, ToolError)

# MAX_RETRIES_PER_NODE is 1 (ai/contracts.py) — immediately re-sending into a rate
# limit burns that single retry on a guaranteed second 429 (verified live during
# Day 13 QA: 3 of 4 eval cases hit this exact pattern). A short fixed delay, not a
# full backoff/jitter scheme, is enough to usually clear a per-second rate window.
_RATE_LIMIT_BACKOFF_SECONDS = 2.0


def call_with_retry(
    attempts_before: int, fn: Callable[[], T]
) -> tuple[T | None, str | None, int]:
    """Run fn(), retrying once (MAX_RETRIES_PER_NODE) on a retryable
    failure. Returns (result, error_message, attempts_made) — error_message
    is None on success. ToolError.retryable governs tool failures; LLM
    failures (no such attribute) are treated as transient/retryable.
    """
    attempts = attempts_before
    while True:
        try:
            return fn(), None, attempts
        except _RETRYABLE_EXCEPTIONS as exc:
            retryable = getattr(exc, "retryable", True)
            attempts += 1
            if not retryable or attempts > MAX_RETRIES_PER_NODE:
                message = getattr(exc, "message", None) or str(exc)
                return None, message, attempts
            if getattr(exc, "status_code", None) == 429:
                time.sleep(_RATE_LIMIT_BACKOFF_SECONDS)
