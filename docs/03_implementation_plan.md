# Implementation Plan

## Project: Supply Chain Intelligence Co-Pilot

Derived from [Product Requirements](./01_product_requirements.md) and
[Technical Requirements](./02_technical_requirements.md). This document
breaks the build into phases, tasks, and acceptance criteria for the
team to execute against, expanding the original two-week plan.

------------------------------------------------------------------------

## 1. Suggested Repository Structure

```
NexChain/
├── docs/                        # This documentation set
├── frontend/                    # Angular app
│   └── src/app/{chat,history,audit,auth,shared}/
├── backend-api/                 # Java Spring Boot
│   └── src/main/java/.../{auth,session,audit,gateway}/
├── ai-service/                  # Python FastAPI
│   └── app/{graph,agents,llm,schemas}/
├── mcp-server/                  # Python MCP server + tools
│   └── tools/{kb_tool,db_tool,api_tool}.py
├── mock-apis/                   # Simulated ERP/WMS/TMS/Shipment APIs
├── db/                          # SQL migrations + seed data
│   ├── migrations/
│   └── seed/
├── knowledge-base/              # Source SOP/SLA/policy documents
├── infra/                       # docker-compose.yml, otel config, grafana dashboards
└── README.md
```

------------------------------------------------------------------------

## 2. Phased Plan

### Phase 0 — Setup (Day 1)
**Owner:** All three (repo scaffold is a joint kickoff task; Person 2 — Aakash Bala — leads the Docker Compose skeleton since they own deployment).
- Initialize monorepo structure above.
- Set up Docker Compose skeleton with empty service stubs.
- Set up shared `.env.example`.
- **Acceptance:** `docker compose up` boots all placeholder services without error.

### Phase 1 — Requirements & Architecture Sign-off (Day 1–2)
**Owner:** All three — this is the non-negotiable Day 1 contract-freeze gate from `docs/team_plan.md` (schema, API contracts, and response schema must be agreed by everyone before coding starts).
- Review and confirm the 6 docs in `/docs` with the whole team.
- Confirm LLM provider choice (Qwen / Llama / GPT) and vector DB choice
  (Chroma vs pgvector).
- **Acceptance:** All teammates agree on schema, agent boundaries, and API contracts before coding starts.

### Phase 2 — Database Design & Seed Data (Day 3–4)
**Owner:** Person 2 (Aakash Bala) — matches P2.1–P2.3 in `docs/team_plan.md`. Output is a hard handoff to Person 3 (Text-to-SQL cannot begin without the frozen schema).
- Implement DDL from [Backend Schema](./06_backend_schema.md) as SQL
  migration scripts in `db/migrations/`.
- Generate synthetic seed data: customers, sales_orders, order_items,
  inventory, warehouse, shipment, invoice, payment, carrier_tracking,
  users, sla_rules (at least 30–50 orders spanning on-time, delayed,
  and SLA-breached scenarios).
- Write 5–10 SOP/SLA markdown/PDF documents for the knowledge base
  (delay handling, customs hold procedure, escalation matrix, etc.).
- **Acceptance:** `psql` against seeded DB returns realistic query
  results for all sample questions in Section 11 of the problem
  statement.

### Phase 3 — Mock External APIs (Day 4–5, parallel with Phase 2)
**Owner:** Person 2 (Aakash Bala) — matches P2.4 in `docs/team_plan.md`.
- Build `mock-apis` service exposing:
  - `GET /api/order/{orderNumber}`
  - `GET /api/shipment/status/{trackingNumber}`
  - `GET /api/inventory/{sku}`
- Responses should be deterministic per seed data (same order number
  always returns the same mock status) so agent behavior is testable.
- **Acceptance:** All 3 endpoints return realistic JSON matching
  Section 12 of the problem statement, including at least one delayed
  shipment scenario (customs hold, HS code mismatch).

### Phase 4 — Angular UI & Spring Boot API Skeleton (Day 5–6)
**Owner:** Person 1 (Muralikarthik) — matches P1.1–P1.4 in `docs/team_plan.md`.
- Spring Boot: user auth (JWT), session endpoints, `/api/chat`
  gateway endpoint (proxies to FastAPI), `/api/history`,
  `/api/audit` (admin-only).
