# FastAPI AI Service (P2.5, Day 5)

The hosting boundary between Spring Boot and the LangGraph agent layer. This is
the service Person 1's `/api/chat` will call at P1.10.

Not to be confused with [`mock_apis/`](../mock_apis/) (P2.4), which simulates
the *external* ERP / shipment / inventory systems on its own port. That's a
system the AI layer calls; this is the AI layer's front door.

| Endpoint | Purpose |
|---|---|
| `GET /health` | `{"status": "UP", "service": "ai-service"}` |
| `POST /ai/query` | Answer a question. Request `{query, sessionId, traceId}`, response = `CoPilotResponse` + envelope. |

## Status: the boundary is real, the answer is not

`POST /ai/query` returns a **temporary placeholder** — no intent
classification, no tools, no LLM. That's the P2.5 scope: the completion gate is
"Spring Boot can send a question and receive valid JSON", so the *shape* is the
deliverable and the LangGraph pipeline behind it lands at P2.10 (Day 11).

The placeholder sets `partial: true` and prefixes `answerText` with a disclaimer.
It deliberately does **not** invent a `warnings` field to say so — `warnings`
belongs to Spring Boot's ChatResponse envelope, and adding one here would be a
silent contract change.

Don't grow keyword routing in this endpoint to make the demo look better.
Spring Boot's `ChatService` already mocks that, and a second copy is just
another thing to delete at P2.10.

## Two cross-team decisions made here (need sign-off)

`docs/api_contracts.md` marks the whole Spring Boot → FastAPI section
`PROVISIONAL - REQUIRES TEAM APPROVAL` and asks Person 2 to react. This service
is that reaction. Both decisions are implemented and tested; neither is final
until Person 1 and Person 3 confirm.

**1. The wire is camelCase.** Spring Boot's records are camelCase; Person 3's
`ai/contracts.py` is snake_case. Neither side gets renamed: Python field names
stay snake_case (matching the frozen contract exactly) and Pydantic serializes
to camelCase via an alias generator. The JSON drops straight into Spring's
`ChatResponse` with no `@JsonProperty` annotations anywhere. Input accepts
either casing, so a Python caller doesn't have to speak camelCase.

**2. `promisedDeliveryDate` / `revisedDeliveryDate` live in this service, not in
`ai/contracts.py`.** Spring Boot's `ChatResponse` already carries them, flagged
provisional, because the UI Impact table (`docs/04_ui_ux_design.md` §3.2) and the
flagship sample (`docs/problem_statement.md` §7) both need them — but
`CoPilotResponse` doesn't have them. Person 3 owns that file and shared contracts
may not be changed silently (`docs/team_plan.md`), so `AiQueryResponse`
**subclasses** `CoPilotResponse` and adds the two fields rather than editing it.

> **If Person 3 folds those two fields into `CoPilotResponse`, delete the two
> declarations in `schemas.py` — the subclass then collapses to just the
> correlation envelope.**

## Tool access layer — `tools/` (P2.6, Day 6)

How the AI layer reaches the database and the mock APIs. The MCP tools (P2.7,
P2.8) are built on these; agents never call HTTP or SQL directly (tech-req §7).

| Module | Provides |
|---|---|
| `tools/api_client.py` | `get_order_status` / `get_shipment_status` / `get_inventory` → `mock_apis` over HTTP, 5s timeout (configurable) |
| `tools/db.py` | `run_select()` and `get_order()` → Postgres as `copilot_readonly` |
| `tools/errors.py` | `ToolError` / `ToolNotFound` / `ToolUnavailable` |

**Every failure is normalized to `ToolError`** — a raw `httpx` or `psycopg`
exception never escapes this layer, because tech-req §7 requires a tool to
"report a clear 'service unavailable' status rather than crashing the graph".

The part that matters downstream is **`retryable`**. Each LangGraph node gets
exactly one retry (`MAX_RETRIES_PER_NODE`), so a failure that can't succeed on a
second attempt must not consume it:

- `ToolNotFound` (404, no such order/SKU/tracking number) — **not** retryable.
  It's a fact about the data, not an outage. The agent should say "no such
  order", not "service unavailable".
- Permission denied from the read-only role — **not** retryable. The same query
  gets refused every time.
- Timeout, connection refused, 5xx — retryable.

`tools/db.py` deliberately does **not** enforce SELECT-only, the table
allowlist, or row limits yet. Those constants already exist in `ai/contracts.py`
and get enforced at **P2.9** (Day 9). Until then the `copilot_readonly` grant is
what stands between a bad query and the data — which is why `run_select()` isn't
exposed over HTTP by anything.

## Logging

Configured once at process start via `ai.logging_setup.configure_logging("ai_service")`
(top of `main.py`) — every module below it just does `logging.getLogger(__name__)`.
Full detail (correlation id propagation, redaction, per-service defaults) is in
the root [README.md § Logging & Observability](../README.md#logging--observability);
the parts specific to this service:

- `RequestContextMiddleware` (`ai/logging_setup.py`) resolves the request's
  `X-Request-ID`/`X-Correlation-ID` (or mints one), and `query()` reconciles it
  with the `traceId` JSON field — whichever was supplied wins, and the result is
  re-bound so every log line for that request (graph nodes, tool calls,
  `mcp_client`) carries the same id via `ai.logging_setup.get_request_id()`.
- Set `LOG_LEVEL=DEBUG` to see diagnostic detail (e.g. `ai_service/tools/db.py`'s
  exact SQL text) — never in a shared environment, only a local terminal.
- `/health` is logged at DEBUG, not INFO, so a polling health check doesn't
  dominate the log.

## Running

```bash
cp ai_service/.env.example ai_service/.env   # DB DSN + mock-API base URL

.venv/bin/uvicorn mock_apis.main:app --port 8000   # the tool layer's upstream
.venv/bin/uvicorn ai_service.main:app --port 8001 --reload
# interactive docs: http://localhost:8001/docs
```

Port 8001 by convention: 8080 is Spring Boot, 8000 is `mock_apis`, 4200 Angular.
`POST /ai/query` itself still needs no database and no LLM key — the P2.5
placeholder doesn't call the tool layer. P2.10 is where the graph starts using it.

## Completion gates

```bash
.venv/bin/python -m pytest ai_service/ -v
```

22 tests: 10 for the P2.5 boundary, 12 for the P2.6 tool layer.

- **P2.5** — the load-bearing one is
  `test_response_fields_cover_spring_boot_chat_response`, which **parses Person 1's
  actual `ChatResponse.java`** and asserts our JSON carries every field it expects
  (minus `timestamp`/`warnings`, which Spring Boot fills in itself). If Person 1
  adds a field to their DTO, that test fails instead of the contract drifting
  quietly until integration day.
- **P2.6** — "FastAPI can retrieve one order, one shipment and one inventory
  record", plus every error path above. Needs a seeded database
  (`db/seed_data.sql`); mounts `mock_apis` in-process so no second server is
  needed. The cross-process run against a live `mock_apis` on port 8000 is
  covered in the session notes, not automated here.
