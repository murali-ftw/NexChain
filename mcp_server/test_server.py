"""Completion gates for the MCP tools.

P2.7 (Day 7): "Person 3 can invoke both tools independently" — independently
meaning over an actual MCP client session, not by importing the Python function.
P2.8 (Day 8): "All tools return consistent structured responses."

If these pass, Person 3's LangGraph nodes can call the tools the same way.
Needs a seeded database:

    psql -v ON_ERROR_STOP=1 -d nexchain -f db/seed_data.sql
    .venv/bin/python -m pytest mcp_server/ -v

The API tools' mock backends (mock_apis/, P2.4) are mounted in-process rather
than requiring a second server on port 8000 — same app, same code path, no
flaky port juggling. Matches ai_service/tools/test_tools.py.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

from ai_service.tools import api_client, db
from ai_service.tools.errors import ToolUnavailable
from mcp_server.server import mcp
from mock_apis.main import app as mock_api_app


def _error_text(content: list[Any]) -> str:
    """Every error result here is server-generated TextContent; narrow it for mypy."""
    first = content[0]
    assert isinstance(first, TextContent)
    return first.text


@pytest.fixture(scope="session", autouse=True)
def require_seeded_db() -> None:
    try:
        if not db.run_select("SELECT 1 AS ok FROM sales_orders LIMIT 1"):
            pytest.fail("Database is empty — run: psql -d nexchain -f db/seed_data.sql")
    except ToolUnavailable as exc:
        pytest.fail(
            f"{exc}\nStart Postgres and run: psql -d nexchain -f db/seed_data.sql"
        )


@pytest.fixture(autouse=True)
def mount_mock_apis_in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_api_client = TestClient(mock_api_app)

    def fake_get(url: str, timeout: float | None = None) -> httpx.Response:
        return mock_api_client.get(url.removeprefix(api_client.base_url()))

    monkeypatch.setattr(api_client.httpx, "get", fake_get)


async def call(tool: str, **arguments: Any) -> Any:
    """Invoke a tool the way Person 3's MCP client will: over a session."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool(tool, arguments)
        if result.isError:
            raise AssertionError(_error_text(result.content))
        return result.structuredContent


ALL_TOOLS = {
    "db_query",
    "get_order",
    "get_order_status",
    "get_shipment_status",
    "get_inventory",
}


@pytest.mark.asyncio
async def test_every_tool_is_advertised() -> None:
    """Person 3 can discover them without being told they exist."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        tools = {tool.name for tool in (await client.list_tools()).tools}
    assert ALL_TOOLS <= tools


@pytest.mark.asyncio
async def test_db_query_returns_structured_rows() -> None:
    result = await call(
        "db_query",
        sql="SELECT order_no, current_status FROM sales_orders WHERE order_no = 'SO-45892'",
    )
    assert result["rows"] == [{"order_no": "SO-45892", "current_status": "Delayed"}]


@pytest.mark.asyncio
async def test_db_query_aggregates() -> None:
    """The case db_query exists for — a question get_order cannot answer."""
    result = await call(
        "db_query",
        sql="SELECT COUNT(*) AS n FROM sales_orders WHERE current_status = 'Delayed'",
    )
    assert result["rows"][0]["n"] >= 1


@pytest.mark.asyncio
async def test_get_order_carries_sla_tier_and_warehouse() -> None:
    """Exactly what the ERP API's order status does not carry, and what the
    Business Rule Agent needs to decide breach and escalation."""
    order = await call("get_order", order_no="SO-45892")
    assert order["sla_tier"] == "GOLD"
    assert order["current_status"] == "Delayed"
    assert order["warehouse_code"]
    # Dates and money survive the MCP JSON boundary rather than blowing up on
    # serialization — the reason the tools go through to_jsonable_python().
    assert order["promised_delivery_date"] == "2026-07-03"
    assert order["total_amount"] == "4200.00"
    assert json.dumps(order)


@pytest.mark.asyncio
async def test_unknown_order_is_a_controlled_error_not_a_crash() -> None:
    """tech-req §7: a tool reports a clear failure rather than crashing the
    graph. Not-found must reach Person 3 as an error, not as a null row."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool("get_order", {"order_no": "SO-NOPE"})
    assert result.isError
    assert "no order SO-NOPE" in _error_text(result.content)


