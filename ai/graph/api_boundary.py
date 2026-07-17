"""Thin boundary over Person 2's operational API tools (P2.8), for
api_status_agent (P3.8).

No MCP client exists anywhere in this repo yet (P3.8 Phase 1 cross-check
of mcp_server/server.py). Each function here calls the same tool-layer
function the real MCP tool calls — ai_service/tools/api_client.py — the
identical code path per that module's docstring. When a real MCP
ClientSession exists project-wide, replace these bodies with that call;
api_status_agent does not need to change, exactly the pattern
text_to_sql_agent/db_boundary.py already established for db_query.
"""

from __future__ import annotations

from ai.contracts import InventoryRecord, OrderStatus, ShipmentStatus
from ai_service.tools import api_client


def get_shipment_status(tracking_no: str) -> ShipmentStatus:
    """Raises ai_service.tools.errors.ToolError on failure."""
    return api_client.get_shipment_status(tracking_no)


def get_order_status(order_no: str) -> OrderStatus:
    """Raises ai_service.tools.errors.ToolError on failure.

    Not reached by any current INTENT_TO_ROUTING mapping (order_status is
    DATABASE_QUERY, not API_QUERY) — wired for when business_rule_agent
    (Day 10) needs the ERP's live view alongside the DB's get_order
    (ai/CONTRACTS.md §5 notes these are deliberately different systems).
    """
    return api_client.get_order_status(order_no)


def get_inventory(sku: str) -> InventoryRecord:
    """Raises ai_service.tools.errors.ToolError on failure.

    Not reached by any current INTENT_TO_ROUTING mapping either (inventory
    is DATABASE_QUERY) — wired for parity with the other two API tools.
    """
    return api_client.get_inventory(sku)
