# API Contracts — Application Layer (Person 1)

## Project: Supply Chain Intelligence Co-Pilot

Frozen on **Day 2 (P1.2 — Spring Boot Foundation)** by Person 1. Documents every
endpoint Angular calls on Spring Boot. Where a field's shape is inherited from
Person 3's frozen `ai/contracts.py` (P3.1), that's noted explicitly. Anything
marked `PROVISIONAL - REQUIRES TEAM APPROVAL` has NOT been agreed by Person 2
or Person 3 yet.

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
    "warnings": ["Day 2 mock response — no real AI pipeline yet (see P1.10, Day 11)."],
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
    addition with an alternative.
  - `traceId`, `sessionId`, `timestamp`, `warnings` are Spring Boot's own
    application-layer envelope — Person 1's addition, not part of Person 3's
    contract.
- **Day 2 status:** **Controlled mock.** If `query` contains "45892" (case-insensitive), returns the full flagship scenario above. Otherwise returns a minimal generic mock (`answerText` echoes the query, all optional fields null, `slaStatus: "N/A"`). No real intent classification, SQL, RAG, or API calls — that's Person 3's work (P3.7–P3.11).
- **Owner:** Person 1 (contract + mock). Real implementation: Person 2 (transport) + Person 3 (content), landing at P1.10 (Day 11).

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
- **Day 2 status:** **Contract stub.** Always returns `[]`. No persistence. Real implementation is P1.7 (Day 7).
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
- **Day 2 status:** **Contract stub.** Always returns `[]`. No persistence, no authorization. Real implementation is P1.8 (Day 8).
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

`PROVISIONAL - REQUIRES TEAM APPROVAL` — not yet agreed with Person 2 or Person 3.

Conceptual expectation once P1.10 (Day 11) lands:

```
POST /ai/query
```

- **Request (proposed):** `{ "query": string, "sessionId": string, "traceId": string }` — `traceId` generated by Spring Boot so a single ID correlates the request across Spring Boot → FastAPI → LangGraph → MCP, per `docs/02_technical_requirements.md` §9 (Observability).
- **Response (proposed):** the `CoPilotResponse` shape in `ai/contracts.py`, extended with the `promisedDeliveryDate`/`revisedDeliveryDate` fields flagged above.
- **Error behavior (proposed):** Person 2's FastAPI service returns a non-200 on failure; Spring Boot maps that to a `ChatResponse` with `partial: true` and a populated `warnings` entry, never a raw 5xx passthrough to Angular.
- **Correlation (proposed):** `traceId` is generated in Spring Boot at the start of every `/api/chat` request (already implemented today, see `ChatService`) and must be threaded through unchanged by FastAPI, LangGraph, and MCP so `docs/06_backend_schema.md`'s `audit_log.trace_id` column can correlate the full request across all three services.

None of the above is implemented. It is documented now so Person 2 and Person 3 can react to it early, per the Day 2 cross-team responsibility in `docs/team_plan.md`.

------------------------------------------------------------------------

## Related Documents

- [Technical Requirements](./02_technical_requirements.md)
- [App Flow](./05_app_flow.md)
- [Backend Schema](./06_backend_schema.md)
- [Team Plan](./team_plan.md)
