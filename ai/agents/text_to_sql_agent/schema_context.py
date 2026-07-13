"""Compact, prompt-ready schema description for the Text-to-SQL Agent.

Column-level detail isn't in `ai/contracts.py` (that file only owns the
table allowlist), so it's hardcoded here from `db/migrations/001_init_schema.sql`.
The module-level assertion below guards against the two ever drifting apart.
"""

from __future__ import annotations

from ai.contracts import SQL_TABLE_ALLOWLIST

# name -> (columns line, notes line: FK relationships + enum values)
_SCHEMA: dict[str, tuple[str, str]] = {
    "customers": (
        "customer_id PK, customer_code, customer_name, contact_email, "
        "contact_phone, region, sla_tier, created_at",
        "sla_tier in {STANDARD, GOLD, PLATINUM}",
    ),
    "warehouse": (
        "warehouse_id PK, warehouse_code, warehouse_name, location, address, created_at",
        "",
    ),
    "sales_orders": (
        "order_id PK, order_no, customer_id FK->customers, warehouse_id FK->warehouse, "
        "order_date, promised_delivery_date, revised_delivery_date, current_status, "
        "total_amount, created_at, updated_at",
        "current_status in {Pending, Dispatched, In Transit, Delayed, Delivered, Cancelled}",
    ),
    "order_items": (
        "order_item_id PK, order_id FK->sales_orders, sku, product_name, quantity, unit_price",
        "",
    ),
    "inventory": (
        "inventory_id PK, sku, product_name, warehouse_id FK->warehouse, "
        "quantity_on_hand, quantity_reserved, reorder_level, updated_at",
        "",
    ),
    "shipment": (
        "shipment_id PK, order_id FK->sales_orders, tracking_no, carrier_name, "
        "dispatch_date, current_location, shipment_status, delay_reason, created_at, updated_at",
        "shipment_status in {Dispatched, In Transit, Customs Hold, Delivered}",
    ),
    "carrier_tracking": (
        "tracking_event_id PK, shipment_id FK->shipment, event_timestamp, "
        "event_location, event_status, raw_payload",
        "",
    ),
    "invoice": (
        "invoice_id PK, order_id FK->sales_orders, invoice_no, invoice_date, amount, invoice_status",
        "invoice_status in {Draft, Sent, Paid, Overdue}",
    ),
    "payment": (
        "payment_id PK, invoice_id FK->invoice, payment_date, amount_paid, payment_method, payment_status",
        "payment_method in {Bank Transfer, Card, Cheque}; "
        "payment_status in {Pending, Completed, Failed}",
    ),
    "sla_rules": (
        "sla_rule_id PK, sla_tier, max_delay_days, escalation_role, description",
        "sla_tier in {STANDARD, GOLD, PLATINUM}; joins to customers.sla_tier (no FK, match on value)",
    ),
}

assert set(_SCHEMA) == SQL_TABLE_ALLOWLIST, (
    "schema_context._SCHEMA has drifted from ai.contracts.SQL_TABLE_ALLOWLIST"
)


def build_schema_context() -> str:
    """Render the 10 allowlisted tables as compact text for prompting."""
    lines = []
    for table, (columns, notes) in _SCHEMA.items():
        line = f"{table}({columns})"
        if notes:
            line += f"  -- {notes}"
        lines.append(line)
    return "\n".join(lines)
