"""Database access for the AI layer (P2.6).

Connects as `copilot_readonly` (db/migrations/002_roles.sh), which can SELECT
the ten Text-to-SQL-allowlisted tables and nothing else — it cannot write
anything, and cannot read `users` or `audit_log` at all. That grant is the
enforcement layer; the SQL validator on top of it is defense in depth, not the
only defense.

Backs the `db_query` MCP tool (P2.7). Failures are normalized to ToolError like
every other tool (tech-req §7).

# ponytail: SELECT-only parsing, the table allowlist, row limits, and the
# statement timeout are P2.9 (Day 9) — SQL_TABLE_ALLOWLIST / SQL_DENIED_KEYWORDS
# / SQL_ROW_LIMIT already exist in ai/contracts.py, unenforced here on purpose.
# Until then the read-only role is what stands between a bad query and the data,
# which is why run_select() is not exposed over HTTP by anything yet.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

from ai_service.tools.errors import ToolError, ToolUnavailable

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

logger = logging.getLogger(__name__)

DEFAULT_DSN = "postgresql://copilot_readonly@localhost:5432/nexchain"
DEFAULT_TIMEOUT_SECONDS = 5.0
TOOL = "db_query"


def dsn() -> str:
    return os.environ.get("AI_SERVICE_DATABASE_URL", "").strip() or DEFAULT_DSN


def timeout_seconds() -> float:
    return float(os.environ.get("AI_SERVICE_DB_TIMEOUT_SECONDS", "") or DEFAULT_TIMEOUT_SECONDS)


def run_select(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a read query and return its rows as dicts.

    `connect_timeout` only bounds establishing the connection; `statement_timeout`
    (P2.9) bounds the query itself, so a pathological SELECT (e.g. an
    unintentionally expensive join let through by the table allowlist) can't
    hang this call indefinitely. A cancelled statement surfaces as
    psycopg.errors.QueryCanceled, a psycopg.OperationalError subclass already
    handled below as a retryable ToolUnavailable.

    # ponytail: a connection per call, same as mock_apis/db.py. A pool is worth
    # it once the graph fans out several tool calls per question; it isn't yet.
    """
    logger.info("tool=%s sql=%s", TOOL, sql)
    try:
        with psycopg.connect(
            dsn(),
            row_factory=dict_row,
            connect_timeout=int(timeout_seconds()),
            options=f"-c statement_timeout={int(timeout_seconds() * 1000)}",
        ) as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    except psycopg.OperationalError as exc:
        raise ToolUnavailable(TOOL, f"cannot reach the database: {exc}") from exc
    except psycopg.errors.InsufficientPrivilege as exc:
        # The read-only role refused it. Permanent — the same query will be
        # refused every time, so this must NOT be retryable or the node wastes
        # its single retry (MAX_RETRIES_PER_NODE) on a guaranteed failure.
        raise ToolError(
            TOOL, f"permission denied: {exc}", retryable=False, status_code=403
        ) from exc
    except psycopg.Error as exc:
        raise ToolUnavailable(TOOL, f"query failed: {exc}") from exc


def get_order(order_no: str) -> dict | None:
    """The order as the *system of record* has it — customer, warehouse, SLA
    tier and dates, which the ERP API's OrderStatus shape doesn't carry.

    This is the DB-side counterpart to api_client.get_order_status(); the
    Business Rule Agent needs the customer's sla_tier and the warehouse to
    decide breach/escalation, and neither is on the API response. Backs the
    `get_order()` MCP tool (P2.7).
    """
    rows = run_select(
        """
        SELECT so.order_no,
               so.current_status,
               so.order_date,
               so.promised_delivery_date,
               so.revised_delivery_date,
               so.total_amount,
               c.customer_code,
               c.customer_name,
               c.sla_tier,
               w.warehouse_code,
               w.location AS warehouse_location
        FROM sales_orders so
        JOIN customers c ON c.customer_id = so.customer_id
        JOIN warehouse w ON w.warehouse_id = so.warehouse_id
        WHERE so.order_no = %s
        """,
        (order_no,),
    )
    return rows[0] if rows else None
