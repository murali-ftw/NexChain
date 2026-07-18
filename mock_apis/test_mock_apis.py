"""P2.4 completion gate: "all endpoints return correct responses for predefined
scenarios" (docs/team_plan.md).

Runs against the seeded database — db/seed_data.sql must have been applied:

    psql -v ON_ERROR_STOP=1 -d nexchain -f db/seed_data.sql
    .venv/bin/python -m pytest mock_apis/ -v

Each scenario asserted here is one of the ones db/verify_scenarios.sql already
proves at the SQL level; this file proves they survive the HTTP boundary with
the exact field names ai/contracts.py freezes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mock_apis.db import MockApiConfigError, fetch_one
from mock_apis.main import app

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def require_seeded_db() -> None:
    """Fail loudly with the fix, rather than 30 confusing assertion errors."""
    try:
        row = fetch_one("SELECT count(*) AS n FROM sales_orders", ())
    except MockApiConfigError as exc:
        pytest.fail(
            f"{exc}\nStart Postgres and run: psql -d nexchain -f db/seed_data.sql"
        )
    if not row or row["n"] == 0:
        pytest.fail("Database is empty — run: psql -d nexchain -f db/seed_data.sql")


def test_health() -> None:
    assert client.get("/health").json() == {"status": "UP", "service": "mock-apis"}


# --- ERP order API ---------------------------------------------------------


def test_flagship_order_is_delayed_with_revised_eta() -> None:
    """SO-45892: the scenario the whole demo is built on (problem_statement §7)."""
    body = client.get("/api/order/SO-45892").json()
    assert body == {
        "order_no": "SO-45892",
        "status": "Delayed",
        "promised_delivery_date": "2026-07-03",
        "revised_delivery_date": "2026-07-09",
    }


def test_on_time_order_has_no_revised_date() -> None:
    body = client.get("/api/order/SO-30001").json()
    assert body["status"] == "Delivered"
    assert body["revised_delivery_date"] is None


def test_cancelled_order() -> None:
    assert client.get("/api/order/SO-30006").json()["status"] == "Cancelled"


def test_unknown_order_is_404_not_a_crash() -> None:
    response = client.get("/api/order/SO-DOES-NOT-EXIST")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# --- Shipment tracking API -------------------------------------------------


def test_flagship_shipment_is_the_customs_hold_scenario() -> None:
    """The delay cause the Final Response Agent quotes back to the user."""
    body = client.get("/api/shipment/status/TRK-45892-1").json()
    assert body == {
        "tracking_no": "TRK-45892-1",
        "shipment_status": "Customs Hold",
        "current_location": "Chennai Port",
        "delay_reason": "HS code mismatch during customs validation.",
    }


def test_carrier_delay_shipment_is_in_transit() -> None:
    body = client.get("/api/shipment/status/TRK-30004-1").json()
    assert body["shipment_status"] == "In Transit"
    assert "capacity" in body["delay_reason"]


def test_warehouse_delay_shipment_never_left_the_warehouse() -> None:
    body = client.get("/api/shipment/status/TRK-30005-1").json()
    assert body["shipment_status"] == "Delayed"
    assert body["current_location"] == "Mumbai Port Warehouse"


def test_delivered_shipment_has_no_delay_reason() -> None:
    body = client.get("/api/shipment/status/TRK-30001-1").json()
    assert body["shipment_status"] == "Delivered"
    assert body["delay_reason"] is None


def test_unknown_tracking_number_is_404() -> None:
    assert client.get("/api/shipment/status/TRK-NOPE").status_code == 404


# --- Inventory API ---------------------------------------------------------


def test_inventory_matches_the_demo_figure() -> None:
    """SKU-1001 = 240 on hand: the number ChatService.java and chat-fixtures.ts
    already show the user. If this breaks, the demo contradicts itself."""
    body = client.get("/api/inventory/SKU-1001").json()
    assert body == {"sku": "SKU-1001", "quantity_on_hand": 240, "quantity_reserved": 40}


def test_inventory_shortage_sku_is_nearly_empty() -> None:
    """SKU-1006 backs the inventory-shortage scenario (SO-30002 wants 50)."""
    assert client.get("/api/inventory/SKU-1006").json()["quantity_on_hand"] == 5


def test_unknown_sku_is_404() -> None:
    assert client.get("/api/inventory/SKU-9999").status_code == 404


# --- Contract conformance --------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected_fields"),
    [
        (
            "/api/order/SO-45892",
            {"order_no", "status", "promised_delivery_date", "revised_delivery_date"},
        ),
        (
            "/api/shipment/status/TRK-45892-1",
            {"tracking_no", "shipment_status", "current_location", "delay_reason"},
        ),
        ("/api/inventory/SKU-1001", {"sku", "quantity_on_hand", "quantity_reserved"}),
    ],
)
def test_response_shape_matches_frozen_contract(
    path: str, expected_fields: set[str]
) -> None:
    """The MCP tools in P2.8 pass these through unchanged — no extra or missing
    fields relative to ai/contracts.py."""
    assert set(client.get(path).json()) == expected_fields


def test_apis_are_read_only_at_the_database_level() -> None:
    """Defense in depth: the mock APIs connect as copilot_readonly, so even a
    bug that tried to write to the system of record would be refused by Postgres."""
    import psycopg

    from mock_apis.db import dsn

    with psycopg.connect(dsn()) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("DELETE FROM sales_orders WHERE order_no = 'SO-45892'")
