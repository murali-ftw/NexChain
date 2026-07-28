"""P2.5/P2.10 FastAPI AI Service — the hosting boundary for the AI layer.

This is the service Spring Boot calls. `POST /ai/query` invokes the real
LangGraph pipeline (ai/graph/graph.py, Person 3) and maps its finished
CoPilotState into the frozen CoPilotResponse wire shape via
response_mapper.state_to_fields — no keyword routing or placeholder text
lives here (that was the P2.5-era stand-in; see git history if it's ever
needed again).

Day 10 (Platform stabilization) hardens the error boundary ahead of that
wiring: every AI-layer failure returns a clean, typed non-200 with a generic
client message (the real detail is logged, not returned). ToolError — the one
shape the tool layer normalizes every failure to — becomes a 503, distinct from
the 500 an actual bug gets. So the error contract is settled before the graph
that exercises it lands.

Not to be confused with mock_apis/ (P2.4), which simulates the external ERP /
shipment / inventory systems and runs on its own port. This app is the AI
layer's front door; that one is a system the AI layer will eventually call.
"""

from __future__ import annotations

import contextvars
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator
from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ai.contracts import CoPilotState
from ai.graph.graph import build_graph
from ai.logging_setup import (
    RequestContextMiddleware,
    configure_logging,
    get_request_id,
    new_request_id,
    request_id_var,
)
from ai_service.response_mapper import state_to_fields
from ai_service.schemas import AiQueryRequest, AiQueryResponse
from ai_service.tools.errors import ToolError

configure_logging("ai_service")
logger = logging.getLogger(__name__)

DEFAULT_GRAPH_TIMEOUT_SECONDS = 30.0


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("lifecycle event=starting service=ai_service")
    yield
    logger.info("lifecycle event=shutting_down service=ai_service")


app = FastAPI(
    title="NexChain AI Service",
    description="Hosting boundary between Spring Boot and the LangGraph agent layer (P2.5/P2.10).",
    version="1.0.0",
    lifespan=_lifespan,
)
app.add_middleware(RequestContextMiddleware, service_name="ai_service")

# Built once at process start — StateGraph.compile() is not cheap enough to
# redo per request, and the compiled graph carries no per-request state of
# its own (every node reads/writes only the CoPilotState passed into invoke()).
_graph_build_started = time.perf_counter()
_graph = build_graph()
logger.info(
    "lifecycle event=ready dependency=langgraph_graph duration_ms=%.1f",
    (time.perf_counter() - _graph_build_started) * 1000,
)

# One request at a time can block on an LLM/tool call; a small pool bounds
# how many concurrent /ai/query calls run without limiting Uvicorn's own
# worker count. Sized generously since each graph run is I/O-bound, not CPU-bound.
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ai-graph")


def graph_timeout_seconds() -> float:
    return float(
        os.environ.get("AI_SERVICE_GRAPH_TIMEOUT_SECONDS", "")
        or DEFAULT_GRAPH_TIMEOUT_SECONDS
    )


def _initial_state(request: AiQueryRequest, session_id: str) -> CoPilotState:
    return {
        "session_id": session_id,
        "user_id": request.user_id or "unknown",
        "raw_query": request.query,
        "intent": "",
        "sub_intents": [],
        "kb_result": None,
        "sql_result": None,
        "api_result": None,
        "rule_result": None,
        "retry_count": {},
        "final_response": None,
        "error": None,
    }


