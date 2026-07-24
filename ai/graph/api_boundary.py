"""Real MCP boundary over Person 2's operational API tools (P2.8), for
api_status_agent (P3.8). See ai/CONTRACTS.md §11.

No MCP client existed anywhere in this repo until Day 11 (P3.8 Phase 1
cross-check of mcp_server/server.py), so each function here called the same
tool-layer function the real MCP tool calls — ai_service/tools/api_client.py
— directly. That placeholder is resolved: these now go through a real
ClientSession over MCP (ai/mcp_client.py); api_status_agent does not need to
change, exactly the pattern text_to_sql_agent/db_boundary.py already
established for db_query.
"""

from __future__ import annotations

from ai import mcp_client
from ai.contracts import InventoryRecord, OrderStatus, ShipmentStatus


def get_shipment_status(tracking_no: str) -> ShipmentStatus:
    """Raises ai_service.tools.errors.ToolError on failure."""
    return ShipmentStatus(
        **mcp_client.call_tool("get_shipment_status", {"tracking_no": tracking_no})
    )


def get_order_status(order_no: str) -> OrderStatus:
    """Raises ai_service.tools.errors.ToolError on failure.

    Not reached by any current INTENT_TO_ROUTING mapping (order_status is
    DATABASE_QUERY, not API_QUERY) — wired for when business_rule_agent
    (Day 10) needs the ERP's live view alongside the DB's get_order
    (ai/CONTRACTS.md §5 notes these are deliberately different systems).
    """
    return OrderStatus(
        **mcp_client.call_tool("get_order_status", {"order_no": order_no})
    )


def get_inventory(sku: str) -> InventoryRecord:
    """Raises ai_service.tools.errors.ToolError on failure.

    Not reached by any current INTENT_TO_ROUTING mapping either (inventory
    is DATABASE_QUERY) — wired for parity with the other two API tools.
    """
    return InventoryRecord(**mcp_client.call_tool("get_inventory", {"sku": sku}))
