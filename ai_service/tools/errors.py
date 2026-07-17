"""Normalized tool failures (P2.6).

Every way a tool can fail — timeout, connection refused, 404, 500, malformed
body, database down — surfaces as one exception type carrying enough structure
for the caller to decide what to do. tech-req §7 is explicit that a tool must
"report a clear 'service unavailable' status rather than crashing the graph",
and tech-req §3.4 gives each LangGraph node exactly one retry
(MAX_RETRIES_PER_NODE), which only works if retryable failures are
distinguishable from permanent ones.

So: `retryable` says whether trying again could plausibly help. A timeout or a
502 is retryable; a 404 for an order number that doesn't exist is not — retrying
it just burns the node's single retry on a guaranteed second failure.
"""

from __future__ import annotations


class ToolError(RuntimeError):
    """A tool call failed. Never let a raw httpx/psycopg exception past the
    tool layer — the graph should only ever have to catch this one."""

    def __init__(
        self,
        tool: str,
        message: str,
        *,
        retryable: bool,
        status_code: int | None = None,
    ) -> None:
        super().__init__(f"{tool}: {message}")
        self.tool = tool
        self.message = message
        self.retryable = retryable
        self.status_code = status_code


class ToolNotFound(ToolError):
    """The upstream system has no such order / tracking number / SKU.

    Not retryable, and not really an error in the system — it's a fact about the
    data. The agent should say "no such order" rather than "service unavailable".
    """

    def __init__(self, tool: str, message: str) -> None:
        super().__init__(tool, message, retryable=False, status_code=404)


class ToolUnavailable(ToolError):
    """The upstream system is down, timed out, or returned a server error."""

    def __init__(self, tool: str, message: str, status_code: int | None = None) -> None:
        super().__init__(tool, message, retryable=True, status_code=status_code)
