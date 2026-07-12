"""Read-only Postgres access for the mock enterprise APIs.

The mock APIs read the same seeded database (db/seed_data.sql) rather than
carrying their own hardcoded fixtures. Two reasons: the P2.4 spec requires
responses to be "deterministic per seed data" (docs/03_implementation_plan.md
Phase 3), and a second copy of the scenario data would silently drift from the
first the moment either changed.

Connects as `copilot_readonly` (db/migrations/002_roles.sh) so the simulated
external systems physically cannot write to the system of record, even by
accident.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

_ENV_PATH = Path(__file__).resolve().parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

DEFAULT_DSN = "postgresql://copilot_readonly@localhost:5432/nexchain"


class MockApiConfigError(RuntimeError):
    """MOCK_API_DATABASE_URL is missing or unusable."""


def dsn() -> str:
    return os.environ.get("MOCK_API_DATABASE_URL", "").strip() or DEFAULT_DSN


def fetch_one(sql: str, params: tuple) -> dict | None:
    """Run a single-row SELECT and return it as a dict, or None if no match.

    # ponytail: one connection per call. Fine for a mock service backing a demo;
    # switch to psycopg_pool.ConnectionPool if call volume ever makes it matter.
    """
    try:
        with psycopg.connect(dsn(), row_factory=dict_row, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()
    except psycopg.OperationalError as exc:
        raise MockApiConfigError(f"Cannot reach the database: {exc}") from exc
