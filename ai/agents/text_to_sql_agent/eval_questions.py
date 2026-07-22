"""Curated business-question test set for the P3.5/P3.6 completion gates.

Each case names the table(s) the generated SQL must touch (a subset
check against the actual tables found by `validator.extract_tables`,
not a brittle exact-SQL match — LLM SQL varies). `expects_join` /
`expects_aggregation` are informational only (printed by eval.py, not
gated on) since there are many valid SQL shapes for the same question.
`category` drives eval.py's per-category breakdown.

The first 20 entries are the original P3.5 baseline (unchanged) that
the P3.6 gate (docs/team_plan.md: >= 15/20) is measured against. The
remaining 10 (Day 6) deliberately stress-test the categories the
baseline under-covered: date arithmetic, multi-table warehouse joins,
and the canonical SLA-breach delay computation
(docs/06_backend_schema.md §6: CURRENT_DATE - promised_delivery_date
vs a tier's max_delay_days, joined through sales_orders -> customers ->
sla_rules), plus GROUP BY/HAVING, NULL handling on the nullable
revised_delivery_date, and enum-casing robustness.
"""

from __future__ import annotations

TEST_QUESTIONS: list[dict[str, object]] = [
    # --- basic filters ---
    {
        "question": "List all sales orders with a current status of Delayed.",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "filter",
    },
    {
        "question": "Which customers are in the 'APAC' region?",
        "expected_tables": ["customers"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "filter",
    },
    {
        "question": "Which inventory items have quantity_on_hand below their reorder_level?",
        "expected_tables": ["inventory"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "filter",
    },
    {
        "question": "List all invoices with an invoice_status of Overdue.",
        "expected_tables": ["invoice"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "filter",
    },
    {
        "question": "Which payments were made using Bank Transfer?",
        "expected_tables": ["payment"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "filter",
    },
    {
        "question": "List all shipments currently in Customs Hold.",
        "expected_tables": ["shipment"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "filter",
    },
    # --- joins ---
    {
        "question": "List customer names along with their order numbers for all Delayed orders.",
        "expected_tables": ["customers", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "join",
    },
    {
        "question": "Show tracking numbers and carrier names for shipments belonging to Cancelled orders.",
        "expected_tables": ["shipment", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "join",
    },
    {
        "question": "List product names and quantities for order SO-45892.",
        "expected_tables": ["order_items", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "join",
    },
    {
        "question": "Show invoice numbers along with the payment status of their payments.",
        "expected_tables": ["invoice", "payment"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "join",
    },
    {
        "question": "List each shipment's current location along with its carrier tracking event status.",
        "expected_tables": ["shipment", "carrier_tracking"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "join",
    },
    {
        "question": "List sales order numbers along with the name of the warehouse they were shipped from.",
        "expected_tables": ["sales_orders", "warehouse"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "join",
    },
    # --- aggregations ---
    {
        "question": "How many sales orders are there for each current_status?",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": True,
        "category": "aggregation",
    },
    {
        "question": "What is the total order amount per customer?",
        "expected_tables": ["customers", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": True,
        "category": "aggregation",
    },
    {
        "question": "What is the average delay in days between promised_delivery_date and revised_delivery_date for delayed orders?",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": True,
        "category": "delay",
    },
    {
        "question": "What is the total quantity_on_hand per warehouse?",
        "expected_tables": ["inventory", "warehouse"],
        "expects_join": True,
        "expects_aggregation": True,
        "category": "warehouse",
    },
    {
        "question": "How many shipments are there for each shipment_status?",
        "expected_tables": ["shipment"],
        "expects_join": False,
        "expects_aggregation": True,
        "category": "aggregation",
    },
    # --- dates / warehouse / delay ---
    {
        "question": "List all sales orders placed in the last 30 days.",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "date",
    },
    {
        "question": "Which warehouse has dispatched the most sales orders?",
        "expected_tables": ["sales_orders", "warehouse"],
        "expects_join": True,
        "expects_aggregation": True,
        "category": "warehouse",
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
        "category": "flagship",
    },
    # ============================================================
    # Day 6 (P3.6) — hard/expanded set: dates, warehouse, delay,
    # NULL handling, HAVING, and enum-casing robustness.
    # ============================================================
    # --- date arithmetic ---
    {
        "question": "Which sales orders were promised for delivery in the last 30 days?",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "date",
    },
    {
        "question": (
            "Which orders had their revised delivery date slip more than 5 days "
            "past the promised delivery date?"
        ),
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "date",
    },
    {
        "question": "List shipments dispatched between 2026-06-01 and 2026-06-30.",
        "expected_tables": ["shipment"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "date",
    },
    # --- multi-table warehouse joins ---
    {
        "question": "For each warehouse, how many distinct SKUs are below their reorder_level?",
        "expected_tables": ["inventory", "warehouse"],
        "expects_join": True,
        "expects_aggregation": True,
        "category": "warehouse",
    },
    {
        "question": (
            "Which warehouse has the most sales orders that are either Delayed or "
            "have a shipment currently in Customs Hold?"
        ),
        "expected_tables": ["warehouse", "sales_orders", "shipment"],
        "expects_join": True,
        "expects_aggregation": True,
        "category": "warehouse",
    },
    # --- canonical SLA-breach delay computation (docs/06_backend_schema.md §6) ---
    {
        "question": (
            "Which orders are currently in SLA breach — where today's date minus the "
            "promised delivery date exceeds the customer's SLA tier's maximum delay days?"
        ),
        "expected_tables": ["sales_orders", "customers", "sla_rules"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "delay",
    },
    {
        "question": (
            "List orders that are At Risk — delayed past their promised delivery date "
            "but not yet past their SLA tier's maximum delay days."
        ),
        "expected_tables": ["sales_orders", "customers", "sla_rules"],
        "expects_join": True,
        "expects_aggregation": False,
        "category": "delay",
    },
    {
        "question": "Which orders have no revised delivery date recorded yet?",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "delay",
    },
    # --- tricky: HAVING + casing robustness ---
    {
        "question": "Which GOLD tier customers have at least 2 Delayed orders?",
        "expected_tables": ["customers", "sales_orders"],
        "expects_join": True,
        "expects_aggregation": True,
        "category": "tricky",
    },
    {
        "question": "Show all orders that are delayed.",
        "expected_tables": ["sales_orders"],
        "expects_join": False,
        "expects_aggregation": False,
        "category": "tricky",
    },
]

# The P3.6 gate (docs/team_plan.md: >= 15 of "the 20 predefined questions")
# is measured against this original baseline slice, preserved in place as
# the first 20 entries above. Everything after it is Day 6's hard expansion.
GATE_BASELINE_COUNT = 20
GATE_THRESHOLD = 15