@pytest.mark.asyncio
async def test_a_broken_query_is_a_controlled_error_not_a_crash() -> None:
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool(
            "db_query", {"sql": "SELECT * FROM no_such_table"}
        )
    assert result.isError
    assert "db_query" in _error_text(result.content)


# --- P2.9: tool safety at the db_query boundary -----------------------------
#
# The completion gate: "Dangerous SQL is rejected and failed tools return
# controlled errors." Validation runs a second time here at the tool boundary
# (defense in depth, tech-req §4.2) even though the Text-to-SQL agent validates
# before emitting SQL — a bug that bypasses the agent must still be stopped here,
# and underneath both the copilot_readonly role is a third, DB-enforced layer.
# A rejection must reach Person 3 as a controlled error, never as an execution.


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM sales_orders WHERE order_no = 'SO-45892'",
        "UPDATE sales_orders SET current_status = 'Delivered'",
        "DROP TABLE customers",
        "TRUNCATE customers",
        "INSERT INTO customers (customer_code) VALUES ('X')",
        "SELECT 1; DELETE FROM sales_orders",  # piggy-backed write
        # RC stabilization: a data-modifying CTE still parses as exp.Select at
        # the top level — must be caught by an explicit AST walk, not just the
        # raw-text keyword scan (ai/agents/text_to_sql_agent/validator.py).
        "WITH t AS (INSERT INTO sales_orders (order_no) VALUES ('X') RETURNING *) SELECT * FROM t",
        "WITH t AS (UPDATE sales_orders SET current_status = 'Delivered' RETURNING *) SELECT * FROM t",
        "SELECT * INTO new_table FROM sales_orders",
        "CREATE TABLE evil AS SELECT * FROM sales_orders",
    ],
)
async def test_write_and_ddl_sql_is_rejected_before_execution(sql: str) -> None:
    """tech-req §271 security test: db_query cannot execute write/DDL. The row
    still exists afterward, proving nothing ran."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool("db_query", {"sql": sql})
    assert result.isError
    assert "rejected" in _error_text(result.content)

    survivor = await call(
        "db_query", sql="SELECT order_no FROM sales_orders WHERE order_no = 'SO-45892'"
    )
    assert survivor["rows"] == [{"order_no": "SO-45892"}]


@pytest.mark.asyncio
async def test_non_allowlisted_table_is_rejected() -> None:
    """`users` and `audit_log` are outside SQL_TABLE_ALLOWLIST — the tool refuses
    them even though a SELECT against them is otherwise well-formed. (The
    copilot_readonly role also can't read them, but the tool must not rely on
    that alone.)"""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool("db_query", {"sql": "SELECT * FROM users"})
    assert result.isError
    assert "non-allowlisted" in _error_text(result.content)


@pytest.mark.asyncio
async def test_uppercase_table_name_is_still_allowlisted() -> None:
    """RC stabilization: Postgres folds unquoted identifiers to lowercase, so
    `SALES_ORDERS` and `sales_orders` are the same table — the validator must
    compare case-insensitively rather than rejecting a query for cosmetic
    casing the LLM happened to emit."""
    result = await call(
        "db_query", sql="SELECT order_no FROM SALES_ORDERS WHERE order_no = 'SO-45892'"
    )
    assert result["rows"] == [{"order_no": "SO-45892"}]


@pytest.mark.asyncio
async def test_schema_qualified_table_is_rejected() -> None:
    """RC stabilization: a schema-qualified reference (`public.sales_orders`)
    must not silently bypass the allowlist by matching only on the bare table
    name — reject it outright rather than depend entirely on DB grants."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool(
            "db_query", {"sql": "SELECT * FROM public.sales_orders"}
        )
    assert result.isError
    assert "schema-qualified" in _error_text(result.content)


