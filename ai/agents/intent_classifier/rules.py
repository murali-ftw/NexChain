"""Deterministic keyword/pattern rules for the intent classifier's fast path.

Pure, no API calls. Returns a BusinessIntent when a query's signal is
unambiguous, or None to fall through to the LLM (classifier.py). Order
matters: multi-tool signals are checked first, since a query can
superficially look single-source ("where is SO-45892") while actually
needing "why + what action" (delay_analysis) or an SLA/breach check.

Matching is lowercase/substring-based, so casual phrasing and casing
("show me delayed orders" vs "Delayed") are handled without needing an
LLM call.
"""

from __future__ import annotations

import re

from ai.contracts import BusinessIntent

_ORDER_NO_RE = re.compile(r"\bso[\s-]\d+\b", re.IGNORECASE)
_TRACKING_NO_RE = re.compile(r"\btrk-[\w-]+\b", re.IGNORECASE)

_REASON_ACTION_WORDS = (
    "why",
    "reason",
    "what should we do",
    "what action",
    "recommended action",
    "what do we do",
    "root cause",
)
_SLA_WORDS = ("sla", "breach", "breached", "at risk", "escalat")
# Deliberately NOT the bare words "order"/"shipment" — a general policy
# question ("does force majeure exempt an order from SLA escalation")
# mentions those words too without referencing any specific, concrete
# order. The multi-tool gate needs a concrete reference: an actual
# order/tracking number, or a deictic phrase pointing at one case.
_SPECIFIC_REFERENCE_WORDS = (
    "this order",
    "my order",
    "our order",
    "the order",
    "this shipment",
    "my shipment",
    "our shipment",
    "the shipment",
)

_SOP_WORDS = (
    "policy",
    "procedure",
    "sop",
    "how do we handle",
    "how should we",
    "escalat",
    "notify",
    "notification",
    "rma",
    "return window",
    "force majeure",
    "what steps",
)

_SHIPMENT_WORDS = ("where is", "current location", "track", "in transit")

_DB_AGG_WORDS = (
    "how many",
    "total",
    "average",
    "list all",
    "list",
    "show me",
    "show all",
    "which customers",
    "which orders",
    "which invoices",
    "which payments",
)

_INVENTORY_WORDS = ("inventory", "stock", "reorder", "quantity_on_hand", "sku")


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(w in text for w in words)


def classify_by_rules(query: str) -> BusinessIntent | None:
    """Deterministic fast-path. Returns None if the query is ambiguous."""
    text = query.lower()

    has_status_ref = bool(
        _ORDER_NO_RE.search(query) or _TRACKING_NO_RE.search(query)
    ) or _contains_any(text, _SPECIFIC_REFERENCE_WORDS)
    has_reason_or_action = _contains_any(text, _REASON_ACTION_WORDS)
    has_sla = _contains_any(text, _SLA_WORDS)

    if has_status_ref and (has_reason_or_action or has_sla):
        return (
            BusinessIntent.DELAY_ANALYSIS
            if has_reason_or_action
            else BusinessIntent.SLA_CHECK
        )

    if _contains_any(text, _SOP_WORDS):
        return BusinessIntent.SOP_LOOKUP

    if _TRACKING_NO_RE.search(query) or _contains_any(text, _SHIPMENT_WORDS):
        return BusinessIntent.SHIPMENT_STATUS

    if (
        _ORDER_NO_RE.search(query)
        or "order status" in text
        or "status of order" in text
    ):
        return BusinessIntent.ORDER_STATUS

    if _contains_any(text, _INVENTORY_WORDS):
        return BusinessIntent.INVENTORY

    if _contains_any(text, _DB_AGG_WORDS):
        return BusinessIntent.REPORT

    return None
