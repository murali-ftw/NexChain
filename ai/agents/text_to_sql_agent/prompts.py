"""Schema-aware Text-to-SQL prompt template.

Provider-agnostic by design: plain text prompt in, plain text SQL out
— same convention as the Knowledge Base Agent's `prompts.py`. The model
is instructed to return raw SQL only; `agent.py` still defensively
strips markdown fences in case that's ignored.
"""

from __future__ import annotations

_SYSTEM_INSTRUCTIONS = """You are the Text-to-SQL Agent for a supply chain co-pilot.
Generate a single PostgreSQL SELECT statement that answers the business question, using ONLY the schema below.

Rules:
- Output ONLY the raw SQL statement. No prose, no explanation, no markdown code fences.
- SELECT statements only — never INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
- Only reference tables and columns from the schema below — never any other table.
- Always include a LIMIT clause of at most 200 rows.
- Match status/enum values exactly as they appear in the schema (case and spacing)."""


def _hint_line(intent_hint: str | None) -> str:
    return f"\nBusiness intent hint: {intent_hint}\n" if intent_hint else ""


def build_prompt(
    question: str, schema_context: str, intent_hint: str | None = None
) -> str:
    return (
        f"{_SYSTEM_INSTRUCTIONS}\n\n"
        f"--- SCHEMA ---\n{schema_context}\n--- END SCHEMA ---\n"
        f"{_hint_line(intent_hint)}\n"
        f"Question: {question}\n"
        f"SQL:"
    )


def build_retry_prompt(
    question: str,
    schema_context: str,
    previous_sql: str,
    failure_reason: str,
    intent_hint: str | None = None,
) -> str:
    return (
        f"{_SYSTEM_INSTRUCTIONS}\n\n"
        f"--- SCHEMA ---\n{schema_context}\n--- END SCHEMA ---\n"
        f"{_hint_line(intent_hint)}\n"
        f"Question: {question}\n\n"
        f"Your previous attempt was rejected:\n{previous_sql}\n"
        f"Reason: {failure_reason}\n"
        f"Generate a corrected SQL statement that fixes this issue.\n"
        f"SQL:"
    )
