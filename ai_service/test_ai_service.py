"""P2.5 completion gate: "Spring Boot can send a question and receive valid
JSON" (docs/team_plan.md).

Spring Boot doesn't call this service until P1.10 (Day 11), so the gate is
verified structurally instead of end-to-end: the request shape Spring Boot
documented is accepted, and the response JSON deserializes cleanly into its
ChatResponse record. test_response_fields_cover_spring_boot_chat_response
parses the actual Java file rather than a copied list of field names, so if
Person 1 adds a field to their DTO, this fails instead of drifting.

    .venv/bin/python -m pytest ai_service/ -v

Needs no database and no LLM key — the P2.5 boundary has neither.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from ai_service.main import app

client = TestClient(app)

CHAT_RESPONSE_JAVA = (
    Path(__file__).resolve().parent.parent
    / "backend-api/src/main/java/com/nexchain/backend/chat/dto/ChatResponse.java"
)

# Spring Boot's own envelope — it fills these in itself, so the AI service is
# not expected to return them (see the ChatResponse javadoc).
SPRING_OWNED_FIELDS = {"timestamp", "warnings"}


def _java_record_fields(path: Path) -> set[str]:
    """Field names from a Java record's component list."""
    body = re.search(r"public record \w+\((.*?)\)\s*\{", path.read_text(), re.DOTALL)
    assert body, f"Could not parse a record declaration out of {path}"
    return {
        component.split()[-1]
        for component in body.group(1).split(",")
        if component.strip()
    }


def test_health() -> None:
    assert client.get("/health").json() == {"status": "UP", "service": "ai-service"}


def test_query_returns_valid_json_for_a_question() -> None:
    """The gate, in one test."""
    response = client.post(
        "/ai/query",
        json={
            "query": "Where is order SO-45892? Why is it delayed?",
            "sessionId": "session-abc",
            "traceId": "trace-123",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answerText"]
    assert body["intent"] in {"KNOWLEDGE_QUERY", "DATABASE_QUERY", "API_QUERY", "MULTI_TOOL_QUERY"}
    assert body["slaStatus"] in {"On Time", "At Risk", "Breached", "N/A"}
    assert body["error"] is None


def test_trace_id_is_echoed_back_unchanged() -> None:
    """Correlation across Spring Boot -> FastAPI -> LangGraph -> MCP depends on
    this ID surviving the hop intact (tech-req §9, audit_log.trace_id)."""
    body = client.post(
        "/ai/query", json={"query": "anything", "traceId": "trace-xyz-789"}
    ).json()
    assert body["traceId"] == "trace-xyz-789"


def test_missing_trace_id_is_minted_not_left_null() -> None:
    body = client.post("/ai/query", json={"query": "anything"}).json()
    assert body["traceId"]
    assert body["sessionId"]


def test_the_wire_is_camel_case() -> None:
    """Spring Boot's records are camelCase; Python's contract is snake_case.
    The JSON must be camelCase or Person 1 needs @JsonProperty on every field."""
    body = client.post("/ai/query", json={"query": "anything"}).json()
    assert "answerText" in body and "answer_text" not in body
    assert "slaStatus" in body and "sla_status" not in body


def test_response_fields_cover_spring_boot_chat_response() -> None:
    """Every field Spring Boot's ChatResponse expects (minus the ones it owns
    itself) is present in our JSON. Reads the live Java file, so this breaks
    loudly if Person 1's DTO changes."""
    java_fields = _java_record_fields(CHAT_RESPONSE_JAVA) - SPRING_OWNED_FIELDS
    body = client.post("/ai/query", json={"query": "anything"}).json()
    missing = java_fields - set(body)
    assert not missing, f"AI service response is missing fields Spring Boot expects: {missing}"


def test_provisional_delivery_date_fields_are_present() -> None:
    """The two fields Person 1 flagged as needing Person 3's sign-off. They're
    nullable and unpopulated today, but the key must exist so Angular's Impact
    table has somewhere to read from once the pipeline is live."""
    body = client.post("/ai/query", json={"query": "anything"}).json()
    assert "promisedDeliveryDate" in body
    assert "revisedDeliveryDate" in body


def test_blank_query_is_a_clean_422_not_a_stack_trace() -> None:
    response = client.post("/ai/query", json={"query": ""})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_missing_query_is_rejected() -> None:
    assert client.post("/ai/query", json={"sessionId": "s1"}).status_code == 422


def test_snake_case_input_is_also_accepted() -> None:
    """populate_by_name=True: tolerate either casing on the way in, so a
    Python caller (Person 3's tests) doesn't have to speak camelCase."""
    body = client.post("/ai/query", json={"query": "anything", "trace_id": "t-1"}).json()
    assert body["traceId"] == "t-1"
