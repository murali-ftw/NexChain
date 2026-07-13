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

## Running

```bash
.venv/bin/uvicorn ai_service.main:app --port 8001 --reload
# interactive docs: http://localhost:8001/docs
```

Port 8001 by convention: 8080 is Spring Boot, 8000 is `mock_apis`, 4200 Angular.
Needs no database and no LLM key — the P2.5 boundary has neither.

## Completion gate

```bash
.venv/bin/python -m pytest ai_service/ -v
```

10 tests. The load-bearing one is
`test_response_fields_cover_spring_boot_chat_response`, which **parses Person 1's
actual `ChatResponse.java`** and asserts our JSON carries every field it expects
(minus `timestamp`/`warnings`, which Spring Boot fills in itself). If Person 1
adds a field to their DTO, that test fails instead of the contract drifting
quietly until integration day.
