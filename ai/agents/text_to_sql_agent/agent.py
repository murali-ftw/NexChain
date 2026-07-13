"""P3.5 Text-to-SQL Agent.

Pipeline: schema-aware prompt -> LLM SQL generation -> validation ->
one retry on validation failure -> validated safe SQL. Does not execute
against a database — there is no live DB yet (Person 2's MCP
`db_query`, `ai/contracts.py`, still raises `NotImplementedError`). The
LangGraph node that drops this into `CoPilotState.sql_result` is P3.8,
not this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ai.agents.text_to_sql_agent.prompts import build_prompt, build_retry_prompt
from ai.agents.text_to_sql_agent.schema_context import build_schema_context
from ai.agents.text_to_sql_agent.validator import ValidationResult, extract_tables, validate_sql
from ai.contracts import MAX_RETRIES_PER_NODE
from ai.llm_client import generate

MAX_ATTEMPTS = 1 + MAX_RETRIES_PER_NODE

_FENCE_RE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

SCHEMA_CONTEXT = build_schema_context()


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


@dataclass
class TextToSQLResult:
    sql: str | None
    valid: bool
    reason: str | None
    tables: list[str] = field(default_factory=list)
    abstained: bool = False
    attempts: int = 0


def generate_sql(question: str, intent_hint: str | None = None) -> TextToSQLResult:
    """Generate and validate a SELECT statement for a business question.

    Retries generation once (`MAX_RETRIES_PER_NODE`) on validation
    failure, feeding the prior SQL and rejection reason back to the
    model, then abstains cleanly rather than returning unsafe or
    unvalidated SQL.
    """
    previous_sql: str | None = None
    result: ValidationResult | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt == 1:
            prompt = build_prompt(question, SCHEMA_CONTEXT, intent_hint=intent_hint)
        else:
            prompt = build_retry_prompt(
                question,
                SCHEMA_CONTEXT,
                previous_sql=previous_sql or "",
                failure_reason=result.reason if result else "unknown",
                intent_hint=intent_hint,
            )

        raw_sql = generate(prompt)
        candidate = _strip_fences(raw_sql)
        result = validate_sql(candidate)

        if result.valid and result.safe_sql:
            return TextToSQLResult(
                sql=result.safe_sql,
                valid=True,
                reason=None,
                tables=extract_tables(result.safe_sql),
                abstained=False,
                attempts=attempt,
            )
        previous_sql = candidate

    return TextToSQLResult(
        sql=None,
        valid=False,
        reason=result.reason if result else "generation failed",
        tables=[],
        abstained=True,
        attempts=MAX_ATTEMPTS,
    )
