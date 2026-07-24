"""Curated question set for the P3.7 intent-classifier completion gate.

20 questions, 5 per RoutingCategory. Within each category, most are
phrased so the zero-cost rule fast-path (rules.py) resolves them
directly; exactly one per category is deliberately ambiguous (no
specific order/tracking number, no rule-trigger phrasing) so it falls
through to the LLM fallback — proving that path works too, not just
the rules. A couple of the rule-resolvable ones also use casual/
lowercase phrasing (Day-6 lesson: robustness to real user phrasing).

`expected_category` is graded against `IntentResult.routing_category`
(the RoutingCategory enum value) — the actual routing decision. Which
finer BusinessIntent the rules or LLM picked is reported by eval.py but
not gated on, since several BusinessIntents can share one category.
"""

from __future__ import annotations

TEST_QUESTIONS: list[dict[str, str]] = [
    # --- KNOWLEDGE_QUERY ---
    {
        "question": "What is the SLA policy for GOLD tier customers?",
        "expected_category": "KNOWLEDGE_QUERY",
    },
    {
        "question": "What steps should we follow when a shipment is delayed after dispatch?",
        "expected_category": "KNOWLEDGE_QUERY",
    },
    {
        "question": "How do we handle a payment hold situation?",
        "expected_category": "KNOWLEDGE_QUERY",
    },
    {
        # Ambiguous: no specific order/shipment reference, no rule-trigger
        # phrase ("carrier" alone isn't a shipment-tracking signal) -> LLM.
        "question": "What's our approach when a carrier loses a shipment?",
        "expected_category": "KNOWLEDGE_QUERY",
    },
    {
        "question": (
            "Under what circumstances does force majeure exempt an order "
            "from standard SLA escalation?"
        ),
        "expected_category": "KNOWLEDGE_QUERY",
    },
    # --- DATABASE_QUERY ---
    {
        "question": "How many sales orders are currently Delayed?",
        "expected_category": "DATABASE_QUERY",
    },
    {
        "question": "List all invoices with an Overdue status.",
        "expected_category": "DATABASE_QUERY",
    },
    {
        "question": "What is the total order amount for customer CUST-1002?",
        "expected_category": "DATABASE_QUERY",
    },
    {
        "question": "Which inventory items are below their reorder level?",
        "expected_category": "DATABASE_QUERY",
    },
    {
        # Ambiguous + casual/lowercase: no DB-aggregation trigger word -> LLM.
        "question": "give me a breakdown of orders by status",
        "expected_category": "DATABASE_QUERY",
    },
    # --- API_QUERY ---
    {
        "question": "Where is shipment tracking number TRK-77341-2 right now?",
        "expected_category": "API_QUERY",
    },
    {
        "question": "What is the current location of the shipment for order SO-90210?",
        "expected_category": "API_QUERY",
    },
    {
        "question": "Track my shipment please.",
        "expected_category": "API_QUERY",
    },
    {
        # Ambiguous + casual: no tracking number, no "where is"/"track" -> LLM.
        "question": "Can you tell me where my package is at the moment?",
        "expected_category": "API_QUERY",
    },
    {
        "question": "In transit status for TRK-55210-9?",
        "expected_category": "API_QUERY",
    },
    # --- MULTI_TOOL_QUERY ---
    {
        # Flagship (ai/CONTRACTS.md §9).
        "question": "Where is SO-45892? Why is it delayed and what action should we take?",
        "expected_category": "MULTI_TOOL_QUERY",
    },
    {
        "question": "Is order SO-11223 at risk of breaching its SLA?",
        "expected_category": "MULTI_TOOL_QUERY",
    },
    {
        "question": "Why is shipment TRK-33210-1 delayed and what should we do about it?",
        "expected_category": "MULTI_TOOL_QUERY",
    },
    {
        "question": (
            "What is causing the delay on order SO-22345 and how should we escalate it?"
        ),
        "expected_category": "MULTI_TOOL_QUERY",
    },
    {
        # Ambiguous: no order/tracking number, no rule-trigger phrase -> LLM.
        "question": (
            "My GOLD tier customer's shipment seems stuck — can you look into "
            "what's going on and tell me what we should do?"
        ),
        "expected_category": "MULTI_TOOL_QUERY",
    },
]

GATE_THRESHOLD = 18