- Angular: login screen, chat screen (static/mock responses first),
  history panel, suggested-questions panel.
- **Acceptance:** User can log in, send a chat message, and see a
  hardcoded/mocked response end-to-end through Spring Boot.

### Phase 5 — Knowledge Base RAG Setup (Day 7–8)
**Owner:** Person 3 (Karthik Saravanan) — matches P3.2–P3.4 in `docs/team_plan.md`.
- Build ingestion script: load documents → chunk → embed → upsert to
  vector DB.
- Implement `kb_search` MCP tool.
- Implement Knowledge Base Agent (LangGraph node) that calls
  `kb_search` and summarizes results with citations.
- **Acceptance:** Asking "What is the SLA breach escalation process?"
  returns a correct, cited answer sourced from ingested documents.

### Phase 6 — Text-to-SQL & PostgreSQL Integration (Day 9–10)
**Owner:** Person 3 (Karthik Saravanan) — matches P3.5–P3.6 in `docs/team_plan.md`, building on Person 2's frozen schema and seed data.
- Implement SQL validator (allow-list tables, block write/DDL
  keywords, enforce `LIMIT`).
- Implement `db_query` MCP tool using a read-only DB role.
- Implement Text-to-SQL Agent: prompt template with fixed schema
  context, few-shot examples, retry-on-validation-failure logic.
- **Acceptance:** "Show delayed orders from Chennai warehouse"
  produces the exact SQL pattern shown in Section 11 of the problem
  statement and returns correct rows.

### Phase 7 — API Status Agent (Day 11)
**Owner:** Person 3 (Karthik Saravanan) — agent logic; Person 2 (Aakash Bala) — underlying MCP API tools (matches P2.8 and part of P3.9 in `docs/team_plan.md`).
- Implement `get_order_status`, `get_shipment_status`,
  `get_inventory` MCP tools calling `mock-apis`.
- Implement API Status Agent with timeout/error handling.
- **Acceptance:** Querying a known order number returns live (mocked)
  shipment status merged correctly into agent state.

### Phase 8 — LangGraph Supervisor Workflow (Day 12)
**Owner:** Person 3 (Karthik Saravanan) — matches P3.8–P3.11 in `docs/team_plan.md`.
- Implement full state graph: intent classifier → conditional
  fan-out to KB/SQL/API agents → Business Rule Agent → Final Response
  Agent → error handler with retry.
- Implement Business Rule Agent: SLA breach calculation (promised vs.
  revised date), delay-day computation, recommended-action generation.
- (Stretch) Implement human-in-the-loop interrupt before escalation
  actions.
- **Acceptance:** The full "Order SO-45892" scenario from Section 6–7
  of the problem statement produces the exact structured output
  format shown (status, reason, impact, recommended action).

### Phase 9 — MCP Tool Integration & Testing (Day 13)
**Owner:** Person 2 (Aakash Bala) — platform integration (matches P2.10 in `docs/team_plan.md`); all three contribute to end-to-end and security testing.
- Wire FastAPI AI layer to LangGraph graph via MCP client.
- End-to-end integration testing across all 3 agent types plus
  combined multi-agent queries.
- Load/latency testing against the 15-second response target.
- Security testing: confirm Text-to-SQL cannot run destructive SQL.
- **Acceptance:** All test types in Technical Requirements Section 11
  pass.

### Phase 10 — Audit Logging & Observability (Day 13, parallel)
**Owner:** Person 1 (Muralikarthik) — audit persistence and Admin audit view UI; observability instrumentation is shared across all three layers.
- Implement `audit_log` writes at every tool call and final response
  from Spring Boot (or FastAPI writing back through Spring Boot).
- Implement Admin audit view in Angular (search/filter by user, date,
  order number).
- Add OpenTelemetry spans across all layers; stand up Grafana
  dashboard (optional but recommended).
- **Acceptance:** Every query in the demo script produces a
  retrievable, complete audit trail.

