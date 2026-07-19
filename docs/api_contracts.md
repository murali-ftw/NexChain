# API Contracts — Application Layer (Person 1)

## Project: Supply Chain Intelligence Co-Pilot

Frozen on **Day 2 (P1.2 — Spring Boot Foundation)** by Person 1, updated on
**Day 4 (P1.4 — Spring Boot Core APIs)**. Documents every endpoint Angular
calls on Spring Boot. Where a field's shape is inherited from Person 3's
frozen `ai/contracts.py` (P3.1), that's noted explicitly. Anything marked
`PROVISIONAL - REQUIRES TEAM APPROVAL` has NOT been agreed by Person 2 or
Person 3 yet.

**Day 4 headline change:** `POST /api/chat` is now Angular's real, only
success path (no more frontend-only mock) — see that section below for the
full deterministic mock-routing table and verification notes.

------------------------------------------------------------------------

## Angular → Spring Boot

### `GET /api/health`

- **Purpose:** connectivity check — proves Spring Boot is reachable and returns JSON.
- **Request:** none.
- **Success response (200):**
  ```json
  { "status": "UP", "service": "backend-api" }
  ```
- **Day 2 status:** Working mock — this is the real, permanent health check (not a stub to be replaced later).
- **Owner:** Person 1.

------------------------------------------------------------------------

### `POST /api/auth/login`

- **Purpose:** eventually authenticate users and issue JWT tokens.
- **Request:**
  ```json
  { "email": "user@example.com", "password": "password" }
  ```
  Validation: `email` required + must be a valid address; `password` required, non-blank. No password strength rules yet.
- **Success response (200):**
  ```json
  {
    "accessToken": "mock-token",
    "refreshToken": null,
    "tokenType": "Bearer",
    "expiresIn": 3600,
    "user": { "id": 1, "username": "demo-user", "email": "user@example.com", "role": "USER" }
  }
  ```
