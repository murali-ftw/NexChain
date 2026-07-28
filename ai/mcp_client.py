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
import time
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from ai_service.tools.errors import ToolError, ToolNotFound, ToolUnavailable

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://localhost:8002/mcp"
DEFAULT_CALL_TIMEOUT_SECONDS = 15.0


def server_url() -> str:
    return os.environ.get("MCP_SERVER_URL", "").strip() or DEFAULT_URL


def call_timeout_seconds() -> float:
    raw = os.environ.get("MCP_CALL_TIMEOUT_SECONDS", "").strip()
    try:
        return float(raw) if raw else DEFAULT_CALL_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_CALL_TIMEOUT_SECONDS


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
        # Created here (not inside _connect()) so close() can always signal it,
        # even if called before the background thread has started running the
        # coroutine — asyncio.Event() doesn't bind to a loop at construction
        # time, only when actually awaited/set, so this is safe to create from
        # the calling thread.
        self._shutdown = asyncio.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="mcp-client"
        )
        self._thread.start()
        # NOTE: does not block here. Callers must call wait_ready() themselves,
        # outside of _connection_lock (see _get_connection), so a slow/hanging
        # handshake doesn't serialize unrelated concurrent requests behind the
        # module-level lock — they instead each wait on self._ready in
        # parallel, sharing the one in-flight attempt.

    def wait_ready(self, timeout: float) -> None:
        """Block (bounded) until the handshake concludes, success or failure.
        Safe to call from multiple threads concurrently — they all just wait
        on the same threading.Event rather than serializing behind a lock."""
        if not self._ready.wait(timeout=timeout):
            raise ToolUnavailable(
                "mcp_client",
                f"MCP connection to {server_url()} did not complete within {timeout}s",
            )
        if self._session is None:
            raise ToolUnavailable(
                "mcp_client",
                f"cannot reach MCP server at {server_url()}: {self._startup_error}",
            )

    @property
    def failed(self) -> bool:
        """True once the handshake has concluded and it did not succeed.
        False while still pending (mid-handshake), so a concurrent caller
        reuses the in-flight attempt instead of starting a redundant one."""
        return self._ready.is_set() and self._session is None

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
                    await self._shutdown.wait()  # held open until close()
        except BaseException as exc:  # noqa: BLE001 - surfaced via wait_ready/call_tool
            logger.warning("mcp_client connect to %s failed: %s", server_url(), exc)
            # A session set earlier in this same coroutine (the "hold open" await
            # raised because the stream broke) is now dead — clear it so `.failed`
            # reports True and the next call rebuilds a fresh _Connection, instead
            # of `.failed` staying False forever because `_session` is non-None.
            self._session = None
            self._startup_error = exc
            self._ready.set()

    def close(self, timeout: float = 5.0) -> None:
        """Gracefully tear down an abandoned connection. Signals the
        background coroutine to fall out of its `async with` blocks normally
        (via self._shutdown), so __aexit__ actually runs for both
        streamable_http_client and ClientSession — closing the HTTP session
        and releasing the socket — rather than discarding them mid-`async
        with` for the garbage collector to eventually reclaim. Then joins the
        thread so it doesn't outlive this call. Bounded by `timeout` so a
        wedged connection can't block the caller indefinitely.
        """
        self._session = None
        try:
            self._loop.call_soon_threadsafe(self._shutdown.set)
        except RuntimeError:
            pass  # loop already stopped/closed — nothing to signal
        self._thread.join(timeout=timeout)

    def call_tool(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self._session
        if session is None:
            raise ToolUnavailable(
                tool,
                f"cannot reach MCP server at {server_url()}: {self._startup_error}",
            )
        future = asyncio.run_coroutine_threadsafe(
            session.call_tool(tool, arguments), self._loop
        )
        try:
            result = future.result(timeout=call_timeout_seconds())
        except Exception as exc:
            future.cancel()
            # Gracefully close (not loop.stop()) so the abandoned
            # streamable_http_client/ClientSession actually run __aexit__ and
            # release their HTTP session/socket, instead of being left
            # mid-`async with` for the garbage collector.
            self.close()
            raise ToolUnavailable(tool, f"MCP call failed: {exc}") from exc
        if result.isError:
            content = result.content[0] if result.content else None
            text = getattr(content, "text", None) or "unknown MCP error"
            raise _classify(tool, text)
        return result.structuredContent or {}


_connection: _Connection | None = None
_connection_lock = threading.Lock()

BOOTSTRAP_TIMEOUT_SECONDS = 10.0


def _get_connection() -> _Connection:
    global _connection
    with _connection_lock:
        conn = _connection
        if conn is None or conn.failed:
            conn = _Connection()
            _connection = conn
    # Wait for the handshake OUTSIDE the lock: concurrent callers that land
    # here while a connection is already pending all share the same `conn`
    # (assigned above under the lock) and each wait on its self._ready
    # independently, in parallel — none of them hold _connection_lock while
    # waiting, so a slow handshake no longer serializes unrelated requests.
    conn.wait_ready(timeout=BOOTSTRAP_TIMEOUT_SECONDS)
    return conn


def call_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call one MCP tool synchronously. Raises ai_service.tools.errors.ToolError
    (or a subclass) on failure — the same exception type every direct
    tool-layer call already raised, so callers don't need to know MCP is
    involved.
    """
    started = time.perf_counter()
    try:
        result = _get_connection().call_tool(tool, arguments)
    except ToolError:
        logger.warning(
            "dependency_call dependency=mcp_server tool=%s outcome=failure duration_ms=%.1f",
            tool,
            (time.perf_counter() - started) * 1000,
        )
        raise
    logger.info(
        "dependency_call dependency=mcp_server tool=%s outcome=success duration_ms=%.1f",
        tool,
        (time.perf_counter() - started) * 1000,
    )
    return result
