"""Minimal identifier extraction from natural-language queries.

No entity-extraction agent exists yet (not assigned to any P3.x day) —
api_status_agent still needs a concrete tracking number to call a tool
with. These reuse the same order/tracking-number patterns
intent_classifier/rules.py already uses to *detect* a reference (SO-####,
TRK-####-#), just to *extract* the value instead. Sufficient for the
flagship demo shape; not a general NLU solution — cross-referencing a bare
order number to its shipment's tracking number (when the query only gives
"SO-45892", not a tracking number) is P3.9 (Day 9) multi-agent
integration, not this module.
"""

from __future__ import annotations

import re

_ORDER_NO_RE = re.compile(r"\b(so)[\s-](\d+)\b", re.IGNORECASE)
_TRACKING_NO_RE = re.compile(r"\b(trk-[\w-]+)\b", re.IGNORECASE)


def extract_order_no(text: str) -> str | None:
    # Normalizes "so 45892" to "SO-45892" (canonical, hyphenated form the DB
    # actually stores) — matching intent_classifier/rules.py's wider detection
    # regex here without normalizing would let routing recognize the order
    # reference while every downstream lookup still misses on the raw text.
    match = _ORDER_NO_RE.search(text)
    return f"{match.group(1)}-{match.group(2)}".upper() if match else None


def extract_tracking_no(text: str) -> str | None:
    match = _TRACKING_NO_RE.search(text)
    return match.group(1).upper() if match else None
