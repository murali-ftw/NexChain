"""LLM fallback prompt for intent classification.

Only called when rules.py's fast path returns None (ambiguous query).
Provider-agnostic: plain text in, plain text out — the model is asked
to return exactly one RoutingCategory value, no prose. classifier.py
validates the response against the enum before trusting it.
"""

from __future__ import annotations

_CATEGORY_DEFINITIONS = """KNOWLEDGE_QUERY: the question asks about a policy, procedure, SOP, or "how do we handle X" — answerable only from written policy documents, not data.
DATABASE_QUERY: the question asks about historical/relational data — order status, inventory levels, counts, totals, averages, or filtered/aggregated lists — answerable from the company's relational database.
API_QUERY: the question asks about a shipment's live, real-time physical location or carrier tracking status — not something recorded in the database.
MULTI_TOOL_QUERY: the question needs database data AND live API data together, typically because it asks WHY something is delayed/breached and WHAT action to take, not just its current status."""

_FEW_SHOT = """Examples:
Q: What is the return window for a PLATINUM tier customer?
A: KNOWLEDGE_QUERY

Q: How many orders are currently Delayed?
A: DATABASE_QUERY

Q: Where is tracking number TRK-88213-4 right now?
A: API_QUERY

Q: Where is order SO-45892, why is it delayed, and what should we do?
A: MULTI_TOOL_QUERY"""


def build_prompt(query: str) -> str:
    return (
        "You are the Intent Classifier for NexChain. "
        "Classify the question below into EXACTLY ONE of these four categories.\n\n"
        f"{_CATEGORY_DEFINITIONS}\n\n"
        f"{_FEW_SHOT}\n\n"
        f"Question: {query}\n"
        "Respond with ONLY the category name, nothing else.\n"
        "Category:"
    )
