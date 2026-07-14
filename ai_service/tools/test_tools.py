"""P2.6 completion gate: "FastAPI can retrieve one order, one shipment and one
inventory record" (docs/team_plan.md), plus the failure paths tech-req §7
requires ("report a clear 'service unavailable' status rather than crashing").

    psql -v ON_ERROR_STOP=1 -d nexchain -f db/seed_data.sql   # if not seeded
    .venv/bin/python -m pytest ai_service/tools/ -v

The API-client tests mount mock_apis in-process rather than requiring a second
server on port 8000 — same app, same code path, no flaky port juggling in CI.
The live cross-process run is done separately (see ai_service/README.md); this
suite is the repeatable one.
"""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from ai_service.tools import api_client, db
from ai_service.tools.errors import ToolError, ToolNotFound, ToolUnavailable
from mock_apis.main import app as mock_api_app


@pytest.fixture(autouse=True)
def mount_mock_apis_in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route api_client's httpx.get at the mock_apis ASGI app in-process.

    Uses Starlette's TestClient rather than httpx.ASGITransport because the
    latter is async-only and api_client is deliberately sync.
    """
    mock_api_client = TestClient(mock_api_app)

    def fake_get(url: str, timeout: float | None = None) -> httpx.Response:
        return mock_api_client.get(url.removeprefix(api_client.base_url()))

    monkeypatch.setattr(api_client.httpx, "get", fake_get)


@pytest.fixture(scope="session", autouse=True)
def require_seeded_db() -> None:
    try:
        if not db.run_select("SELECT 1 AS ok FROM sales_orders LIMIT 1"):
            pytest.fail("Database is empty — run: psql -d nexchain -f db/seed_data.sql")
    except ToolUnavailable as exc:
        pytest.fail(f"{exc}\nStart Postgres and run: psql -d nexchain -f db/seed_data.sql")


# --- The gate: one order, one shipment, one inventory record ---------------


def test_can_retrieve_one_order() -> None:
    order = api_client.get_order_status("SO-45892")
    assert order.order_no == "SO-45892"
    assert order.status == "Delayed"
    assert order.revised_delivery_date == "2026-07-09"


def test_can_retrieve_one_shipment() -> None:
    shipment = api_client.get_shipment_status("TRK-45892-1")
    assert shipment.shipment_status == "Customs Hold"
    assert shipment.current_location == "Chennai Port"
    assert shipment.delay_reason == "HS code mismatch during customs validation."


def test_can_retrieve_one_inventory_record() -> None:
    inventory = api_client.get_inventory("SKU-1001")
    assert inventory.quantity_on_hand == 240
    assert inventory.quantity_reserved == 40


def test_can_retrieve_one_order_from_the_database() -> None:
    """The DB-side counterpart: carries sla_tier and warehouse, which the ERP
    API's response shape does not, and which the Business Rule Agent needs."""
    order = db.get_order("SO-45892")
    assert order is not None
    assert order["sla_tier"] == "GOLD"
    assert order["warehouse_location"] == "Chennai"
    assert order["customer_name"] == "Acme Industries"


# --- Error normalization (tech-req §7) -------------------------------------


def test_unknown_order_raises_not_found_not_unavailable() -> None:
    """A 404 means "no such order", which is a fact, not an outage. It must not
    be retryable — retrying burns the node's single retry on a certain failure."""
    with pytest.raises(ToolNotFound) as exc_info:
        api_client.get_order_status("SO-DOES-NOT-EXIST")
    assert exc_info.value.retryable is False
    assert exc_info.value.status_code == 404


def test_unknown_sku_and_tracking_number_also_raise_not_found() -> None:
    with pytest.raises(ToolNotFound):
        api_client.get_inventory("SKU-9999")
    with pytest.raises(ToolNotFound):
        api_client.get_shipment_status("TRK-NOPE")


def test_unreachable_api_raises_retryable_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Connection refused: the graph must get a clean 'service unavailable',
    not an httpx exception it doesn't know how to catch."""

    def refuse(*_args, **_kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(api_client.httpx, "get", refuse)
    with pytest.raises(ToolUnavailable) as exc_info:
        api_client.get_order_status("SO-45892")
    assert exc_info.value.retryable is True
    assert exc_info.value.tool == "get_order_status"


def test_timeout_raises_retryable_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def time_out(*_args, **_kwargs):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(api_client.httpx, "get", time_out)
    with pytest.raises(ToolUnavailable) as exc_info:
        api_client.get_shipment_status("TRK-45892-1")
    assert exc_info.value.retryable is True
    assert "timed out" in exc_info.value.message


def test_upstream_500_is_retryable_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def server_error(*_args, **_kwargs):
        return httpx.Response(500, json={"detail": "boom"}, request=httpx.Request("GET", "/"))

    monkeypatch.setattr(api_client.httpx, "get", server_error)
    with pytest.raises(ToolUnavailable) as exc_info:
        api_client.get_inventory("SKU-1001")
    assert exc_info.value.status_code == 500
    assert exc_info.value.retryable is True


def test_non_json_error_body_does_not_itself_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    """The error path must not have its own error path."""

    def html_error(*_args, **_kwargs):
        return httpx.Response(502, text="<html>bad gateway</html>", request=httpx.Request("GET", "/"))

    monkeypatch.setattr(api_client.httpx, "get", html_error)
    with pytest.raises(ToolUnavailable) as exc_info:
        api_client.get_order_status("SO-45892")
    assert exc_info.value.status_code == 502


def test_database_writes_are_refused_by_the_role() -> None:
    """The tool layer connects as copilot_readonly, so even a SELECT-only bug
    can't damage the system of record. SQL validation lands at P2.9; this is
    the layer underneath it.

    A permission denial must be non-retryable: the same query gets refused every
    time, so retrying only burns the node's one retry (MAX_RETRIES_PER_NODE).
    """
    with pytest.raises(ToolError) as exc_info:
        db.run_select("DELETE FROM sales_orders WHERE order_no = 'SO-45892'")
    assert "permission denied" in exc_info.value.message
    assert exc_info.value.retryable is False
    assert not isinstance(exc_info.value, ToolUnavailable)


def test_database_down_raises_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_SERVICE_DATABASE_URL", "postgresql://nobody@localhost:9/nope")
    with pytest.raises(ToolUnavailable) as exc_info:
        db.run_select("SELECT 1")
    assert exc_info.value.retryable is True
