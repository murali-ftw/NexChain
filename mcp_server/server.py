"""MCP server — standardized tool access for the AI layer (P2.7 + P2.8).

The independent tool process tech-req §4.2 requires: Person 3's agents never
touch psycopg or HTTP, they call MCP tools, and this is the server behind them.

Five of the six tools in the frozen tech-req §4.1 table are live here:

    db_query, get_order                                    (P2.7, Day 7)
    get_order_status, get_shipment_status, get_inventory   (P2.8, Day 8)

`kb_search` is the sixth and is not implemented — see the note at the bottom of
this file.

The tools are thin on purpose. All real work — connection handling, HTTP, and
the normalization of every failure to ToolError — lives in ai_service/tools/,
so the same code path is exercised whether you go through MCP or import the
tool layer directly in a test.

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
from typing import Any, Literal, get_args

from collections.abc import Callable
from typing import TypeVar

from mcp.server.fastmcp import FastMCP
from pydantic_core import to_jsonable_python

from ai.agents.text_to_sql_agent.validator import validate_sql
from ai.contracts import DBResult, InventoryRecord, OrderStatus, ShipmentStatus
from ai_service.tools import api_client, db
from ai_service.tools.errors import ToolError, ToolNotFound

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_PORT = 8002  # 4200 Angular, 8080 Spring Boot, 8000 mock_apis, 8001 ai_service

mcp = FastMCP("nexchain-tools", port=int(os.environ.get("MCP_PORT") or DEFAULT_PORT))

T = TypeVar("T")


def _call(tool: str, inputs: str, fn: Callable[..., T], *args: object) -> T:
    """Run one tool-layer call with the audit log tech-req §4.2 requires:
    tool name, input, output size, latency, success/failure.

    Only ToolError is caught — the tool layer promises that is the only thing
    it raises (ai_service/tools/errors.py), so anything else escaping is a bug
    in the tool layer and should be loud, not swallowed here.
    """
    started = time.perf_counter()
    try:
        result = fn(*args)
    except ToolError as exc:
        logger.warning(
            "mcp_tool=%s input=%s status=failed retryable=%s error=%s",
            tool,
            inputs,
            exc.retryable,
            exc.message,
        )
        raise
    logger.info(
        "mcp_tool=%s input=%s size=%d latency_ms=%.1f status=ok",
        tool,
        inputs,
        len(result) if isinstance(result, list | dict) else 1,
        (time.perf_counter() - started) * 1000,
    )
    return result


# --- P2.7: database tools ---------------------------------------------------


@mcp.tool()
def db_query(sql: str) -> DBResult:
    """Execute a read-only SQL SELECT against the supply-chain database and
    return the matching rows.

    Validated here (P2.9) against the same allowlist/denylist/row-limit the
    Text-to-SQL agent (tech-req §5) already enforces before generating this
    tool's input — this is defense in depth at the tool boundary itself, not
    reliance on the caller alone. Use for questions that need aggregation,
    filtering or joins across orders, customers, inventory, shipments,
    invoices and payments.
    """
    validation = validate_sql(sql)
    if not validation.valid or not validation.safe_sql:
        raise ToolError("db_query", f"rejected: {validation.reason}", retryable=False, status_code=400)
    return DBResult(
        rows=to_jsonable_python(_call("db_query", sql, db.run_select, validation.safe_sql))
    )


@mcp.tool()
def get_order(order_no: str) -> dict[str, Any]:
    """Look up one sales order as the system of record holds it — status,
    promised and revised delivery dates, plus the customer's SLA tier and the
    fulfilling warehouse.

    Prefer this over `db_query` for a single known order number. It carries the
    `sla_tier` and warehouse that the ERP API's order status does not, and that
    the Business Rule Agent needs to decide breach and escalation.
    """
    order = _call("get_order", order_no, db.get_order, order_no)
    if order is None:
        # A fact about the data, not a failure of the system — and the same
        # answer api_client gives for an unknown order, so the graph has one
        # way to learn "no such order" whichever tool it asked.
        raise ToolNotFound("get_order", f"no order {order_no}")
    return to_jsonable_python(order)


_Transport = Literal["stdio", "sse", "streamable-http"]
_VALID_TRANSPORTS = get_args(_Transport)
# --- P2.8: operational API tools --------------------------------------------
#
# These reach the mock ERP / shipment-tracking / inventory systems (mock_apis/,
# port 8000) over HTTP. Note get_order_status and get_order are *different
# systems answering about the same order*: this one is what the ERP API reports,
# get_order is what the database holds. The flagship delay case needs both —
# that disagreement is often the story.


@mcp.tool()
def get_order_status(order_no: str) -> OrderStatus:
    """Ask the ERP system for an order's current status and delivery dates.

    This is the *external system's* view of the order. For the customer's SLA
    tier and fulfilling warehouse, which the ERP does not return, use
    `get_order` instead.
    """
    return _call("get_order_status", order_no, api_client.get_order_status, order_no)


@mcp.tool()
def get_shipment_status(tracking_no: str) -> ShipmentStatus:
    """Track a shipment with the carrier: where it physically is right now, and
    why it is held up if it is.

    `current_location` and `delay_reason` are what the Business Rule Agent needs
    to explain a delay rather than just report one. Takes a tracking number
    (e.g. TRK-45892-1), not an order number — get that from `get_order` or the
    `shipment` table first.
    """
    return _call(
        "get_shipment_status", tracking_no, api_client.get_shipment_status, tracking_no
    )


@mcp.tool()
def get_inventory(sku: str) -> InventoryRecord:
    """Check warehouse stock for one SKU: quantity on hand and quantity already
    reserved against other orders.

    Available-to-promise is on-hand minus reserved — a SKU can show healthy
    stock and still be unable to fulfil an order.
    """
    return _call("get_inventory", sku, api_client.get_inventory, sku)


# ponytail: kb_search (the sixth tool in tech-req §4.1, also Person 2's) is not
# here. It is the one tool the team_plan never assigns a day, and nothing is
# blocked on it: Person 3's ai/agents/knowledge_base_agent/retrieval.py calls
# ai/rag/vector_store.py directly today and works. Adding it is ~10 lines
# (wrap vector_store.search, normalize failures to ToolError like every other
# tool) whenever routing KB retrieval through MCP actually buys something.


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT") or "stdio"
    if transport not in _VALID_TRANSPORTS:
        raise ValueError(f"MCP_TRANSPORT must be one of {_VALID_TRANSPORTS}, got {transport!r}")
    mcp.run(transport=transport)  # type: ignore[arg-type]
