"""Real MCP client for the AI layer's boundary modules (Day 11, ai/CONTRACTS.md
§11). Replaces the direct-call shortcut db_boundary.py/api_boundary.py used
while no MCP client existed anywhere in this repo.

Talks to the independently-running mcp_server service (mcp_server/server.py,
streamable-http transport) over MCP_SERVER_URL — the same environment-variable
service-discovery pattern ai_service already uses for MOCK_API_BASE_URL and
the database URL.

ClientSession is async-only; every boundary call is synchronous (matching the
rest of the tool layer), so one background thread owns a single long-lived
event loop + session for the process's lifetime, and callers block on it via
asyncio.run_coroutine_threadsafe. One persistent connection, not one per call
— reconnecting per query would pay a handshake for every db_query /
get_shipment_status / get_inventory call the direct-call shortcut never paid.

MCP's CallToolResult carries only text on error — none of ToolError's
retryable/status_code fields cross the wire. Failing closed as retryable,
except for the two textual shapes the tool implementations actually produce
for permanent failures ("rejected:" from SQL validation, "no such"/"no order"/
"not found" for an unknown order/tracking/sku), is deliberate: treating an
ambiguous failure as transient costs one extra retry (MAX_RETRIES_PER_NODE
already bounds that to 1); treating a transient one as permanent means giving
up when a retry would have worked.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from ai_service.tools.errors import ToolError, ToolNotFound, ToolUnavailable

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://localhost:8002/mcp"


def server_url() -> str:
    return os.environ.get("MCP_SERVER_URL", "").strip() or DEFAULT_URL


def _classify(tool: str, message: str) -> ToolError:
    lowered = message.lower()
    if "rejected:" in lowered:
        return ToolError(tool, message, retryable=False, status_code=400)
    if "no such" in lowered or "no order" in lowered or "not found" in lowered:
        return ToolNotFound(tool, message)
    return ToolUnavailable(tool, message)


class _Connection:
    """One background thread, one event loop, one MCP session — started
    lazily on first use and held for as long as it stays healthy."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._session: ClientSession | None = None
        self._startup_error: BaseException | None = None
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="mcp-client"
        )
        self._thread.start()
        self._ready.wait()

    @property
    def failed(self) -> bool:
        return self._session is None

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect())

    async def _connect(self) -> None:
        try:
            async with streamable_http_client(server_url()) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self._session = session
                    self._ready.set()
                    await asyncio.Event().wait()  # hold the session open
        except BaseException as exc:  # noqa: BLE001 - surfaced via call_tool
            logger.warning("mcp_client connect to %s failed: %s", server_url(), exc)
            self._startup_error = exc
            self._ready.set()

    def call_tool(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._session is None:
            raise ToolUnavailable(
                tool, f"cannot reach MCP server at {server_url()}: {self._startup_error}"
            )
        future = asyncio.run_coroutine_threadsafe(
            self._session.call_tool(tool, arguments), self._loop
        )
        try:
            result = future.result()
        except Exception as exc:
            raise ToolUnavailable(tool, f"MCP call failed: {exc}") from exc
        if result.isError:
            content = result.content[0] if result.content else None
            text = getattr(content, "text", None) or "unknown MCP error"
            raise _classify(tool, text)
        return result.structuredContent or {}


_connection: _Connection | None = None
_connection_lock = threading.Lock()


def _get_connection() -> _Connection:
    global _connection
    with _connection_lock:
        if _connection is None or _connection.failed:
            _connection = _Connection()
        return _connection


def call_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call one MCP tool synchronously. Raises ai_service.tools.errors.ToolError
    (or a subclass) on failure — the same exception type every direct
    tool-layer call already raised, so callers don't need to know MCP is
    involved.
    """
    return _get_connection().call_tool(tool, arguments)
