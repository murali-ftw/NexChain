"""P2.7 MCP server — standardized database access for the AI layer (Day 7).

The independent tool process tech-req §4.2 requires: Person 3's agents never
touch psycopg or HTTP, they call MCP tools, and this is the server behind them.
Today it exposes the two database tools (P2.7); the three API tools
(`get_order_status`, `get_shipment_status`, `get_inventory`) land at P2.8 and
their tool-layer functions already exist in ai_service/tools/api_client.py.

The tools are thin on purpose. All real work — connection handling, and the
normalization of every failure to ToolError — lives in ai_service/tools/, so
the same code path is exercised whether you go through MCP or import the tool
layer directly in a test.

Run it:

    .venv/bin/python -m mcp_server.server                      # stdio (default)
    MCP_TRANSPORT=streamable-http .venv/bin/python -m mcp_server.server   # port 8002

# ponytail: SELECT-only parsing, the table allowlist and row limits are P2.9
# (Day 9) — until then `db_query` executes what it is given and the
# copilot_readonly grant (db/migrations/002_roles.sh) is the only thing
# stopping a bad query. It cannot write, and cannot read users or audit_log at
# all, so the blast radius is "reads a table it didn't need to", not damage.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic_core import to_jsonable_python

from ai.contracts import DBResult
from ai_service.tools import db
from ai_service.tools.errors import ToolError, ToolNotFound

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_PORT = 8002  # 4200 Angular, 8080 Spring Boot, 8000 mock_apis, 8001 ai_service

mcp = FastMCP("nexchain-tools", port=int(os.environ.get("MCP_PORT") or DEFAULT_PORT))


def _audit(tool: str, inputs: str, started: float, rows: int | None = None) -> None:
    """tech-req §4.2: every tool call is logged with name, input, output size,
    latency and outcome. Failures are logged by the caller's `except`."""
    logger.info(
        "mcp_tool=%s input=%s rows=%s latency_ms=%.1f status=ok",
        tool,
        inputs,
        rows,
        (time.perf_counter() - started) * 1000,
    )


@mcp.tool()
def db_query(sql: str) -> DBResult:
    """Execute a pre-validated read-only SQL SELECT against the supply-chain
    database and return the matching rows.

    `sql` must already have been validated by the Text-to-SQL agent (tech-req
    §5). Use for questions that need aggregation, filtering or joins across
    orders, customers, inventory, shipments, invoices and payments.
    """
    started = time.perf_counter()
    try:
        rows = db.run_select(sql)
    except ToolError:
        logger.warning("mcp_tool=db_query input=%s status=failed", sql)
        raise
    _audit("db_query", sql, started, rows=len(rows))
    return DBResult(rows=to_jsonable_python(rows))


@mcp.tool()
def get_order(order_no: str) -> dict[str, Any]:
    """Look up one sales order as the system of record holds it — status,
    promised and revised delivery dates, plus the customer's SLA tier and the
    fulfilling warehouse.

    Prefer this over `db_query` for a single known order number. It carries the
    `sla_tier` and warehouse that the ERP API's order status does not, and that
    the Business Rule Agent needs to decide breach and escalation.
    """
    started = time.perf_counter()
    try:
        order = db.get_order(order_no)
    except ToolError:
        logger.warning("mcp_tool=get_order input=%s status=failed", order_no)
        raise
    if order is None:
        # A fact about the data, not a failure of the system — and the same
        # answer api_client gives for an unknown order, so the graph has one
        # way to learn "no such order" whichever tool it asked.
        logger.warning("mcp_tool=get_order input=%s status=not_found", order_no)
        raise ToolNotFound("get_order", f"no order {order_no}")
    _audit("get_order", order_no, started, rows=1)
    return to_jsonable_python(order)


if __name__ == "__main__":
    mcp.run(transport=os.environ.get("MCP_TRANSPORT") or "stdio")