@app.exception_handler(RequestValidationError)
async def _validation_error(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Spring Boot must never see a raw FastAPI validation blob; give it the
    same {"detail": ...} shape every other error path here uses so its error
    mapping (docs/api_contracts.md) has one thing to parse."""
    return JSONResponse(status_code=422, content={"detail": exc.errors()[0]["msg"]})


@app.exception_handler(ToolError)
async def _tool_error(_request: Request, exc: ToolError) -> JSONResponse:
    """A tool the graph called failed (P2.10 stabilization). The tool layer has
    already normalized every httpx/psycopg failure to ToolError, so this is the
    one AI-layer failure shape — map it to a clear 503 "service unavailable"
    (tech-req §7) rather than the generic 500 a bug gets. The client detail stays
    generic (the message can embed internal error text); the specifics are logged
    for the trace_id to correlate against (tech-req §9)."""
    logger.warning(
        "Tool failure in /ai/query: tool=%s retryable=%s detail=%s",
        exc.tool,
        exc.retryable,
        exc.message,
    )
    return JSONResponse(
        status_code=503, content={"detail": "AI tool temporarily unavailable"}
    )


@app.exception_handler(Exception)
async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
    """Contract with Person 1: on failure this service returns a non-200 and
    Spring Boot maps it to a partial ChatResponse with a warning — it never
    passes a 5xx through to Angular. So failures must be non-200 and typed, not a
    stack trace. The client message stays generic (docs/api_contracts.md); the
    real exception is logged server-side, not returned."""
    logger.exception("Unhandled error in /ai/query")
    return JSONResponse(
        status_code=500, content={"detail": "Internal AI service error"}
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP", "service": "ai-service"}


@app.post("/ai/query", response_model=AiQueryResponse)
def query(request: AiQueryRequest) -> AiQueryResponse:
    """Answer a natural-language supply-chain question by running it through
    the real LangGraph pipeline (intent classification -> KB/SQL/API
    branches -> business rules -> final response).

    `traceId` is echoed back unchanged, so Spring Boot can correlate the call
    (tech-req §9). If Spring Boot didn't send one, we mint it here rather than
    leaving the audit trail with a hole in it. Graph node failures degrade in
    place (retry.py) and surface as `partial: true` + `error: "..."` via
    response_mapper — only a total pipeline failure (unexpected exception, or
    exceeding the timeout below) reaches the 500/504 handlers, per tech-req §7
    ("report a clear 'service unavailable' status rather than crashing").
    """
    # The correlation id is the same value everywhere: if Spring Boot's X-Request-ID
    # header made it here (RequestContextMiddleware), it wins over minting a second,
    # independent id; an explicit body trace_id (e.g. a direct test call with no
    # header) takes precedence over that in turn. Re-binding request_id_var to the
    # resolved value means every log line for the rest of this request — graph node
    # execution, tool calls, mcp_client — carries this exact trace_id too.
    inbound_request_id = get_request_id()
    trace_id = request.trace_id or (
        inbound_request_id if inbound_request_id != "-" else None
    ) or new_request_id()
    request_id_var.set(trace_id)
    session_id = request.session_id or str(uuid.uuid4())
    logger.info("ai_query trace_id=%s session_id=%s", trace_id, session_id)

    # ThreadPoolExecutor.submit does not itself propagate contextvars into the worker
    # thread (unlike anyio.to_thread, which is how this sync endpoint itself got here) —
    # copy_context().run() carries request_id_var (and anything else bound above) into
    # the graph invocation, so every node/tool log during this call still resolves the
    # same trace_id via get_request_id().
    ctx = contextvars.copy_context()
    started = time.perf_counter()
    future: Future[CoPilotState] = _executor.submit(
        ctx.run, _graph.invoke, _initial_state(request, session_id)
    )
    try:
        final_state = future.result(timeout=graph_timeout_seconds())
    except FutureTimeoutError:
        logger.error(
            "ai_query trace_id=%s timed out after %ss",
            trace_id,
            graph_timeout_seconds(),
        )
        raise TimeoutError(f"AI pipeline exceeded {graph_timeout_seconds()}s") from None
    logger.info(
        "ai_query trace_id=%s session_id=%s duration_ms=%.1f outcome=success",
        trace_id,
        session_id,
        (time.perf_counter() - started) * 1000,
    )

    fields = state_to_fields(final_state)
    return AiQueryResponse(trace_id=trace_id, session_id=session_id, **fields)


@app.exception_handler(TimeoutError)
async def _timeout(_request: Request, exc: TimeoutError) -> JSONResponse:
    return JSONResponse(status_code=504, content={"detail": str(exc)})
