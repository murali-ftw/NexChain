"""Thin boundary over the not-yet-live database.

This is the swap point called out in the P3.5 spec: once Person 2's
`db_query` MCP tool exists, replace the body of `db_query()` with an
MCP client call. Its return shape already matches the frozen `DBResult`
contract (ai/contracts.py), so nothing above this function — the
agent, validator, or the prompt — needs to change.
"""

from __future__ import annotations

from ai.contracts import DBResult
from ai.contracts import db_query as _db_query_stub


def db_query(sql: str) -> DBResult:
    """Execute already-validated SELECT SQL. Raises NotImplementedError
    until Person 2's live MCP db_query tool replaces this passthrough."""
    return _db_query_stub(sql)
