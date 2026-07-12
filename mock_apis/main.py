"""P2.4 Mock Enterprise APIs (Day 4).

Simulates the three external operational systems the API Status Agent will
call: ERP (order), TMS/carrier (shipment tracking), and WMS (inventory).
Endpoint paths are fixed by docs/problem_statement.md §12 and
docs/03_implementation_plan.md Phase 3:

    GET /api/order/{orderNumber}
    GET /api/shipment/status/{trackingNumber}
    GET /api/inventory/{sku}

Response bodies are exactly the frozen models in ai/contracts.py
(OrderStatus / ShipmentStatus / InventoryRecord), so the MCP tools that wrap
these endpoints in P2.8 are thin passthroughs rather than another translation
layer that could drift from the contract.

This is NOT the FastAPI AI service (that's P2.5, a separate app on its own
port). This app has no LLM, no agents, and no writes — it only reads the
seeded database.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from ai.contracts import InventoryRecord, OrderStatus, ShipmentStatus
from mock_apis.db import MockApiConfigError, fetch_one

app = FastAPI(
    title="NexChain Mock Enterprise APIs",
    description="Simulated ERP / shipment-tracking / inventory systems (P2.4).",
    version="1.0.0",
)


@app.exception_handler(MockApiConfigError)
async def _db_unavailable(_request, exc: MockApiConfigError) -> JSONResponse:
    """The API Status Agent must see a clean, typed failure rather than a
    stack trace when the backing system is down (tech-req §7)."""
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP", "service": "mock-apis"}


@app.get("/api/order/{order_number}", response_model=OrderStatus)
def get_order(order_number: str) -> OrderStatus:
    """Mock ERP order API — backs the `get_order_status` MCP tool (tech-req §4.1)."""
    row = fetch_one(
        """
        SELECT order_no, current_status, promised_delivery_date, revised_delivery_date
        FROM sales_orders
        WHERE order_no = %s
        """,
        (order_number,),
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Order {order_number} not found")
    return OrderStatus(
        order_no=row["order_no"],
        status=row["current_status"],
        promised_delivery_date=_iso(row["promised_delivery_date"]),
        revised_delivery_date=_iso(row["revised_delivery_date"]),
    )


@app.get("/api/shipment/status/{tracking_number}", response_model=ShipmentStatus)
def get_shipment_status(tracking_number: str) -> ShipmentStatus:
    """Mock shipment-tracking API — backs the `get_shipment_status` MCP tool.

    This is the endpoint that surfaces the flagship scenario's delay cause:
    TRK-45892-1 returns Customs Hold at Chennai Port with the HS code mismatch
    reason (problem_statement.md §7).
    """
    row = fetch_one(
        """
        SELECT tracking_no, shipment_status, current_location, delay_reason
        FROM shipment
        WHERE tracking_no = %s
        """,
        (tracking_number,),
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Tracking number {tracking_number} not found")
    return ShipmentStatus(
        tracking_no=row["tracking_no"],
        shipment_status=row["shipment_status"],
        current_location=row["current_location"],
        delay_reason=row["delay_reason"],
    )


@app.get("/api/inventory/{sku}", response_model=InventoryRecord)
def get_inventory(sku: str) -> InventoryRecord:
    """Mock inventory/WMS API — backs the `get_inventory` MCP tool."""
    row = fetch_one(
        """
        SELECT sku, quantity_on_hand, quantity_reserved
        FROM inventory
        WHERE sku = %s
        """,
        (sku,),
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"SKU {sku} not found")
    return InventoryRecord(
        sku=row["sku"],
        quantity_on_hand=row["quantity_on_hand"],
        quantity_reserved=row["quantity_reserved"],
    )