- **Validation error (400):** see [Error Response Shape](#error-response-shape) below.
- **Day 2 status:** **Contract stub.** `accessToken` is a fixed literal string, not a real JWT. No password hashing, no user store, no Spring Security. Real implementation is P1.6 (Day 6).
- **Owner:** Person 1. No cross-team dependency.

------------------------------------------------------------------------

### `POST /api/chat`

- **Purpose:** receive a natural-language supply-chain question from Angular. Spring Boot will eventually forward this to Person 2's FastAPI AI service (see [Spring Boot → FastAPI](#spring-boot--fastapi) below).
- **Request:**
  ```json
  { "query": "Where is order SO-45892?", "sessionId": "optional-session-id" }
  ```
  Validation: `query` required, non-blank. `sessionId` optional — if omitted, Spring Boot generates one.
- **Success response (200):**
  ```json
  {
    "traceId": "uuid",
    "sessionId": "uuid",
    "timestamp": "2026-07-08T05:35:40.191213Z",
    "answerText": "Order SO-45892 has been dispatched from the warehouse.",
    "intent": "MULTI_TOOL_QUERY",
    "orderStatus": "Dispatched",
    "shipmentStatus": "Customs Hold",
    "currentLocation": "Chennai Port",
    "delayReason": "HS code mismatch during customs validation.",
    "promisedDeliveryDate": "2026-07-03",
    "revisedDeliveryDate": "2026-07-09",
    "delayDays": 6,
    "slaStatus": "Breached",
    "recommendedActions": [
      "Verify the HS code in the commercial invoice.",
      "Send the corrected document to the customs broker.",
      "Escalate to the logistics manager.",
      "Notify the customer with the revised ETA."
    ],
    "sources": [],
    "partial": false,
    "warnings": ["Day 4 mock response — no real AI pipeline yet (see P1.10, Day 11)."],
    "error": null
  }
  ```
- **Validation error (400):** blank/missing `query` → see [Error Response Shape](#error-response-shape).
- **Schema provenance:** `answerText` through `error` mirror `CoPilotResponse` in
  `ai/contracts.py` (Person 3, P3.1, frozen Day 1) field-for-field — **do not
  rename these without Person 3's sign-off.**
  - `intent` reuses Person 3's `RoutingCategory` enum (`KNOWLEDGE_QUERY` /
    `DATABASE_QUERY` / `API_QUERY` / `MULTI_TOOL_QUERY`) verbatim.
  - `slaStatus` reuses Person 3's `SLAStatus` wire strings (`"On Time"` / `"At Risk"` / `"Breached"` / `"N/A"`) verbatim.
  - `PROVISIONAL - REQUIRES TEAM APPROVAL`: `promisedDeliveryDate` and
    `revisedDeliveryDate` are **not** present in the current
    `ai/contracts.py CoPilotResponse`. They were added here because
    `docs/04_ui_ux_design.md` §3.2 (Impact table) and the flagship sample in
    `docs/problem_statement.md` §7 both require them. **Needs Person 3 to fold
    these back into the frozen Python contract**, or explicitly reject the
    addition with an alternative. Still unresolved as of Day 4.
  - `traceId`, `sessionId`, `timestamp`, `warnings` are Spring Boot's own
    application-layer envelope — Person 1's addition, not part of Person 3's
    contract.
- **CURRENT DAY 4 IMPLEMENTATION: SPRING BOOT TEMPORARY MOCK RESPONSE.** Deterministic
  keyword matching in `ChatService.getMockResponse()`, in priority order:
  1. `query` contains `"45892"` → full flagship delay/SLA-breach scenario (above).
  2. `query` contains `"sku"` or `"stock"` → inventory scenario (`DATABASE_QUERY`, no impact fields).
  3. `query` contains `"sla"` or `"escalation"` → SLA/SOP scenario (`KNOWLEDGE_QUERY`, 2 KB sources).
  4. `query` contains `"warehouse"` or `"report"` → reporting scenario (`DATABASE_QUERY`, prose result).
  5. Anything else → generic mock (`answerText` echoes the query, all optional fields null, `slaStatus: "N/A"`).
  No real intent classification, SQL, RAG, or API calls — that's Person 3's work (P3.7–P3.11).
- **Day 4 status:** this is now Angular's **primary, only** success path for chat — the
  Day 3 frontend-only `ChatMockService` has been removed. Angular's `ChatApiService`
  (`frontend/src/app/features/chat/services/chat-api.service.ts`) POSTs here directly via
  `HttpClient`; verified with a real browser (headless Chrome via CDP) — genuine CORS
  preflight + POST, 200 response, full structured render, for both manually-typed
  questions and suggested-question clicks. Two frontend-only local triggers remain by
  design, per the Day 4 task's explicit allowance for isolated test scenarios that Spring
  Boot has no reason to simulate itself: a query containing `"simulate error"` rejects
  locally without an HTTP call, and `"simulate degraded"` returns the local
  `DEGRADED_RESPONSE` fixture (`partial: true` + a populated `warnings` entry) — both
  implemented directly in `ChatPageComponent`, not via any mock service.
- **Owner:** Person 1 (contract + mock + Angular transport). Real AI content: Person 2 (transport) + Person 3 (content), landing at P1.10 (Day 11).

------------------------------------------------------------------------

### `GET /api/chat/history`

- **Purpose:** eventually return the authenticated user's previous queries and responses.
- **Request:** none (future: auth token, pagination).
- **Success response (200):**
  ```json
  [
    {
      "id": "string",
      "question": "string",
      "answerSummary": "string",
      "timestamp": "2026-07-08T05:35:40Z",
      "sessionId": "string"
    }
  ]
  ```
- **CURRENT DAY 4 IMPLEMENTATION: SPRING BOOT TEMPORARY MOCK RESPONSE.** Returns 3
  fixed, realistic mock records (`HistoryService.getMockHistory()`) — no persistence,
  no database. Angular's History page is **not** wired to this endpoint yet (out of
  today's mandatory scope per the Day 4 task; the mandatory integration target was
  Chat). Real persistence is P1.7 (Day 7).
- **Owner:** Person 1. No cross-team dependency.

------------------------------------------------------------------------

### `GET /api/audit`

