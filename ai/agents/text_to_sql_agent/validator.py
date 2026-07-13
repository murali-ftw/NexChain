"""Safety-critical validator for LLM-generated SQL.

This is the only thing standing between raw LLM output and a database
once Person 2's MCP `db_query` tool goes live (`ai/contracts.py`). It
must reject anything that isn't a single, allowlisted, keyword-clean
SELECT, and always return a row-limited statement.

All limits/allowlists are read from `ai/contracts.py` — never hardcoded
here, since that file is the frozen, jointly-owned source of truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from ai.contracts import SQL_DENIED_KEYWORDS, SQL_ROW_LIMIT, SQL_TABLE_ALLOWLIST

_DIALECT = "postgres"

_DENIED_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in SQL_DENIED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    valid: bool
    reason: str | None
    safe_sql: str | None


def _reject(reason: str) -> ValidationResult:
    return ValidationResult(valid=False, reason=reason, safe_sql=None)


def validate_sql(sql: str) -> ValidationResult:
    """Validate a single candidate SQL string, returning a safe, row-limited
    rewrite on success. Never raises — all failures come back as a
    `ValidationResult(valid=False, ...)`."""
    denied_hit = _DENIED_KEYWORD_RE.search(sql)
    if denied_hit:
        return _reject(f"contains denied keyword '{denied_hit.group(1).upper()}'")

    try:
        statements = sqlglot.parse(sql, read=_DIALECT)
    except ParseError as exc:
        return _reject(f"parse failure: {exc}")

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        return _reject(f"expected exactly one statement, found {len(statements)}")

    statement = statements[0]
    if not isinstance(statement, exp.Select):
        return _reject("not a SELECT statement")

    cte_aliases = {cte.alias for cte in statement.find_all(exp.CTE)}
    tables = {t.name for t in statement.find_all(exp.Table)} - cte_aliases
    disallowed = tables - SQL_TABLE_ALLOWLIST
    if disallowed:
        return _reject(f"references non-allowlisted table(s): {sorted(disallowed)}")

    existing_limit = statement.args.get("limit")
    if existing_limit is None:
        statement.set("limit", exp.Limit(expression=exp.Literal.number(SQL_ROW_LIMIT)))
    else:
        try:
            limit_value = int(existing_limit.expression.name)
        except (AttributeError, ValueError):
            return _reject("LIMIT clause has a non-numeric value")
        if limit_value > SQL_ROW_LIMIT:
            statement.set(
                "limit", exp.Limit(expression=exp.Literal.number(SQL_ROW_LIMIT))
            )

    return ValidationResult(
        valid=True, reason=None, safe_sql=statement.sql(dialect=_DIALECT)
    )


def extract_tables(safe_sql: str) -> list[str]:
    """Return the sorted table names an already-validated SELECT touches
    (CTE aliases excluded). For use on `ValidationResult.safe_sql` only."""
    statement = sqlglot.parse_one(safe_sql, read=_DIALECT)
    cte_aliases = {cte.alias for cte in statement.find_all(exp.CTE)}
    tables = {t.name for t in statement.find_all(exp.Table)} - cte_aliases
    return sorted(tables)
