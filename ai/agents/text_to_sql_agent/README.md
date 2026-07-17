# Text-to-SQL Agent (P3.5, Day 5)

## Status (as of commit)

Validator passes its adversarial suite **14/14** (parse failures, denied
keywords, denied tables, missing/over-limit `LIMIT`, multi-statement
injection). Generation eval (`test_questions.py`, live Gemini run)
scores **20/20** — clears the P3.6 gate (`docs/team_plan.md`, >= 15/20)
comfortably, including the flagship SO-45892 question generating a
correct `sales_orders` + `customers` + `sla_rules` join on `sla_tier`.

**Execution against a live database is PENDING Person 2's DB** — the MCP
`db_query` tool (`ai/contracts.py`) still raises `NotImplementedError`,
so the completion gate is only **partially met**: SQL generation and
safety validation are fully proven; execution correctness against real
data is unverified until Person 2's database and MCP tool (P2.8) land.

Converts a natural-language business question into a validated, read-only
SQL query against the 10 allowlisted tables. Does **not** build the
LangGraph node or graph (P3.8) — it returns a plain result object a future
node can drop into `CoPilotState.sql_result`. Does **not** do intent
classification (P3.7) — `generate_sql()` takes an optional `intent_hint`
string param instead.

## Pipeline

1. **Schema-aware prompting** (`schema_context.py` + `prompts.py`) — a
   compact, static description of the 10 allowlisted tables (columns, FK
   relationships, enum values) is folded into a plain-text prompt
   instructing SELECT-only, allowlisted-tables-only, `LIMIT 200`, raw SQL
   output (no prose/fences).
2. **Generation** (`agent.py` + `ai/llm_client.py`) — calls Gemini for a
   SQL candidate, defensively stripping markdown fences.
3. **Validation** (`validator.py`) — the safety-critical gate: parses with
   `sqlglot`, rejects non-`SELECT`/multi-statement/denied-keyword/
   denied-table SQL, and enforces `SQL_ROW_LIMIT` (injecting or clamping
   `LIMIT`). Never executes anything — it only accepts or rejects a string.
4. **One retry** — if validation fails, the agent retries generation once
   (`MAX_RETRIES_PER_NODE` in `ai/contracts.py`), feeding the prior SQL and
   rejection reason back into the prompt. If both attempts fail, the agent
   abstains cleanly (`TextToSQLResult(abstained=True, sql=None, ...)`)
   rather than ever returning unsafe or unvalidated SQL.

## Running the eval (completion gate)

```bash
# from repo root, with deps from requirements.txt installed
python -m ai.agents.text_to_sql_agent.eval
```

Gate (`docs/team_plan.md` P3.6): **>= 15 of the 20 curated questions**
(`test_questions.py`) must generate valid, allowlisted SQL touching the
expected tables. Since there's no live DB yet, this grades generation +
validation correctness, not query-result correctness. **Live result:
20/20 passed** (Day 5, `gemini-flash-latest`) — GATE MET.

If generation succeeds but the LLM call fails (most commonly: no key
configured), the eval reports that question as `SKIPPED`.

## LLM provider

Shared `ai/llm_client.py` (Gemini-only, see its module docstring) — same
provider and config (`ai/.env`, `LLM_PRIMARY_*`) as the Knowledge Base
Agent. No keys are hardcoded anywhere.

## Swap point for Person 2's `db_query`

`db_boundary.py: db_query()` is the only place that will talk to the live
database. It already returns the frozen `DBResult` contract shape
(`ai/contracts.py`). Right now it passes straight through to
`ai.contracts.db_query`, which raises `NotImplementedError("Owned by
Person 2 via MCP")` — that's intentional, not a bug. When Person 2's MCP
tool is live, replace this function's body with an MCP client call;
nothing in `agent.py`, `validator.py`, or `prompts.py` needs to change.
Note `agent.py` does not call `db_boundary.py` at all yet — P3.5 stops at
validated SQL, by design; wiring execution in is a later step, once a real
database exists to execute against.

## Files

| File | Responsibility |
|---|---|
| `validator.py` | Safety-critical SQL validator — parse, SELECT-only, allowlist, keyword-deny, row-limit |
| `schema_context.py` | Compact schema description of the 10 allowlisted tables, for prompting |
| `prompts.py` | Provider-agnostic Text-to-SQL prompt (initial + retry variants) |
| `db_boundary.py` | Thin boundary over `ai.contracts.db_query` — the live-DB swap point |
| `agent.py` | Orchestration: prompt -> generate -> validate -> one retry -> `TextToSQLResult` |
| `test_questions.py` | 20 curated business questions (filters, joins, aggregations, dates/warehouse/delay, flagship) |
| `eval.py` | Runs the question set, reports pass/fail against the completion gate |