### Phase 11 — Documentation, PPT & Demo Prep (Day 14)
**Owner:** All three, per the "Demo + documentation" row for every person in the Day-by-Day Breakdown of `docs/team_plan.md`.
- Finalize README with setup instructions.
- Prepare project report, PPT, and demo video script based on the
  main use case.
- Dry-run the full demo end-to-end at least twice.
- **Acceptance:** Fresh clone + `docker compose up` + seed script
  reproduces the full demo without manual intervention.

------------------------------------------------------------------------

## 3. Team Task Ownership (suggested split)

| Track | Owner role | Phases |
|---|---|---|
| Frontend (Angular) | Frontend dev | 4, 10 (audit UI), 11 |
| Backend API (Spring Boot) | Backend dev | 4, 10 |
| AI/Agents (FastAPI + LangGraph) | AI/ML dev | 5, 6, 7, 8 |
| Data & Infra (DB, mock APIs, Docker, MCP) | Full-stack/infra dev | 2, 3, 9 |

Cross-cutting: everyone reviews Phase 1 docs; everyone contributes to
Phase 11 demo prep.

**Real names for the roles above** (see `docs/team_plan.md` for the
full day-by-day task timeline): Frontend dev / Backend dev = Person 1
(Muralikarthik); AI/ML dev = Person 3 (Karthik Saravanan); Full-stack/
infra dev = Person 2 (Aakash Bala).

------------------------------------------------------------------------

## 4. Definition of Done (per feature)

A feature/task is "done" only when:
1. Code is committed with a clear message referencing the phase/task.
2. Unit tests (where applicable per Technical Requirements Section 11)
   pass locally and in CI (if configured).
3. The feature is demonstrable via the Angular UI or a documented
   API/tool call.
4. Any new MCP tool, agent, or endpoint is reflected back into the
   relevant doc (Technical Requirements, App Flow, or Backend Schema)
   if it changes the original contract.

------------------------------------------------------------------------

## 5. Related Documents

- [Product Requirements](./01_product_requirements.md)
- [Technical Requirements](./02_technical_requirements.md)
- [UI/UX Design](./04_ui_ux_design.md)
- [App Flow](./05_app_flow.md)
- [Backend Schema](./06_backend_schema.md)

------------------------------------------------------------------------

## 6. Team Ownership (Detailed Work Plan)

This phased plan is a compressed, module-oriented view. The
authoritative, task-level execution plan — with per-person branch
problem statements, day-by-day deadlines, technology stacks, and
completion gates — lives in `docs/team_plan.md`. Use that document
when a teammate needs their next concrete task; use this document when
the whole team needs to see how the phases fit together.

| Team Member | Branch | Phases Owned Above |
|---|---|---|
| Muralikarthik (Person 1) | Application Engineer | Phase 4, Phase 10 (audit UI/persistence), Phase 11 |
| Aakash Bala (Person 2) | AI Platform & Tooling Engineer | Phase 0, Phase 2, Phase 3, Phase 9, Phase 11 |
| Karthik Saravanan (Person 3) | AI Intelligence & Orchestration Engineer | Phase 5, Phase 6, Phase 7 (agent logic), Phase 8, Phase 11 |

### Non-Negotiable Milestones (from `docs/team_plan.md`)

- **End of Day 1:** Architecture, database schema, API contracts, and
  response schema are frozen (Phase 1 above).
- **End of Day 6:** Angular → Spring Boot → FastAPI works; database,
  APIs, RAG, and Text-to-SQL work independently (Phases 2–5 above).
- **End of Day 9:** MCP tools and LangGraph routing work; the flagship
  question can gather multi-source evidence (Phases 6–7 above).
- **End of Day 11:** Complete end-to-end flow works; feature freeze
  begins (Phase 8 above).
- **Days 12–13:** Only integration, testing, evaluation, and bug
  fixing (Phase 9–10 above).
- **Day 14:** Demo, report, presentation, and final packaging
  (Phase 11 above).

**Feature freeze rule:** after Day 11, no new features are allowed
unless they fix a critical gap in the flagship demo (order SO-45892
scenario). Days 12–14 are for reliability, evaluation, documentation,
and presentation only.