"""Curated business-question test set for the P3.5/P3.6 completion gates.

Each case names the table(s) the generated SQL must touch (a subset
check against the actual tables found by `validator.extract_tables`,
not a brittle exact-SQL match — LLM SQL varies). `expects_join` /
`expects_aggregation` are informational only (printed by eval.py, not
gated on) since there are many valid SQL shapes for the same question.

Covers P3.6's stated categories (docs/team_plan.md): filtering,
aggregation, joins, dates, warehouse, and delay queries — plus the
flagship SO-45892 scenario (ai/CONTRACTS.md §9).
"""

from __future__ import annotations

TEST_QUESTIONS: list[dict[str, object]] = [
    # --- basic filters ---
    {
        "question": "List all sales orders with a current status of Delayed.",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
    },
    {
        "question": "Which customers are in the 'APAC' region?",
        "expected_tables": ["customers"],
        "expects_join": False,
        "expects_aggregation": False,
    },
    {
        "question": "Which inventory items have quantity_on_hand below their reorder_level?",
        "expected_tables": ["inventory"],
        "expects_join": False,
        "expects_aggregation": False,
    },
    {
        "question": "List all invoices with an invoice_status of Overdue.",
        "expected_tables": ["invoice"],
        "expects_join": False,
        "expects_aggregation": False,
    },
    {
        "question": "Which payments were made using Bank Transfer?",
        "expected_tables": ["payment"],
        "expects_join": False,
        "expects_aggregation": False,
    },
    {
        "question": "List all shipments currently in Customs Hold.",
        "expected_tables": ["shipment"],
        "expects_join": False,
        "expects_aggregation": False,
    },
    # --- joins ---
    {
        "question": "List customer names along with their order numbers for all Delayed orders.",
        "expected_tables": ["customers", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": False,
    },
    {
        "question": "Show tracking numbers and carrier names for shipments belonging to Cancelled orders.",
        "expected_tables": ["shipment", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": False,
    },
    {
        "question": "List product names and quantities for order SO-45892.",
        "expected_tables": ["order_items", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": False,
    },
    {
        "question": "Show invoice numbers along with the payment status of their payments.",
        "expected_tables": ["invoice", "payment"],
        "expects_join": True,
        "expects_aggregation": False,
    },
    {
        "question": "List each shipment's current location along with its carrier tracking event status.",
        "expected_tables": ["shipment", "carrier_tracking"],
        "expects_join": True,
        "expects_aggregation": False,
    },
    {
        "question": "List sales order numbers along with the name of the warehouse they were shipped from.",
        "expected_tables": ["sales_orders", "warehouse"],
        "expects_join": True,
        "expects_aggregation": False,
    },
    # --- aggregations ---
    {
        "question": "How many sales orders are there for each current_status?",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": True,
    },
    {
        "question": "What is the total order amount per customer?",
        "expected_tables": ["customers", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": True,
    },
    {
        "question": "What is the average delay in days between promised_delivery_date and revised_delivery_date for delayed orders?",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": True,
    },
    {
        "question": "What is the total quantity_on_hand per warehouse?",
        "expected_tables": ["inventory", "warehouse"],
        "expects_join": True,
        "expects_aggregation": True,
    },
    {
        "question": "How many shipments are there for each shipment_status?",
        "expected_tables": ["shipment"],
        "expects_join": False,
        "expects_aggregation": True,
    },
    # --- dates / warehouse / delay ---
    {
        "question": "List all sales orders placed in the last 30 days.",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
    },
    {
        "question": "Which warehouse has dispatched the most sales orders?",
        "expected_tables": ["sales_orders", "warehouse"],
        "expects_join": True,
        "expects_aggregation": True,
    },
    # --- flagship (SO-45892, ai/CONTRACTS.md §9) ---
    {
        "question": (
            "What is order SO-45892's current status, and what is its customer's "
            "SLA tier and the maximum delay days allowed for that tier?"
        ),
        "expected_tables": ["sales_orders", "customers", "sla_rules"],
        "expects_join": True,
        "expects_aggregation": False,
    },
]
