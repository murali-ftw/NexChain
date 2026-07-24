# Day 14 — Demo Results

Live evidence from the full Docker Compose stack (`infra/docker-compose.yml`,
all 6 services healthy), run against a freshly seeded database
(`db/seed_data.sql`) with a real Gemini key configured. Every response below
is copy-pasted from an actual `curl` against `POST /api/chat` through the
complete Angular-facing chain: **Spring Boot → FastAPI → LangGraph → MCP →
Postgres / mock APIs**. See [README.md](../README.md) for architecture, tech
stack, security, and known limitations — this document only records results.

## Auth

Seeded demo accounts (`InMemoryUserStore`): `user@example.com` / `password`
(role `USER`), `admin@example.com` / `password` (role `ADMIN`, required for
`/api/audit`).

## 1. Flagship scenario — SO-45892 (customs hold, SLA breach)

**Question:** *"Where is customer order SO-45892? Why is it delayed and what
action should we take?"*

```json
{
  "answerText": "Order SO-45892 is currently Delayed. Shipment status: Customs Hold at Chennai Port. Cause: HS code mismatch during customs validation. SLA status: Breached (6 day(s) past the promised date). Escalated to: Logistics Manager.",
  "intent": "MULTI_TOOL_QUERY",
  "orderStatus": "Delayed",
  "shipmentStatus": "Customs Hold",
  "currentLocation": "Chennai Port",
  "delayReason": "HS code mismatch during customs validation.",
  "promisedDeliveryDate": "2026-07-03",
  "revisedDeliveryDate": "2026-07-09",
  "delayDays": 6,
  "slaStatus": "Breached",
  "recommendedActions": [
    "Verify the HS code in the commercial invoice against product master data (Customs Hold SOP step 1).",
    "Send the corrected commercial invoice to the customs broker for re-validation (Customs Hold SOP step 3).",
    "Escalate to the Logistics Manager (Customs Hold SOP step 6 / Escalation Matrix).",
    "Notify the customer with the revised ETA per the Customer Notification Policy (Customs Hold SOP step 7)."
  ],
  "sources": [
    { "documentName": "Customs Hold SOP", "score": 0.6335 },
    { "documentName": "Customer Notification Policy", "score": 0.4318 }
  ],
  "partial": false,
  "warnings": [],
  "agentsInvoked": ["intent_classifier", "api_status_agent", "knowledge_base_agent", "business_rule_agent", "final_response_agent"]
}
```

Every step of the flagship acceptance flow (team_plan.md §9) is visible in
this single response: order + shipment data pulled via MCP tools, SLA breach
detected deterministically by the business-rule engine, SOP guidance
retrieved and cited by RAG, and a final structured answer with no free-text
parsing required on the Angular side.

## 2. Pure knowledge query

**Question:** *"What is our SLA policy for shipment delays?"*

- `intent`: `KNOWLEDGE_QUERY`
- 3 sources retrieved and cited
- `partial: false`

## 3. Pure database query

**Question:** *"How many sales orders are currently delayed?"*

- `intent`: `DATABASE_QUERY`
- `answerText`: "There are currently 11 sales orders that are delayed."
- `generatedSql`: `SELECT COUNT(*) FROM sales_orders WHERE current_status = 'Delayed' LIMIT 200`
- Validated against the SELECT-only/table-allowlist/row-cap guardrails (P2.9) before execution.

## 4. Non-flagship SLA breach — SO-10288

**Question:** *"Is order SO-10288 breaching its SLA? What should we do?"*

- `intent`: `MULTI_TOOL_QUERY`
- `slaStatus`: `Breached`, `delayDays`: `5` — matches `db/verify_scenarios.sql` PASS 8 exactly.
- Cause: carrier congestion; escalated to Logistics Coordinator; SOP citations from Carrier Delay Handling SOP, Force Majeure & Exception Handling Policy, Customer Notification Policy.

## 5. Order status lookup — SO-30002

**Question:** *"Do we have enough inventory to fulfill order SO-30002?"*

- `intent`: `DATABASE_QUERY`
- `answerText`: "Order SO-30002 is currently Pending."
- `partial: false`

## Audit trail (admin-only, `GET /api/audit`)

Every turn above is persisted with full traceability:

```json
{
  "auditId": 6,
  "user": "demo-user",
  "rawQuestion": "Is order SO-10288 breaching its SLA? What should we do?",
  "detectedIntent": ["MULTI_TOOL_QUERY"],
  "agentsInvoked": ["intent_classifier", "api_status_agent", "knowledge_base_agent", "business_rule_agent", "final_response_agent"],
  "kbSources": [ { "documentName": "Carrier Delay Handling SOP", "score": 0.4059 }, "..." ],
  "slaResult": "Breached",
  "status": "SUCCESS",
  "warnings": []
}
```

Confirms the audit view's completion gate (P1.8): every test query has a
visible audit record with user, question, intent, agents, tools, and status.

## Test gate summary (Day 13 hardening, re-verified before this demo)

| Gate | Result |
|---|---|
| Angular (`ng test`, 83 specs) | 83/83 pass |
| Spring Boot (`mvnw test`) | full suite pass |
| `db/verify_scenarios.sql` | 11/11 (gate requires ≥ 10) |
| `db/verify_crud.sql` | FKs enforced, CRUD works |
| `mock_apis/` pytest | 17/17 pass |
| `ai_service/` pytest | 25/25 pass |
| `mcp_server/` pytest | 23/23 pass |

## Note on `partial`/degraded responses

Without `LLM_PRIMARY_API_KEY` configured, every response above still
returns correct database/API-sourced fields (order status, SLA verdict,
delay days) but with `partial: true`, an empty `sources` array, and a
`warnings` entry — by design (README "Graceful degradation"). The results
recorded here were captured with a real Gemini key wired into
`infra/.env`, which is why `sources` are populated and `partial` is
`false` throughout.
