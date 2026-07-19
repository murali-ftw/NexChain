"""Real MCP boundary over the database tools (ai/CONTRACTS.md §11).

This was the swap point called out in the P3.5 spec: Person 2's MCP db_query
tool (P2.8, mcp_server/server.py) existed but no MCP client existed anywhere
in this repo, so db_query called the tool-layer function the MCP server
itself calls (ai_service/tools/db.py: run_select) directly. Day 11 resolved
that placeholder — this now goes through a real ClientSession over MCP
(ai/mcp_client.py); nothing above this function — the agent, validator, or
the prompt — needed to change.

get_order (Day 12) closes the one gap Day 11 left: ai/graph/nodes.py was
still importing ai_service.tools.db.get_order directly, bypassing this
boundary entirely — the one MCP tool call in the graph that never went
through mcp_client. Routed the same way as db_query now.

resolve_tracking_no is a fixed lookup, not one of the frozen MCP tools
(§11), so it still calls run_select directly, same as before.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from ai import mcp_client
from ai.agents.text_to_sql_agent.validator import validate_sql
from ai.contracts import DBResult
from ai_service.tools.db import run_select
from ai_service.tools.errors import ToolError, ToolNotFound

logger = logging.getLogger(__name__)

_ORDER_DATE_FIELDS = ("order_date", "promised_delivery_date", "revised_delivery_date")


def db_query(sql: str) -> DBResult:
    """Execute already-validated SELECT SQL against the live database, via
    the MCP db_query tool.

    Re-validates (P2.9) as defense in depth even though the only current
    caller (text_to_sql_agent_node) already passes generate_sql()'s own
    safe_sql — so a future caller can never reach the database with
    unvalidated SQL through this boundary either, and a malformed query
    never even crosses the wire to the MCP server.

    Raises ai_service.tools.errors.ToolError (via mcp_client, or directly on
    validation failure) on failure — callers (the text_to_sql_agent graph
    node) handle retry/error routing.
    """
    validation = validate_sql(sql)
    if not validation.valid or not validation.safe_sql:
        logger.warning(
            "tool=db_query status=rejected sql=%s reason=%s", sql, validation.reason
        )
        raise ToolError(
            "db_query",
            f"rejected: {validation.reason}",
            retryable=False,
            status_code=400,
        )
    return DBResult(**mcp_client.call_tool("db_query", {"sql": validation.safe_sql}))


def get_order(order_no: str) -> dict[str, Any] | None:
    """The order as the system of record holds it — customer, warehouse,
    SLA tier and dates — via the MCP get_order tool.

    ai_service/tools/db.py:get_order() returns None for an unknown order;
    the MCP tool converts that into a ToolNotFound (mcp_server/server.py) so
    it crosses the wire as a controlled error rather than an empty success.
    Converted back to None here so business_rule_agent_node's existing
    `order is None` -> "not applicable, not an error" handling
    (ai/graph/nodes.py) doesn't need to change.

    db.get_order() returns date columns as real `date` objects (psycopg,
    in-process); MCP JSON-serializes everything, so the same fields come
    back as ISO strings (mcp_server/test_server.py asserts exactly that:
    `order["promised_delivery_date"] == "2026-07-03"`). Parsed back to
    `date` here — business_rule_agent_node does `date - date` arithmetic
    on these (rules.py:compute_delay_days) and would otherwise TypeError
    on `str - str`.

    Raises ai_service.tools.errors.ToolError for anything else (e.g. a
    retryable database-unavailable failure) — callers handle retry/error
    routing exactly as they did calling db.get_order() directly.
    """
    try:
        order = mcp_client.call_tool("get_order", {"order_no": order_no})
    except ToolNotFound:
        return None
    for field in _ORDER_DATE_FIELDS:
        value = order.get(field)
        if isinstance(value, str):
            order[field] = datetime.date.fromisoformat(value)
    return order


def resolve_tracking_no(order_no: str) -> str | None:
    """Order number -> its shipment's tracking number, straight from the
    live DB (sales_orders -> shipment). The P3.9 cross-reference
    api_status_agent needs when a query gives an order number but no
    tracking number (ai/graph/entities.py) — a fixed lookup, not
    LLM-generated SQL, same pattern as ai_service/tools/db.py:get_order().

    Raises ai_service.tools.errors.ToolError (via run_select) on failure.
    Returns None if the order has no shipment yet.

    order_id has no UNIQUE constraint on shipment (db/06_backend_schema.md),
    so a re-ship or duplicate row is possible; ORDER BY shipment_id DESC
    picks the most recent shipment deterministically instead of whatever
    row the database happens to return first.
    """
    rows = run_select(
        "SELECT tracking_no FROM shipment WHERE order_id = "
        "(SELECT order_id FROM sales_orders WHERE order_no = %s) "
        "ORDER BY shipment_id DESC",
        (order_no,),
    )
    return rows[0]["tracking_no"] if rows else None
