"""Thin boundary over the live database, via Person 2's tool layer.

This is the swap point called out in the P3.5 spec. Person 2's MCP
db_query tool (P2.8, mcp_server/server.py) now exists, but no MCP client
exists anywhere in this repo yet (P3.8 Phase 1 cross-check) — so this
calls the same tool-layer function the MCP server itself calls
(ai_service/tools/db.py: run_select), the identical code path per that
module's own docstring. When a real MCP ClientSession exists
project-wide, replace the body below with that call; nothing above this
function — the agent, validator, or the prompt — needs to change.
"""

from __future__ import annotations

from pydantic_core import to_jsonable_python

from ai.contracts import DBResult
from ai_service.tools.db import run_select


def db_query(sql: str) -> DBResult:
    """Execute already-validated SELECT SQL against the live database.

    Raises ai_service.tools.errors.ToolError (via run_select) on failure —
    callers (the text_to_sql_agent graph node) handle retry/error routing.
    """
    return DBResult(rows=to_jsonable_python(run_select(sql)))


def resolve_tracking_no(order_no: str) -> str | None:
    """Order number -> its shipment's tracking number, straight from the
    live DB (sales_orders -> shipment). The P3.9 cross-reference
    api_status_agent needs when a query gives an order number but no
    tracking number (ai/graph/entities.py) — a fixed lookup, not
    LLM-generated SQL, same pattern as ai_service/tools/db.py:get_order().

    Raises ai_service.tools.errors.ToolError (via run_select) on failure.
    Returns None if the order has no shipment yet.
    """
    rows = run_select(
        "SELECT tracking_no FROM shipment WHERE order_id = "
        "(SELECT order_id FROM sales_orders WHERE order_no = %s)",
        (order_no,),
    )
    return rows[0]["tracking_no"] if rows else None