@pytest.mark.asyncio
async def test_quoted_identifier_differs_from_unquoted() -> None:
    """Quoted identifiers in PostgreSQL are case-sensitive and distinct from
    unquoted identifiers. `"Sales_Orders"` is not the same table as `sales_orders`
    or `SALES_ORDERS`. The validator should reject quoted identifiers that don't
    exactly match an allowlisted table."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        # Quoted identifier with different casing should be rejected (doesn't exist)
        result = await client.call_tool(
            "db_query", {"sql": 'SELECT order_no FROM "Sales_Orders" LIMIT 1'}
        )
    assert result.isError
    assert "non-allowlisted" in _error_text(result.content)


@pytest.mark.asyncio
async def test_row_limit_is_capped_at_200() -> None:
    """An over-large LIMIT is rewritten down to SQL_ROW_LIMIT so a tool call can
    never dump an unbounded result set at the graph."""
    result = await call(
        "db_query", sql="SELECT order_no FROM sales_orders LIMIT 100000"
    )
    assert len(result["rows"]) <= 200


# --- P2.8: the three operational API tools ----------------------------------


@pytest.mark.asyncio
async def test_get_order_status_reaches_the_erp() -> None:
    status = await call("get_order_status", order_no="SO-45892")
    assert status["order_no"] == "SO-45892"
    assert status["status"] == "Delayed"
    assert status["revised_delivery_date"] == "2026-07-09"


@pytest.mark.asyncio
async def test_get_shipment_status_carries_location_and_delay_reason() -> None:
    """The two fields that let the Business Rule Agent explain a delay rather
    than merely report one."""
    shipment = await call("get_shipment_status", tracking_no="TRK-45892-1")
    assert shipment["shipment_status"] == "Customs Hold"
    assert shipment["current_location"] == "Chennai Port"
    assert "HS code mismatch" in shipment["delay_reason"]


@pytest.mark.asyncio
async def test_get_inventory_returns_on_hand_and_reserved() -> None:
    inventory = await call("get_inventory", sku="SKU-1001")
    assert inventory["quantity_on_hand"] == 240
    assert inventory["quantity_reserved"] == 40


@pytest.mark.asyncio
async def test_the_erp_and_the_database_agree_about_the_flagship_order() -> None:
    """get_order_status and get_order are different systems answering about the
    same order. The flagship demo leans on both, so a disagreement between them
    would be a data bug, not an interesting finding."""
    from_erp = await call("get_order_status", order_no="SO-45892")
    from_db = await call("get_order", order_no="SO-45892")
    assert from_erp["status"] == from_db["current_status"]
    assert from_erp["revised_delivery_date"] == from_db["revised_delivery_date"]


# --- The P2.8 gate: "all tools return consistent structured responses" -------


@pytest.mark.asyncio
async def test_every_tool_declares_an_output_schema() -> None:
    """Consistent = every tool returns typed structured content, not a blob of
    text Person 3 has to parse. A bare `dict` return annotation silently gets
    no output schema from the SDK, which is exactly the trap this catches."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        tools = {
            t.name: t for t in (await client.list_tools()).tools if t.name in ALL_TOOLS
        }
    for name, tool in tools.items():
        assert tool.outputSchema, f"{name} has no output schema"
        assert tool.description, f"{name} has no description for the model to route on"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("get_order", {"order_no": "SO-NOPE"}),
        ("get_order_status", {"order_no": "SO-NOPE"}),
        ("get_shipment_status", {"tracking_no": "TRK-NOPE"}),
        ("get_inventory", {"sku": "SKU-NOPE"}),
    ],
)
async def test_unknown_identifiers_fail_the_same_way_on_every_tool(
    tool: str, arguments: dict[str, str]
) -> None:
    """tech-req §7: a tool reports a clear failure rather than crashing the
    graph — and it reports it *the same way* whichever tool was asked, so the
    graph needs one not-found path, not four."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool(tool, arguments)
    assert result.isError, (
        f"{tool} returned success for an identifier that does not exist"
    )
    assert _error_text(result.content)
