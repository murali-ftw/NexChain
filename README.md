# NexChain — Supply Chain Intelligence Co-Pilot

[![CI](https://github.com/murali-ftw/NexChain/actions/workflows/ci.yml/badge.svg)](https://github.com/murali-ftw/NexChain/actions/workflows/ci.yml)

A conversational assistant for supply-chain operations: ask about an order,
a shipment, an SLA breach, or a policy in plain English, and get back a
**structured, deterministic answer** — not free-text prose you have to parse.
A multi-agent [LangGraph](https://github.com/langchain-ai/langgraph)
pipeline decides whether the question needs a database lookup, a live API
call, a knowledge-base search, or all three, then a business-rule engine
turns the raw data into an SLA verdict and a recommended action.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start (Docker Compose)](#quick-start-docker-compose)
  - [Local Development](#local-development)
- [Configuration](#configuration)
- [Testing &amp; Quality Gates](#testing--quality-gates)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)

---

## Features

- **Natural-language query understanding** — an intent classifier routes each
  question to exactly the agents it needs (database, API, knowledge base, or
  a combination), instead of every query paying the cost of every agent.
- **Text-to-SQL over a real schema** — LLM-generated SQL is validated against
  a table allow-list, a denied-keyword list, and a row cap before it ever
  reaches the database (defense in depth, enforced twice: once in the
  boundary layer, once again at the MCP tool).
- **Retrieval-augmented policy answers (RAG)** — grounded in a real knowledge
  base of SOPs and policies (`ai/knowledge_base/`), with citations, not
  hallucinated procedure.
- **Deterministic business rules** — SLA breach status, severity, escalation
  role, and recommended actions are computed by a pure rule engine
  (`ai/agents/business_rule_agent/rules.py`), not left to an LLM to
  improvise — the same inputs always produce the same verdict.
- **Structured response contract end-to-end** — the wire shape
  (`CoPilotResponse`) is frozen and typed from FastAPI through Spring Boot to
  Angular; the UI renders real fields (order status, SLA status, recommended
  actions, sources), not a markdown blob.
- **Graceful degradation, not failure** — if the LLM key, the database, or an
  upstream API is unavailable, the pipeline still returns every fact it *can*
  determine, with `partial: true` and a clear `error` explaining what's
  missing, rather than a 500.
- **Real MCP tool connectivity** — the agents don't import a database driver
  or an HTTP client directly; they call an independent MCP tool server
  (`mcp_server/`) over a real `ClientSession`, matching the
  [Model Context Protocol](https://modelcontextprotocol.io/) rather than a
  simulated version of it.
- **Full audit trail** — every chat turn is persisted with its detected
  intent, agents invoked, generated SQL, and sources, browsable in an
  admin-only audit log.

## Architecture

```
 Angular (4200)
      │  HTTP + JWT
      ▼
 Spring Boot backend-api (8080)  ── auth, per-user history, admin audit log
      │  POST /ai/query
      ▼
 FastAPI ai_service (8001)  ── thin HTTP wrapper
      │
      ▼
 LangGraph pipeline (ai/graph/)
      │
      ├─▶ intent_classifier ──┬─▶ knowledge_base_agent   (RAG)
      │                       ├─▶ text_to_sql_agent       (DB)
      │                       └─▶ api_status_agent        (external API)
      │                              │
      │                              ▼
      │                     business_rule_agent  ── SLA breach / escalation
      │                              │
      │                              ▼
      │                     final_response_agent  ── assembles CoPilotResponse
      ▼
 ai/mcp_client.py  (real MCP ClientSession, streamable-http)
      │
      ▼
 mcp_server (8002)  ── db_query, get_order, get_order_status,
      │                 get_shipment_status, get_inventory
      ├──────────────┬──────────────┐
      ▼              ▼              ▼
 PostgreSQL      mock_apis      (KB search stays direct —
   (5432)         (8000)         see Known Limitations)
```

The response then flows back up the same chain: LangGraph → FastAPI →
Spring Boot (mapped to the app-layer `ChatResponse` and persisted to
history + audit) → Angular (rendered as structured cards, not raw text).

## Repository Structure

```
NexChain/
├── frontend/           Angular 21 SPA — chat, history, audit views
├── backend-api/        Spring Boot 3.5 — auth, history, audit, AI proxy
├── ai_service/         FastAPI — HTTP wrapper around the LangGraph pipeline
├── ai/                 The LangGraph multi-agent pipeline
│   ├── agents/           intent_classifier, text_to_sql_agent,
│   │                     knowledge_base_agent, business_rule_agent
│   ├── graph/            LangGraph wiring, routing, boundary modules, evals
│   ├── knowledge_base/   SOP/policy documents (source for RAG)
│   ├── rag/              Vector store + ingestion
│   ├── mcp_client.py     Real MCP client used by the boundary modules
│   └── contracts.py      Frozen CoPilotResponse / state contracts
├── mcp_server/         MCP tool server (db_query, get_order, ...)
├── mock_apis/          Simulated ERP / shipment-tracking / inventory APIs
├── db/                 Schema + role migrations, demo seed data
├── infra/              docker-compose.yml, environment template
├── scripts/            Dev tooling (e.g. load_test.py)
├── docs/               Requirements, schema, and API contract documents
└── .github/workflows/  CI (build, test, lint, dependency scan)
```

## Tech Stack

| Layer                | Technology                                                                          |
| -------------------- | ----------------------------------------------------------------------------------- |
| Frontend             | Angular 21, TypeScript, RxJS, Karma + Jasmine                                       |
| App backend          | Spring Boot 3.5 (Web, Security, Validation, Data JPA), Java 25, JJWT, H2 (embedded) |
| AI service           | FastAPI, Pydantic                                                                   |
| Agent orchestration  | LangGraph, LangChain                                                                |
| RAG / knowledge base | ChromaDB (embedded), sentence-transformers                                          |
| Text-to-SQL safety   | sqlglot (parse + validate before execution)                                         |
| Tool connectivity    | Model Context Protocol (`mcp` SDK), streamable-http                               |
| Database             | PostgreSQL 15, SQLAlchemy / psycopg3                                                |
| Testing              | pytest, JUnit 5 + MockMvc, Karma/Jasmine,`pip-audit` / `npm audit`              |
| Lint & types         | ruff, mypy, TypeScript strict mode                                                  |
| Infra                | Docker, Docker Compose, GitHub Actions                                              |

## Getting Started

### Prerequisites

- **Docker + Docker Compose** — the supported way to run the full stack.
- **For native/local development instead of Docker:** Python 3.12+, Node 20+,
  a JDK 25+ (JDK 26 verified working), PostgreSQL 15.

### Quick Start (Docker Compose)

```bash
cp infra/.env.example infra/.env
# edit infra/.env: set POSTGRES_PASSWORD, COPILOT_READONLY_PASSWORD, COPILOT_APP_PASSWORD
# LLM_PRIMARY_API_KEY is optional — see "Graceful degradation" above

cd infra
docker compose up -d --build
```

Seed the database once, on first run:

```bash
docker exec -i nexchain-postgres psql -U postgres -d nexchain -v ON_ERROR_STOP=1 < ../db/seed_data.sql
```

| Service     | Port     |
| ----------- | -------- |
| frontend    | `4200` |
| backend-api | `8080` |
| ai_service  | `8001` |
| mcp_server  | `8002` |
| mock_apis   | `8000` |
| postgres    | `5432` |

Open [http://localhost:4200](http://localhost:4200) and log in with the
seeded demo account (`user@example.com` / `password`, or `admin@example.com`
/ `password` for audit-log access). These three passwords are public in this
repository (`InMemoryUserStore`) — override them via `DEMO_USER_PASSWORD` /
`DEMO_SECOND_USER_PASSWORD` / `DEMO_ADMIN_PASSWORD` before exposing this
service outside local development; see "Known Limitations".

### Local Development

Each stack can also run natively, outside Docker, provided the others it
depends on are reachable (see the [Configuration](#configuration) table).

<details>
<summary><strong>Python (ai / ai_service / mcp_server / mock_apis)</strong></summary>

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# with Postgres + mock_apis + mcp_server reachable:
python -m pytest ai/ ai_service/ mcp_server/ mock_apis/
ruff check . && mypy .
```

</details>

<details>
<summary><strong>Frontend</strong></summary>

```bash
cd frontend
npm ci
npm run build
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  npx ng test --watch=false --browsers=ChromeHeadless   # macOS; point CHROME_BIN at your browser
```

CI also runs `FirefoxHeadless` (`karma-firefox-launcher` +
`browser-actions/setup-firefox`) — add it to `--browsers` locally if you have
Firefox installed.

</details>

<details>
<summary><strong>Backend</strong></summary>

`pom.xml` pins `<java.version>25</java.version>`, but any JDK ≥ 25 builds it
fine (verified with JDK 26 — Maven only needs a JDK at least as new as the
target release):

```bash
cd backend-api
./mvnw test          # or: ./mvnw clean verify   (what CI runs)
```

No local JDK? Build/test in Docker instead:

```bash
docker run --rm -v "$PWD":/app -w /app -v maven-repo-cache:/root/.m2 \
  maven:3.9-eclipse-temurin-25 mvn -B test
```

</details>

## Configuration

All variables are read from `infra/.env` in Docker Compose, or the shell
environment for native/local runs.

| Variable                                        | Used by                                              | Default                                                                 |
| ----------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------- |
| `POSTGRES_PASSWORD`                           | postgres                                             | required, no default                                                    |
| `COPILOT_READONLY_PASSWORD`                   | db role migrations, ai_service, mcp_server           | required, no default                                                    |
| `COPILOT_APP_PASSWORD`                        | db role migrations, backend-api                      | required, no default                                                    |
| `AI_SERVICE_DATABASE_URL`                     | ai_service, mcp_server (text-to-SQL,`get_order`)   | none — must be set                                                     |
| `MOCK_API_DATABASE_URL`                       | mock_apis                                            | none — must be set                                                     |
| `MOCK_API_BASE_URL`                           | ai_service, mcp_server (calling mock_apis)           | `http://localhost:8000`                                               |
| `MCP_SERVER_URL`                              | `ai/mcp_client.py` (ai_service calling mcp_server) | `http://localhost:8002/mcp`                                           |
| `LLM_PRIMARY_API_KEY`                         | ai_service (`ai/llm_client.py`)                    | none — degrades gracefully if unset                                    |
| `LLM_PRIMARY_PROVIDER`, `LLM_PRIMARY_MODEL` | ai_service (`ai/llm_client.py`)                    | see`ai/llm_client.py`                                                 |
| `JWT_SECRET`                                  | backend-api                                          | dev-only fallback —**must** be overridden in any real deployment |
| `AI_SERVICE_BASE_URL`                         | backend-api calling ai_service                       | `http://localhost:8001`                                               |

## Testing & Quality Gates

Three independent CI jobs (`.github/workflows/ci.yml`) mirror what's
described below: **Spring Boot** (`mvn clean verify`), **Angular** (build +
Chrome/Firefox headless unit tests), and **Python** (ruff + mypy + pytest +
the completion-gate evals, against a live Postgres/mock_apis/mcp_server).
Dependency advisories are scanned inline (`pip-audit`, `npm audit`) and
tracked continuously by `.github/dependabot.yml` across all three
ecosystems.

### AI pipeline evaluation gates

Beyond unit tests, each agent has a completion-gate eval script that proves
it meets its accuracy bar against live infrastructure — these are what
actually validate intent accuracy, SQL correctness, RAG grounding, and rule
determinism, not just that the code runs:

```bash
python -m ai.agents.intent_classifier.eval      # routing accuracy
python -m ai.agents.text_to_sql_agent.eval      # generated-SQL correctness
python -m ai.agents.knowledge_base_agent.eval   # RAG grounding + citations
python -m ai.agents.business_rule_agent.eval    # SLA rule engine, exact-match
python -m ai.graph.eval                         # end-to-end routing/path
python -m ai.graph.eval_final_response          # structured CoPilotResponse, live
```

### Load / concurrency testing

`scripts/load_test.py` (stdlib-only, no extra dependencies) fires concurrent
`POST /api/chat` requests against a live stack and reports latency
percentiles and error rate — the one dimension none of the correctness
suites above measure.

```bash
python scripts/load_test.py --base-url http://localhost:8080 --concurrency 10 --requests 30
```

Baseline (concurrency 10, 30 requests, local Docker Compose, real LLM key):
**30/30 succeeded, zero errors under concurrent load** — p50 13.7s, p95
19.4s. Consistent with the ~14s single-request flagship latency: no
throughput cliff at this concurrency, but also no speedup, since each
`/api/chat` call is a sequential chain of several LLM/tool calls with no
request-level caching or parallelization across independent sub-agents.

## Security

- **Authentication** — stateless JWT (HS256), issued by `backend-api`,
  attached by an Angular HTTP interceptor, validated on every request.
- **Authorization** — the audit log is admin-only, enforced at two layers:
  server-side (`SecurityConfig`'s `hasRole("ADMIN")` on `/api/audit/**`) and
  client-side (`adminGuard` on the `/audit` route, redirects non-admins).
- **CORS** — an explicit allow-list (`app.cors.allowed-origins`), not a
  wildcard; verified live to reject unlisted origins with `403`.
- **SQL safety** — every generated query is parsed and validated
  (SELECT-only, table allow-list, denied-keyword list, row cap) before
  execution, enforced independently at both the boundary layer and the MCP
  tool — verified with a live SQL-injection probe that left the database
  untouched.
- **Prompt-injection resistance** — the knowledge-base agent only answers
  from retrieved policy documents; a live "ignore previous instructions"
  probe returned a grounded refusal, not a leaked prompt.
- **No stack-trace leakage** — a global exception handler
  (`GlobalExceptionHandler`) returns a generic message on any unhandled
  error; full detail is logged server-side only.
- **Dependency scanning** — `pip-audit` and `npm audit` run in CI on every
  push; Dependabot tracks Maven, npm, pip, and GitHub Actions weekly. Two
  advisories are currently accepted with no fix available upstream — see
  [Known Limitations](#known-limitations) for the verification behind each.

## Troubleshooting

| Symptom                                                                                          | Cause / Fix                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Unable to locate a Java Runtime` running `./mvnw`                                           | No local JDK. Install one (JDK 26 verified) — Maven only needs a JDK ≥ the pinned`25`, not an exact match — or build/test in Docker (see [Local Development](#local-development)).                                                                                                                                                                                                                                                                                                             |
| `password authentication failed for user "copilot_readonly"`                                   | The Postgres data volume was created by an earlier`docker compose up` with different role passwords than your current `infra/.env` (init scripts only run once, against an empty volume). Fix without losing data: `docker exec nexchain-postgres psql -U postgres -d nexchain -c "ALTER ROLE copilot_readonly WITH PASSWORD '<value>'; ALTER ROLE copilot_app WITH PASSWORD '<value>';"` matching `infra/.env`. To start clean instead: `docker compose down -v` (destroys the volume). |
| `mock_apis`/`mcp_server` pytest suites fail with `Cannot reach the database`               | `MOCK_API_DATABASE_URL` isn't set in your shell — these tests mount `mock_apis` in-process, and it needs its own DB connection string even though `mcp_server` also has `AI_SERVICE_DATABASE_URL` set.                                                                                                                                                                                                                                                                                    |
| `ai/graph/eval_final_response.py`'s flagship case fails with a DB/MCP connection error         | Postgres,`mock_apis`, and `mcp_server` all need to be reachable (see [Configuration](#configuration)). The fallback cases in that same script pass regardless — they simulate the failure deliberately.                                                                                                                                                                                                                                                                                        |
| A chat response comes back with`partial: true` and `error: "LLM_PRIMARY_API_KEY is not set"` | Expected without an LLM key — every database/API-sourced field is still correct; only LLM-dependent prose and citations are degraded. See[Features](#features).                                                                                                                                                                                                                                                                                                                                    |
| Frontend production bundle points at`http://localhost:8080`                                    | Correct for the Docker Compose deployment target — the*browser* resolves this URL, not the frontend container. A real multi-host production deployment would need a build-time-configurable `apiBaseUrl`, which the current Angular `environment.ts` setup doesn't support.                                                                                                                                                                                                                 |

## Known Limitations

- **`InMemoryUserStore` is a demo user directory, not real user management** —
  three accounts (`user@example.com`, `second-user@example.com`,
  `admin@example.com`, all seeded with public default passwords) are the
  entire user directory; there is no registration, password-change, or
  persistent-user-record endpoint. Override the seed passwords via
  `DEMO_USER_PASSWORD` / `DEMO_SECOND_USER_PASSWORD` / `DEMO_ADMIN_PASSWORD`
  before exposing this service outside local development — the defaults are
  public in this repository.
- **backend-api's conversation history / audit log (H2) needs its Docker
  volume kept** — `infra/docker-compose.yml`'s `backend_data` volume is what
  makes `/app/data/nexchain-history.*` survive a container recreate; running
  `docker compose down -v` (or any deployment that doesn't preserve named
  volumes) discards all chat history and the admin audit trail. This is a
  separate, backend-api-owned H2 file — not Person 2's shared Postgres
  `nexchain` database, which `db/migrations`/`pg_dump` back up independently.
- **`kb_search` is not exposed as an MCP tool** — `knowledge_base_agent`
  calls the RAG vector store directly instead. Deliberate; see the trailing
  note in `mcp_server/server.py`.
- **No CI-wired dependency scan for Maven** — OWASP's `dependency-check`
  plugin needs an NVD API key and a slow first-run database download, too
  brittle for per-push CI without one. Covered instead by
  `.github/dependabot.yml`, which watches all three ecosystems (plus GitHub
  Actions itself) via GitHub's advisory database.
- **Cross-browser coverage** — CI runs Chrome + Firefox headless; no Safari
  coverage anywhere (CI runs on `ubuntu-latest`, and Safari is macOS/iOS-only,
  which would need a `macos-latest` runner).

### Dependency advisories with no fix available

All confirmed non-exploitable in this codebase; re-checked automatically by
`pip-audit`/`npm audit` in CI, so a future fix version will surface on the
next push. (RC stabilization: `fast-uri`'s `GHSA-v2hh-gcrm-f6hx`, previously
listed here as high-severity, was resolved via a plain `npm audit fix` —
patch-level bump of a transitive devDependency, no breaking change.)

- **`npm audit` (frontend), 7 moderate, all devDependency-only build/CLI
  tooling** — verified none of the packages below appear anywhere in
  `dist/frontend/browser/*.js`; none are reachable by a user of the shipped app:
  - `uuid`'s [`GHSA-w5hq-g745-h8pq`](https://github.com/advisories/GHSA-w5hq-g745-h8pq)
    (missing buffer bounds check), transitive via
    `@angular-devkit/build-angular` → `webpack-dev-server` → `sockjs` → `uuid`
    — only reachable through `ng serve`'s local dev server. No fix available yet.
  - `@hono/node-server`'s [`GHSA-frvp-7c67-39w9`](https://github.com/advisories/GHSA-frvp-7c67-39w9)
    (path traversal in `serve-static`, Windows-only), transitive via
    `@angular/cli` → `@modelcontextprotocol/sdk` → `@hono/node-server` — the
    Angular CLI's own MCP tooling dependency, never invoked by this repo's
    build/test/serve scripts. Fix requires `npm audit fix --force`
    (`@angular/cli@21.0.4`, a downgrade) — deferred pending a compatible patch.
- **`pip-audit` (Python)** — `chromadb` 1.5.9 (the latest available release)
  has `CVE-2026-45829`, a pre-auth code-injection in ChromaDB's own HTTP
  server, reachable only via `trust_remote_code=true` on its collections
  endpoint. Verified: `ai/rag/vector_store.py` uses `chromadb.PersistentClient`
  only (embedded, in-process — ChromaDB's HTTP server is never started), and
  `trust_remote_code` does not appear anywhere in this codebase. No fix
  version exists yet.

---

For the frozen wire contracts, see [`ai/CONTRACTS.md`](ai/CONTRACTS.md) (AI
layer) and [`docs/api_contracts.md`](docs/api_contracts.md) (Angular ↔
Spring Boot). For product/requirements background, see
[`docs/`](docs/).
