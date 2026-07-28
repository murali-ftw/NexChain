"""Shared structured-logging setup for every Python process in the stack
(ai_service, mcp_server, mock_apis, and the ai/ package itself).

Mirrors what backend-api does with Logback + MDC (see
backend-api/src/main/resources/logback-spring.xml and
RequestCorrelationFilter): one correlation id per request, carried via a
contextvar rather than threaded through every function signature, and
injected into every log record automatically through a logging.Filter so
individual log statements never have to format it in by hand.

Each service's entrypoint calls `configure_logging(service_name)` exactly
once, at process start (ai_service/main.py, mcp_server/server.py,
mock_apis/main.py) — everywhere else in the codebase gets a plain
module-level `logging.getLogger(__name__)`, same as today.
"""

from __future__ import annotations

import contextvars
import logging
import os
import time
import uuid
from collections.abc import Mapping

REQUEST_ID_HEADER = "x-request-id"
CORRELATION_ID_HEADER = "x-correlation-id"

# The one correlation id for the life of a request, read by _RequestIdFilter
# below so every log record carries it without each call site formatting it
# in by hand. contextvars, not threading.local: FastAPI/Starlette dispatch a
# sync endpoint via anyio.to_thread.run_sync, which *does* propagate the
# current context into that worker thread (unlike a bare
# ThreadPoolExecutor.submit — see ai_service/main.py's use of
# contextvars.copy_context() around the graph invocation for the one place
# in this codebase that needs the manual version of the same propagation).
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

# Never log these header values verbatim — same redaction list conceptually
# as backend-api never logging Authorization/JWT/cookies.
_SENSITIVE_HEADER_NAMES = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "proxy-authorization",
    }
)
_REDACTED = "***REDACTED***"

# Third-party library chatter that isn't actionable day to day — quieted the
# same way backend-api's logback-spring.xml pins org.springframework/
# org.hibernate to WARN so this app's own INFO lines aren't drowned out.
_NOISY_THIRD_PARTY_LOGGERS = (
    "httpx",
    "httpcore",
    "uvicorn.access",
    "chromadb",
    "urllib3",
)


class _RequestIdFilter(logging.Filter):
    """Injects the current request's correlation id (or "-" outside any
    request, e.g. startup/shutdown logs) as `record.request_id`."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def new_request_id() -> str:
    return str(uuid.uuid4())


def get_request_id() -> str:
    """The active correlation id, or "-" if none is bound (e.g. code running
    outside of a request, such as the RAG ingestion CLI)."""
    return request_id_var.get() or "-"


def configure_logging(service_name: str, level: str | None = None) -> None:
    """Configure root logging once, at process entry. Safe to call more than
    once (e.g. re-imported under a test runner) — it replaces the root
    handler each time rather than accumulating duplicates.

    Level defaults to INFO; override via the `LOG_LEVEL` env var (or the
    `level` argument) to enable DEBUG locally. Never set DEBUG in a shared
    environment — some DEBUG-level statements in this codebase intentionally
    carry data (e.g. generated SQL) kept out of INFO for exactly that reason
    (see ai_service/tools/db.py).
    """
    resolved_level = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-5s [%(threadName)s] %(name)s "
            f"service={service_name} [request_id=%(request_id)s] - %(message)s"
        )
    )
    handler.addFilter(_RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(resolved_level)
    root.handlers = [handler]

    for noisy_logger in _NOISY_THIRD_PARTY_LOGGERS:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Safe-to-log copy of a headers mapping: sensitive values replaced,
    everything else (method, path-adjacent metadata) passed through."""
    return {
        name: (_REDACTED if name.lower() in _SENSITIVE_HEADER_NAMES else value)
        for name, value in headers.items()
    }


class RequestContextMiddleware:
    """Pure-ASGI middleware (not Starlette's BaseHTTPMiddleware, which spawns
    a separate task for response streaming — contextvars set here must be
    visible to the request handler running in the *same* task): resolves the
    correlation id, binds it for the life of the request, logs one
    method/path/status/duration summary line, and echoes the id back as a
    response header.

    Shared by ai_service and mock_apis (both FastAPI apps) so the request
    logging shape is identical on both sides of that hop.
    """

    #: Logged at DEBUG instead of INFO — frequent liveness/readiness probes would
    #: otherwise dominate the log at the default level (requirement: no noisy
    #: per-loop/per-poll logs).
    QUIET_PATHS = frozenset({"/health"})

    def __init__(self, app, service_name: str) -> None:
        self.app = app
        self.service_name = service_name
        self._logger = logging.getLogger("http.request")

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id = (
            headers.get(REQUEST_ID_HEADER)
            or headers.get(CORRELATION_ID_HEADER)
            or new_request_id()
        )
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 0

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = list(message.get("headers", []))
                response_headers.append(
                    (b"x-request-id", request_id.encode("latin-1"))
                )
                message = {**message, "headers": response_headers}
            await send(message)

        path = scope.get("path", "-")
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            level = logging.DEBUG if path in self.QUIET_PATHS else logging.INFO
            self._logger.log(
                level,
                "http_request method=%s path=%s status=%s duration_ms=%.1f",
                scope.get("method", "-"),
                path,
                status_code,
                duration_ms,
            )
            request_id_var.reset(token)
