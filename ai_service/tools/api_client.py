"""HTTP clients for the mock enterprise APIs (P2.6).

Wraps mock_apis/ (P2.4, port 8000) — the simulated ERP, shipment-tracking, and
inventory systems — behind three typed functions returning the frozen models
from ai/contracts.py. The MCP API tools (P2.8) call these; agents never call
HTTP endpoints directly (tech-req §7).

Every failure is normalized to ToolError. Timeout is configurable and defaults
to 5s, per tech-req §7.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from ai.contracts import InventoryRecord, OrderStatus, ShipmentStatus
from ai_service.tools.errors import ToolNotFound, ToolUnavailable

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 5.0


def base_url() -> str:
    return os.environ.get("MOCK_API_BASE_URL", "").strip() or DEFAULT_BASE_URL


def timeout_seconds() -> float:
    return float(os.environ.get("MOCK_API_TIMEOUT_SECONDS", "") or DEFAULT_TIMEOUT_SECONDS)


def _get(tool: str, path: str, timeout: float | None = None) -> dict:
    """One GET against the mock APIs, with every failure mode normalized.

    Returns the parsed JSON body, or raises ToolNotFound / ToolUnavailable.
    """
    url = f"{base_url()}{path}"
    try:
        response = httpx.get(url, timeout=timeout or timeout_seconds())
    except httpx.TimeoutException as exc:
        raise ToolUnavailable(tool, f"timed out after {timeout or timeout_seconds()}s") from exc
    except httpx.RequestError as exc:
        # Connection refused, DNS failure, etc. The service is simply not there.
        raise ToolUnavailable(tool, f"cannot reach {url}: {exc}") from exc

    if response.status_code == 404:
        raise ToolNotFound(tool, _detail(response, default="not found"))
    if response.status_code >= 400:
        raise ToolUnavailable(
            tool,
            _detail(response, default=f"HTTP {response.status_code}"),
            status_code=response.status_code,
        )

    try:
        return response.json()
    except ValueError as exc:
        raise ToolUnavailable(tool, "upstream returned a non-JSON body") from exc


def _detail(response: httpx.Response, default: str) -> str:
    """Pull the mock APIs' {"detail": "..."} message out, tolerating a body
    that isn't the shape we expect — an error path must not itself error."""
    try:
        body = response.json()
    except ValueError:
        return default
    detail = body.get("detail") if isinstance(body, dict) else None
    return str(detail) if detail else default


def get_order_status(order_no: str, timeout: float | None = None) -> OrderStatus:
    """Mock ERP API. Backs the `get_order_status` MCP tool (tech-req §4.1)."""
    logger.info("tool=get_order_status order_no=%s", order_no)
    return OrderStatus(**_get("get_order_status", f"/api/order/{order_no}", timeout))


def get_shipment_status(tracking_no: str, timeout: float | None = None) -> ShipmentStatus:
    """Mock shipment-tracking API. Backs the `get_shipment_status` MCP tool."""
    logger.info("tool=get_shipment_status tracking_no=%s", tracking_no)
    return ShipmentStatus(
        **_get("get_shipment_status", f"/api/shipment/status/{tracking_no}", timeout)
    )


def get_inventory(sku: str, timeout: float | None = None) -> InventoryRecord:
    """Mock inventory/WMS API. Backs the `get_inventory` MCP tool."""
    logger.info("tool=get_inventory sku=%s", sku)
    return InventoryRecord(**_get("get_inventory", f"/api/inventory/{sku}", timeout))
