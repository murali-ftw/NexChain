"""Curated policy-question test set for the P3.4 completion gate.

Each case names keyword(s) expected to appear in the *cited source*
(document name or snippet) if the agent retrieved the right document —
this is what eval.py checks in addition to "sources non-empty", so a
source that merely exists but is off-topic still fails.

Covers: SLA tiers, general shipment delay, customs hold / HS code
mismatch (flagship), inventory shortage, escalation, customer
notification, payment hold, carrier delay, warehouse delay, order
amendment/cancellation, returns/RMA, and force majeure — i.e. all 12
documents in ai/knowledge_base/INDEX.md.
"""

from __future__ import annotations

TEST_QUESTIONS: list[dict[str, object]] = [
    {
        "question": "What is the maximum delay allowed before an order breaches SLA for a GOLD tier customer?",
        "expected_doc_keywords": ["SLA Policy"],
    },
    {
        # Flagship (SO-45892): must cite the Customs Hold SOP.
        "question": "What should we do when an order is held at customs for an HS code mismatch?",
        "expected_doc_keywords": ["Customs Hold"],
    },
    {
        "question": "What steps should we follow when a shipment is delayed after it has been dispatched?",
        "expected_doc_keywords": ["Shipment Delay"],
    },
    {
        "question": "How do we handle an order that cannot be fulfilled due to insufficient inventory on hand?",
        "expected_doc_keywords": ["Inventory Shortage"],
    },
    {
        "question": "Who should an At Risk order be escalated to, and how quickly should they respond?",
        "expected_doc_keywords": ["Escalation Matrix"],
    },
    {
        "question": "How and when should a customer be notified if their order's SLA has been breached?",
        "expected_doc_keywords": ["Customer Notification"],
    },
    {
        "question": "What happens to an order's SLA clock while payment is on hold?",
        "expected_doc_keywords": ["Payment Hold"],
    },
    {
        "question": "What is the procedure when a carrier loses a shipment in transit?",
        "expected_doc_keywords": ["Carrier Delay"],
    },
    {
        "question": "What causes warehouse-side fulfillment delays and how are they resolved?",
        "expected_doc_keywords": ["Warehouse Delay"],
    },
    {
        "question": "Within what window can a customer amend or cancel an order after it is placed?",
        "expected_doc_keywords": ["Order Amendment"],
    },
    {
        "question": "What is the return window for a PLATINUM tier customer under the RMA policy?",
        "expected_doc_keywords": ["Returns"],
    },
    {
        "question": "Which disruption events qualify as force majeure and exempt an order from standard SLA escalation?",
        "expected_doc_keywords": ["Force Majeure"],
    },
    {
        "question": "What is the difference between an At Risk and a Breached SLA status?",
        "expected_doc_keywords": ["SLA Policy"],
    },
]
