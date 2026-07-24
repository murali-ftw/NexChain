# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Four personas share the chat interface with comparable priority (confirmed — no single persona is designed for at the others' expense):

- **Supply Chain Manager** — needs fast answers on order/shipment status and delay reasons, wants recommended next actions rather than raw data, cares about SLA breaches and customer impact.
- **Customer Service Representative** — needs to answer "where is my order" calls/emails in plain language, not SQL or JSON.
- **Operations / Warehouse Analyst** — needs inventory availability and warehouse-level reporting; asks more data-heavy, tabular questions (e.g. "list all delayed orders from Chennai warehouse").
- **Admin / IT Auditor** — reviews audit logs of every query, tool call, and generated SQL for compliance and debugging; the only persona with an admin-only surface (`/api/audit`, role `ADMIN`).

## Product Purpose

NexChain is a conversational Supply Chain Intelligence Co-Pilot. Supply chain data is fragmented across ERP, WMS, TMS, shipment tracking portals, and document repositories, forcing business users to manually check multiple systems for order status, shipment status, inventory, invoices, and SLA compliance. NexChain answers natural-language business questions by combining a knowledge base (RAG over SOP/SLA/policy documents), text-to-SQL over Postgres, and REST calls to enterprise-style APIs, then applies deterministic SLA/business rules and returns one structured, auditable answer with a recommended action list — not just raw data.

Success (per docs/01_product_requirements.md §5): sub-15-second responses, every documented query type self-served through chat instead of an IT/ops request, every delayed order automatically flagged with SLA breach status, every delay-style answer carrying a recommended action list, and 100% of queries/tool calls/generated SQL traceable in the audit log.

## Positioning

A neighboring "chatbot over our database" could not truthfully copy NexChain's mechanism: it doesn't just retrieve or just query — a LangGraph supervisor classifies intent and routes to whichever of Knowledge Base / Text-to-SQL / API Status agents apply (including multiple at once, as in the flagship SO-45892 scenario), a deterministic Business Rule Agent then checks SLA breaches and produces recommended actions, and every tool call, generated SQL statement, and agent decision is logged for audit. The answer is always structured and source-cited, never a free-text guess.

## Operating Context

- Primary interaction is a chat UI: the user asks a free-text question, authenticated via JWT, and receives a structured answer covering order status, shipment status, delay reason, SLA impact, and recommended actions.
- Real end-to-end flow (confirmed live, not aspirational): Angular → Spring Boot (auth, session, audit) → FastAPI AI layer → LangGraph supervisor → Knowledge Base / Text-to-SQL / API Status agents → MCP tools → PostgreSQL / mock ERP-WMS-TMS APIs → Business Rule Agent → Final Response Agent.
- Query history and a suggested-questions panel help users get started and revisit past answers.
- Admins have a separate audit view to search and inspect log entries (user id, timestamp, raw question, detected intent, agents invoked, tool calls including generated SQL/API calls, final response).
- Entire stack runs locally via Docker Compose for demo purposes (academic final-year project, not a production deployment).

## Capabilities and Constraints

- Natural-language query input, intent classification and routing (order status, shipment delay, inventory check, SOP/SLA lookup, general reporting).
- Knowledge Base retrieval (RAG) cites source document/section for every answer that uses it.
- Text-to-SQL is read-only and validated before execution (SELECT-only, table allowlist, row limit, no INSERT/UPDATE/DELETE/DROP) — this is a hard security constraint, not a UI concern to soften.
- API Status Agent calls simulated ERP/WMS/TMS/shipment-tracking REST APIs (real third-party integration is explicitly out of scope for this project).
- Business Rule Agent evaluates SLA breaches (promised vs. revised delivery date, delay thresholds) and always attaches a recommended-action list to delay/breach answers.
- LangGraph retries a failed tool call once before failing gracefully; a degraded/partial answer (`partial: true`) with a warning is always preferred over a raw error surfaced to the user.
- Two roles: standard user and admin/auditor. Login required before any query.
- English only, single-tenant, for this MVP.
- Chat UI must clearly separate answer, data source (DB/API/KB), and recommended action (explicit usability requirement, docs/01_product_requirements.md §8) — a durable structural constraint for any chat surface design, not a styling preference.
- No formal accessibility standard is required (confirmed); follow ordinary accessible-by-default practice.

## Brand Commitments

Product name is **NexChain** (confirmed). No logo, wordmark, or visual identity exists yet — the current frontend has no branding applied (`frontend/src/index.html` still reads `<title>Frontend</title>`, no asset folder). Any visual identity work is a from-scratch decision, not a refinement of an existing mark.

## Evidence on Hand

- Real, working demo output exists and must not be treated as fabricated example copy: `docs/07_demo_results.md` records actual `curl` responses from the live stack (Docker Compose, seeded Postgres, real Gemini key) against `POST /api/chat`, including the flagship scenario (order `SO-45892`, customs hold, SLA breach, cited SOP sources, full agent trace).
- Seeded demo accounts exist: `user@example.com` / `password` (role USER), `admin@example.com` / `password` (role ADMIN).
- Named scenario orders are real, hardcoded, and cross-referenced across layers: `SO-45892` (flagship), `SO-10241`/`SO-10288`/`SO-10299`/`SO-10310` (reporting set), `SO-3000x` (category scenarios) — see `db/seed_data.sql`, `ChatService.java`, `chat-fixtures.ts`.
- No customer testimonials, press, case studies, or third-party logos exist or should be invented — this is an academic prototype with simulated (mock) external systems, not a company with real customers.

## Product Principles

1. **Structured and sourced over free-text.** Every answer separates status, cause, impact, and recommended action, and cites the DB/API/KB source it came from — never an unstructured LLM narrative standing alone.
2. **Never fail loud to the end user.** Tool and network failures degrade to a clear partial/warning state; a raw 5xx or stack trace reaching Angular is treated as a defect, not an acceptable edge case.
3. **Read-only and auditable by construction.** SQL execution is SELECT-only and allowlisted, and every query, tool call, and generated SQL statement is logged — these are product guarantees the UI should make visible (e.g. the audit view), not just backend implementation detail.
4. **Serve four different jobs from one interface.** The same chat surface must work for a manager who wants a quick verdict, a CS rep who wants plain language, an analyst who wants tabular data, and an auditor who wants a full trace — no persona is the "real" one the others are cut down from.
5. **Prototype honesty.** APIs are simulated, data is synthetic, and the project is a 14-day academic deliverable — design and copy should not imply real third-party integrations, real customers, or production-scale guarantees that don't exist.

## Accessibility & Inclusion

No specific standard (e.g. WCAG) is required (confirmed). Follow ordinary accessible-by-default practice.
