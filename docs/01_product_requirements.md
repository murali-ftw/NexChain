# Product Requirements Document (PRD)

## Project: Supply Chain Intelligence Co-Pilot

---

## 1. Purpose

Define what the product must do from a business and user perspective.
This document is the source of truth for scope, user stories, and
acceptance criteria. All other documents (technical requirements,
implementation, UI/UX, app flow, backend schema) derive their scope
from this file.

---

## 2. Vision

Give supply chain managers, customer service reps, and operations
staff a single conversational interface to ask natural-language
questions about orders, shipments, inventory, invoices, and SLAs —
instead of manually checking ERP, WMS, TMS, courier portals, Excel
files, and SOP documents.

---

## 3. Target Users / Personas

### Persona 1 — Supply Chain Manager (Primary)

- Needs fast answers on order/shipment status and delay reasons.
- Wants recommended next actions, not just raw data.
- Cares about SLA breaches and customer impact.

### Persona 2 — Customer Service Representative

- Needs to answer customer calls/emails about "where is my order."
- Needs simple language answers, not SQL or JSON.

### Persona 3 — Operations / Warehouse Analyst

- Needs inventory availability and warehouse-level reporting.
- May ask more data-heavy, tabular questions (e.g., "list all delayed
  orders from Chennai warehouse").

### Persona 4 — Admin / IT Auditor

- Needs to review audit logs of every query, tool call, and generated
  SQL for compliance and debugging.

---

## 4. Problem Statement (Summary)

Supply chain data is fragmented across ERP, WMS, TMS, shipment
tracking portals, and document repositories. Business users cannot get
a single, trustworthy, conversational answer to operational questions,
causing delay, manual dependency on IT/ops teams, and poor customer
responsiveness. See `docs/problem_statement.md` for full background.

---

## 5. Goals and Success Metrics

| Goal                                         | Metric                                                             |
| -------------------------------------------- | ------------------------------------------------------------------ |
| Reduce time to answer order/shipment queries | < 15 seconds per query response                                    |
| Reduce manual SQL/report requests to IT/ops  | 100% of documented query types self-served via chat                |
| Improve delay/SLA visibility                 | Every delayed order automatically flagged with SLA breach status   |
| Provide actionable guidance, not just data   | Every "delay" style answer includes a recommended action list      |
| Full traceability                            | 100% of queries, tool calls, and generated SQL logged to audit_log |

---

## 6. Scope

### 6.1 In Scope (MVP / Final-Year Project Deliverable)

- Conversational chat UI (Angular) for natural language supply chain questions.
- Authentication (JWT/OAuth2) and session management.
- Intent classification and agent routing via LangGraph Supervisor.
- Knowledge Base Agent (RAG over SOP/SLA/policy documents).
- Text-to-SQL Agent over PostgreSQL (orders, inventory, invoices, shipments).
- API Status Agent calling simulated ERP/WMS/TMS/shipment tracking REST APIs.
- Business Rule Agent for SLA breach detection and escalation logic.
- Final Response Agent that composes a structured natural-language answer.
- MCP server exposing DB, vector DB, KB, and API tools to agents.
- Audit logging of every user query, agent decision, tool call, and generated SQL.
- Query history and suggested-questions panel in the UI.
- Docker-based local deployment of all services.

### 6.2 Out of Scope (Future Enhancements)

- Real SAP / Microsoft Dynamics 365 integration (simulated APIs only for MVP).
- WhatsApp / voice-based assistant channels.
- Predictive delay analytics and demand forecasting models.
- Automated customer notification (email/SMS) delivery.
- Multi-language support.
- Full control-tower dashboard with live BI charts.

---

## 7. Functional Requirements

### FR-1: Natural Language Query Input

The system shall accept free-text business questions from an
authenticated user via a chat interface.

### FR-2: Intent Detection and Routing

The system shall classify each query's intent (e.g., order status,
shipment delay, inventory check, SOP/SLA lookup, general reporting) and
route it to one or more of: Knowledge Base Agent, Text-to-SQL Agent,
API Status Agent.

### FR-3: Knowledge Base Retrieval (RAG)

The system shall retrieve relevant SOP, SLA, and policy document
excerpts from a vector database and cite the source document/section
in the response.

### FR-4: Text-to-SQL Generation and Execution

