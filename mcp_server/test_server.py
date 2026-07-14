"""P2.7 completion gate: "Person 3 can invoke both tools independently"
(docs/team_plan.md), with structured tool outputs (tech-req §4.1).

Independently = over an actual MCP client session, not by importing the Python
function. If these pass, Person 3's LangGraph nodes can call the tools the same
way. Needs a seeded database:

    psql -v ON_ERROR_STOP=1 -d nexchain -f db/seed_data.sql
    .venv/bin/python -m pytest mcp_server/ -v
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from ai_service.tools import db
from ai_service.tools.errors import ToolUnavailable
from mcp_server.server import mcp


@pytest.fixture(scope="session", autouse=True)
def require_seeded_db() -> None:
    try:
        if not db.run_select("SELECT 1 AS ok FROM sales_orders LIMIT 1"):
            pytest.fail("Database is empty — run: psql -d nexchain -f db/seed_data.sql")
    except ToolUnavailable as exc:
        pytest.fail(f"{exc}\nStart Postgres and run: psql -d nexchain -f db/seed_data.sql")


async def call(tool: str, **arguments: Any) -> Any:
    """Invoke a tool the way Person 3's MCP client will: over a session."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool(tool, arguments)
        if result.isError:
            raise AssertionError(result.content[0].text)
        return result.structuredContent


@pytest.mark.asyncio
async def test_the_two_tools_are_advertised() -> None:
    """Person 3 can discover them without being told they exist."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        tools = {tool.name for tool in (await client.list_tools()).tools}
    assert {"db_query", "get_order"} <= tools


@pytest.mark.asyncio
async def test_db_query_returns_structured_rows() -> None:
    result = await call("db_query", sql="SELECT order_no, current_status FROM sales_orders WHERE order_no = 'SO-45892'")
    assert result["rows"] == [{"order_no": "SO-45892", "current_status": "Delayed"}]


@pytest.mark.asyncio
async def test_db_query_aggregates() -> None:
    """The case db_query exists for — a question get_order cannot answer."""
    result = await call("db_query", sql="SELECT COUNT(*) AS n FROM sales_orders WHERE current_status = 'Delayed'")
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
    assert "no order SO-NOPE" in result.content[0].text


@pytest.mark.asyncio
async def test_a_broken_query_is_a_controlled_error_not_a_crash() -> None:
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool("db_query", {"sql": "SELECT * FROM no_such_table"})
    assert result.isError
    assert "db_query" in result.content[0].text