- **Purpose:** eventually provide an admin-facing audit log.
- **Request:** none (future: auth token + role check, filters).
- **Success response (200):**
  ```json
  [
    {
      "auditId": 1,
      "traceId": "string",
      "timestamp": "2026-07-08T05:35:40Z",
      "user": "string",
      "rawQuestion": "string",
      "detectedIntent": ["order_status", "delay_analysis"],
      "agentsInvoked": ["text_to_sql_agent", "api_status_agent"],
      "generatedSql": "string | null",
      "apiCalls": [{ "endpoint": "string", "statusCode": 200, "latencyMs": 320 }],
      "kbSources": [{ "documentName": "string", "snippet": "string", "docId": 1, "score": 0.9 }],
      "slaResult": "Breached",
      "status": "string"
    }
  ]
  ```
  Field shape mirrors the `audit_log` table in `docs/06_backend_schema.md` §2.14.
- **CURRENT DAY 4 IMPLEMENTATION: SPRING BOOT TEMPORARY MOCK RESPONSE.** Returns 2
  fixed, realistic mock records (`AuditService.getMockAuditLog()`) covering every
  documented field, including a non-null `generatedSql` example — no persistence, no
  authorization. Real persistence is P1.8 (Day 8).
- **Owner:** Person 1. No cross-team dependency.

------------------------------------------------------------------------

## Error Response Shape

Every 4xx/5xx from any endpoint above returns this shape (never a stack trace):

```json
{
  "timestamp": "2026-07-08T05:35:40.212579Z",
  "status": 400,
  "error": "Bad Request",
  "message": "query: query must not be blank",
  "path": "/api/chat"
}
```

| Trigger | Status |
|---|---|
| Bean Validation failure (`@Valid` on request body) | 400 |
| Malformed JSON body | 400 |
| No controller mapped for the request path | 404 |
| Any other unhandled exception | 500 (logged server-side; message to client stays generic) |

------------------------------------------------------------------------

## CORS / Local Development

Spring Boot enforces CORS server-side (`CorsConfig`, `/api/**`), allowing only
`http://localhost:4200` (Angular's default `ng serve` port), configured via
`app.cors.allowed-origins` in `application.yml` — not a wildcard. Chosen over
an Angular proxy config because the allow-list lives on the server that will
eventually sit behind a real gateway in every environment, not just local dev,
and it's directly inspectable in the network tab during demos.

If a teammate runs Angular on a different port, update
`app.cors.allowed-origins` (comma-separated) rather than loosening it to `*`.

------------------------------------------------------------------------

## Spring Boot → FastAPI

Implemented as of P1.10 (Day 11) — `RestClientAiQueryClient`
(`backend-api/src/main/java/com/nexchain/backend/chat/client/`), live-verified
Day 12 against the real FastAPI service via `docker compose` (flagship query,
degraded-mode with `LLM_PRIMARY_API_KEY` unset, and SQL-injection/prompt-injection
probes — see the Day 12 release-hardening report).

```
POST /ai/query
```

- **Request:** `{ "query": string, "sessionId": string, "traceId": string }` — `traceId` generated by Spring Boot so a single ID correlates the request across Spring Boot → FastAPI → LangGraph → MCP, per `docs/02_technical_requirements.md` §9 (Observability).
- **Response:** the `CoPilotResponse` shape in `ai/contracts.py`, extended with the `promisedDeliveryDate`/`revisedDeliveryDate` fields flagged above.
- **Error behavior:** Person 2's FastAPI service returns a non-200 on failure; Spring Boot maps that to a `ChatResponse` with `partial: true` and a populated `warnings` entry, never a raw 5xx passthrough to Angular. `AiServiceConfig` bounds this with a 3s connect / 35s read timeout (`application.yml`); there is no retry at this layer (LangGraph's own `MAX_RETRIES_PER_NODE` already covers per-node retry inside the AI pipeline).
- **Correlation:** `traceId` is generated in Spring Boot at the start of every `/api/chat` request (`ChatService`) and threaded through unchanged by FastAPI, LangGraph, and MCP so `docs/06_backend_schema.md`'s `audit_log.trace_id` column can correlate the full request across all three services.

------------------------------------------------------------------------

## Related Documents

- [Technical Requirements](./02_technical_requirements.md)
- [App Flow](./05_app_flow.md)
- [Backend Schema](./06_backend_schema.md)
- [Team Plan](./team_plan.md)