The system shall convert a business question into a validated,
read-only SQL query, execute it against PostgreSQL, and return
structured results. Unsafe or invalid SQL shall be rejected before
execution.

### FR-5: External API Status Lookup

The system shall call REST APIs (ERP order status, inventory, shipment
tracking) and parse JSON responses into a normalized internal format.

### FR-6: Business Rule Evaluation

The system shall evaluate SLA rules (promised vs. revised delivery
date, delay thresholds) and flag SLA breaches, computing delay in days.

### FR-7: Recommended Action Generation

For any delay or SLA breach scenario, the system shall produce an
ordered list of recommended corrective actions (e.g., escalation,
document correction, customer notification).

### FR-8: Final Response Composition

The system shall merge outputs from all invoked agents into a single,
structured, human-readable answer (status, reason, impact, recommended
action), matching the format shown in `docs/problem_statement.md`
Section 7.

### FR-9: Query History

The system shall persist and display a user's past queries and
responses within their session/account.

### FR-10: Suggested Questions

The system shall present example/suggested supply chain questions to
help users get started.

### FR-11: Audit Logging

The system shall record, for every query: user id, timestamp, raw
question, detected intent, agents invoked, tool calls made (including
generated SQL and API calls), and final response.

### FR-12: Audit View

The system shall provide an admin-facing view to search and inspect
audit log entries.

### FR-13: Authentication and Authorization

The system shall require login (JWT/OAuth2) before allowing any query,
and shall support at least two roles: standard user and admin
(auditor).

### FR-14: Human-in-the-Loop (Optional/Stretch)

The system shall support pausing a workflow to request human
confirmation before executing a high-impact action (e.g., before
escalation or notification steps), if enabled.

---

## 8. Non-Functional Requirements

| Category      | Requirement                                                                                                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Performance   | 95% of chat responses returned within 15 seconds under normal load                                                                                                               |
| Reliability   | LangGraph workflow must retry a failed tool call at least once before failing gracefully                                                                                         |
| Security      | All API traffic over HTTPS in deployed environments; SQL execution restricted to read-only role; no destructive SQL (INSERT/UPDATE/DELETE/DROP) permitted from Text-to-SQL Agent |
| Auditability  | Every tool call and generated SQL statement must be logged with timestamp and user id, non-editable by end users                                                                 |
| Scalability   | Architecture must support adding new MCP tools/agents without changing the Supervisor's core routing logic                                                                       |
| Usability     | Chat UI must clearly separate: answer, data source (DB/API/KB), and recommended action                                                                                           |
| Portability   | Entire stack must run locally via Docker Compose for demo purposes                                                                                                               |
| Observability | Key agent decisions and latencies must be traceable via OpenTelemetry/Grafana                                                                                                    |

---

## 9. User Stories

1. **As a** supply chain manager, **I want to** ask "Where is order
   SO-45892 and why is it delayed?" **so that** I can respond to a
   customer without checking three different systems.
2. **As a** customer service rep, **I want to** get a plain-language
   delay explanation and revised ETA **so that** I can inform the
   customer accurately.
3. **As an** operations analyst, **I want to** ask "Show delayed orders
   from Chennai warehouse" **so that** I get a tabular list without
   writing SQL myself.
4. **As a** supply chain manager, **I want** the system to tell me the
   SLA policy that applies **so that** I know if this delay counts as
   a breach.
5. **As an** admin, **I want to** view the audit log of a specific
   query **so that** I can verify what data/SQL/API calls produced a
   given answer.
6. **As a** user, **I want to** see my past queries **so that** I can
   revisit earlier answers without re-asking.
7. **As a** new user, **I want to** see suggested example questions
   **so that** I understand what the assistant can do.

---

## 10. Assumptions and Constraints

- ERP/WMS/TMS/shipment APIs will be **simulated** (mock REST services)
  for this project, not connected to real third-party systems.
- LLM may be a locally hosted or API-based model (Qwen / Llama / GPT);
  exact model choice is a technical decision, not a product constraint.
- Dummy/synthetic data will be used for customers, orders, inventory,
  shipments, and SOP documents.
- Single-tenant deployment (no multi-company/multi-tenant requirement).
- English language only for MVP.

---

## 11. Glossary

