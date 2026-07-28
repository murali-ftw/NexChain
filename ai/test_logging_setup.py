"""Coverage for the shared logging setup (correlation id propagation and
header redaction) used by ai_service, mcp_server, and mock_apis.

    .venv/bin/python -m pytest ai/test_logging_setup.py -v
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai.logging_setup import (
    RequestContextMiddleware,
    get_request_id,
    redact_headers,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware, service_name="test-service")

    @app.get("/whoami")
    def whoami() -> dict[str, str]:
        # Proves the id set by the middleware is actually visible to request-handling
        # code, not just echoed back — the whole point of the contextvar plumbing.
        return {"request_id": get_request_id()}

    return app


client = TestClient(_build_app())


def test_missing_request_id_is_minted_and_returned_in_response_header() -> None:
    response = client.get("/whoami")
    request_id = response.headers["x-request-id"]
    assert request_id
    assert response.json()["request_id"] == request_id


def test_supplied_x_request_id_is_echoed_back_unchanged() -> None:
    response = client.get("/whoami", headers={"X-Request-ID": "caller-req-123"})
    assert response.headers["x-request-id"] == "caller-req-123"
    assert response.json()["request_id"] == "caller-req-123"


def test_x_correlation_id_is_accepted_when_x_request_id_is_absent() -> None:
    response = client.get("/whoami", headers={"X-Correlation-ID": "corr-456"})
    assert response.headers["x-request-id"] == "corr-456"


def test_x_request_id_takes_precedence_over_x_correlation_id() -> None:
    response = client.get(
        "/whoami",
        headers={"X-Request-ID": "primary-789", "X-Correlation-ID": "secondary-000"},
    )
    assert response.headers["x-request-id"] == "primary-789"


def test_request_id_does_not_leak_across_requests() -> None:
    first = client.get("/whoami", headers={"X-Request-ID": "req-a"})
    second = client.get("/whoami")
    assert first.json()["request_id"] == "req-a"
    assert second.json()["request_id"] != "req-a"


def test_redact_headers_masks_sensitive_values_case_insensitively() -> None:
    headers = {
        "Authorization": "Bearer super-secret-jwt",
        "Cookie": "session=abc123",
        "X-Api-Key": "sk-live-secret",
        "Content-Type": "application/json",
    }
    redacted = redact_headers(headers)
    assert redacted["Authorization"] == "***REDACTED***"
    assert redacted["Cookie"] == "***REDACTED***"
    assert redacted["X-Api-Key"] == "***REDACTED***"
    assert redacted["Content-Type"] == "application/json"


def test_redact_headers_does_not_mutate_safe_values() -> None:
    headers = {"X-Request-ID": "req-1", "User-Agent": "pytest"}
    assert redact_headers(headers) == headers
