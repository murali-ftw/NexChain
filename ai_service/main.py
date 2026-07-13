"""P2.5 FastAPI AI Service (Day 5) — the hosting boundary for the AI layer.

This is the service Spring Boot calls. Its job today is to be a stable,
correctly-shaped boundary: request/response models, a health check, and
`POST /ai/query` returning a *temporary* response. The LangGraph workflow
behind it is Person 3's (P3.8) and gets wired in at P2.10 (Day 11) — until
then every answer here is a placeholder and says so in `warnings`.

Not to be confused with mock_apis/ (P2.4), which simulates the external ERP /
shipment / inventory systems and runs on its own port. This app is the AI
layer's front door; that one is a system the AI layer will eventually call.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ai.contracts import RoutingCategory, SLAStatus
from ai_service.schemas import AiQueryRequest, AiQueryResponse

logger = logging.getLogger(__name__)

# Disclosed in answer_text, not in a `warnings` field: CoPilotResponse has no
# such field. `warnings` belongs to Spring Boot's own ChatResponse envelope
# (Person 1 owns it), so inventing one here would be a silent contract change.
TEMPORARY_ANSWER_PREFIX = (
    "[Temporary P2.5 response — the LangGraph pipeline is not wired in yet (P2.10, Day 11).]"
)

app = FastAPI(
    title="NexChain AI Service",
    description="Hosting boundary between Spring Boot and the LangGraph agent layer (P2.5).",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Spring Boot must never see a raw FastAPI validation blob; give it the
    same {"detail": ...} shape every other error path here uses so its error
    mapping (docs/api_contracts.md) has one thing to parse."""
    return JSONResponse(status_code=422, content={"detail": exc.errors()[0]["msg"]})


@app.exception_handler(Exception)
async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
    """Contract with Person 1: on failure this service returns a non-200 and
    Spring Boot maps it to a partial ChatResponse with a warning — it never
    passes a 5xx through to Angular. So failures must be non-200 and typed,
    not a stack trace."""
    logger.exception("Unhandled error in /ai/query")
    return JSONResponse(status_code=500, content={"detail": f"AI service error: {exc}"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP", "service": "ai-service"}


@app.post("/ai/query", response_model=AiQueryResponse)
def query(request: AiQueryRequest) -> AiQueryResponse:
    """Answer a natural-language supply-chain question.

    Today: a temporary, contract-shaped placeholder. The response is a valid
    CoPilotResponse so Person 1 can integrate against the real shape now
    (P2.5's completion gate is exactly that — "Spring Boot can send a question
    and receive valid JSON"), and P2.10 swaps the body of this function for a
    LangGraph invocation without the wire contract moving.

    `traceId` is echoed back unchanged, so Spring Boot can correlate the call
    (tech-req §9). If Spring Boot didn't send one, we mint it here rather than
    leaving the audit trail with a hole in it.
    """
    trace_id = request.trace_id or str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    logger.info("ai_query trace_id=%s session_id=%s", trace_id, session_id)

    # ponytail: no intent classification, no tools, no LLM — that's the whole
    # point of a P2.5 placeholder. Replaced wholesale at P2.10; don't grow
    # keyword routing here, Spring Boot's ChatService already mocks that and a
    # second copy would just be another thing to delete.
    return AiQueryResponse(
        trace_id=trace_id,
        session_id=session_id,
        answer_text=f'{TEMPORARY_ANSWER_PREFIX} Received: "{request.query}"',
        intent=RoutingCategory.DATABASE_QUERY,
        sla_status=SLAStatus.NOT_APPLICABLE,
        # partial=True is the honest signal that this is not a complete answer;
        # it's what Spring Boot already keys its degraded-response handling off.
        partial=True,
        error=None,
    )