| Term             | Meaning                                                                             |
| ---------------- | ----------------------------------------------------------------------------------- |
| RAG              | Retrieval-Augmented Generation — retrieving document context to ground LLM answers |
| MCP              | Model Context Protocol — standardized tool-connectivity layer for agents           |
| SLA              | Service Level Agreement — contractual delivery/response commitment                 |
| SOP              | Standard Operating Procedure document                                               |
| Text-to-SQL      | Converting a natural language question into an executable SQL query                 |
| ETA              | Estimated Time of Arrival                                                           |
| Supervisor Agent | The LangGraph node that classifies intent and routes to sub-agents                  |

---

## 12. Related Documents

- [Technical Requirements](./02_technical_requirements.md)
- [Implementation Plan](./03_implementation_plan.md)
- [UI/UX Design](./04_ui_ux_design.md)
- [App Flow](./05_app_flow.md)
- [Backend Schema](./06_backend_schema.md)
- [Original Problem Statement](./problem_statement.md)

---

## 13. Team Ownership

Per `docs/team_plan.md`, the 3-person team owns this product by
architectural layer, not by random task split. Every requirement in
this document is delivered by one primary owner (with the other two
as integration partners at the agreed handoff points).

| Team Member                  | Role                                     | Owns                                                                                                                                                                           |
| ---------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Muralikarthik (Person 1)     | Application Engineer                     | Chat UI, login, history, audit view, structured response rendering — i.e., how the user interacts with and sees the system (FR-1, FR-9, FR-10, FR-12, FR-13)                  |
| Aakash Bala (Person 2)       | AI Platform & Tooling Engineer           | PostgreSQL, mock ERP/WMS/Shipment APIs, FastAPI hosting, MCP tools and tool safety — i.e., how the AI safely accesses data and services (FR-4 execution, FR-5, part of FR-11) |
| Karthik Saravanan (Person 3) | AI Intelligence & Orchestration Engineer | Intent detection, RAG, Text-to-SQL generation, LangGraph orchestration, business rules, final answer composition (FR-2, FR-3, FR-4 generation, FR-6, FR-7, FR-8, FR-14)        |

### Functional Requirement → Owner Mapping

| Requirement                                | Primary Owner                                                              | Notes                                                                                                  |
| ------------------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| FR-1 Natural Language Query Input          | Person 1                                                                   | Chat UI capture; Person 2 hosts the receiving endpoint                                                 |
| FR-2 Intent Detection and Routing          | Person 3                                                                   | LangGraph Supervisor / intent classifier                                                               |
| FR-3 Knowledge Base Retrieval (RAG)        | Person 3                                                                   | Agent logic; Person 2 owns the underlying MCP`kb_search` tool and vector DB hosting                  |
| FR-4 Text-to-SQL Generation and Execution  | Person 3 (generation) / Person 2 (safe execution)                          | SQL generated by Person 3's agent, executed via Person 2's`db_query` MCP tool and DB safety controls |
| FR-5 External API Status Lookup            | Person 3 (agent) / Person 2 (mock APIs + MCP tool)                         |                                                                                                        |
| FR-6 Business Rule Evaluation              | Person 3                                                                   | Business Rule Agent                                                                                    |
| FR-7 Recommended Action Generation         | Person 3                                                                   | Business Rule Agent                                                                                    |
| FR-8 Final Response Composition            | Person 3                                                                   | Final Response Agent; schema consumed by Person 1's UI                                                 |
| FR-9 Query History                         | Person 1                                                                   | Spring Boot history API + UI                                                                           |
| FR-10 Suggested Questions                  | Person 1                                                                   | UI only                                                                                                |
| FR-11 Audit Logging                        | Person 1 (persistence + view) / Person 2 & 3 (data supplied per tool call) |                                                                                                        |
| FR-12 Audit View                           | Person 1                                                                   | UI + Spring Boot audit controller                                                                      |
| FR-13 Authentication and Authorization     | Person 1                                                                   | Spring Security / JWT                                                                                  |
| FR-14 Human-in-the-Loop (Optional/Stretch) | Person 3 (graph interrupt) / Person 1 (confirmation UI)                    |                                                                                                        |

**How to apply:** when a requirement in this document needs further
detail (technical design, task breakdown, UI spec, flow, or schema),
route the question to the primary owner listed above. See
`docs/team_plan.md` for the full day-by-day task timeline and
cross-team handoff gates.
