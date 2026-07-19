# NexChain AI Layer — Frozen Shared Contracts (P3.1)

Human-readable mirror of [`ai/contracts.py`](./contracts.py) for Person 1 and
Person 2 to review and sign off on. This file must stay in sync with
`contracts.py` — where they disagree, `contracts.py` (and, above it, the docs
it cites) wins; fix this file, not the other way around.

Source of truth: `docs/02_technical_requirements.md`, `docs/06_backend_schema.md`,
`docs/team_plan.md`, `docs/problem_statement.md`.

Backfilled after the fact (Day 6) — `contracts.py` was frozen End of Day 1;
this document did not exist until now. No values were changed to write it.

---

## 1. Routing Categories

The four categories the LangGraph supervisor branches on (`RoutingCategory`):

| Value                |
| -------------------- |
| `KNOWLEDGE_QUERY`  |
| `DATABASE_QUERY`   |
| `API_QUERY`        |
| `MULTI_TOOL_QUERY` |

---

## 2. Business Intents

`BusinessIntent` — finer-grained intent used in `CoPilotState.intent` and
`audit_log.detected_intent`:

| Intent              | Routing Category     | Why                                                                                                                     |
| ------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `order_status`    | `DATABASE_QUERY`   | Answerable from`sales_orders`/`order_items` alone.                                                                  |
| `shipment_status` | `API_QUERY`        | Live carrier/tracking data, not a DB read.                                                                              |
| `inventory`       | `DATABASE_QUERY`   | Answerable from`inventory` alone.                                                                                     |
| `sop_lookup`      | `KNOWLEDGE_QUERY`  | Policy/procedure text lives only in the KB.                                                                             |
| `report`          | `DATABASE_QUERY`   | Aggregate/tabular query against allow-listed tables.                                                                    |
| `sla_check`       | `MULTI_TOOL_QUERY` | `business_rule_agent` needs DB (promised date, tier) + API (current shipment state) results together.                 |
| `delay_analysis`  | `MULTI_TOOL_QUERY` | Same as`sla_check`, plus KB guidance (the relevant SOP) for a "why and what do we do" answer (problem_statement §6). |

`INTENT_TO_ROUTING` (exact mapping, `contracts.py` §2):

```python
{
    SOP_LOOKUP: KNOWLEDGE_QUERY,
    ORDER_STATUS: DATABASE_QUERY,
    INVENTORY: DATABASE_QUERY,
    REPORT: DATABASE_QUERY,
    SHIPMENT_STATUS: API_QUERY,
    SLA_CHECK: MULTI_TOOL_QUERY,
    DELAY_ANALYSIS: MULTI_TOOL_QUERY,
}
```

**Worked example (flagship, see §9):** "Where is SO-45892? Why is it delayed
and what action should we take?" carries at least `delay_analysis` (and
implicitly touches `order_status`/`shipment_status` data) → routes
`MULTI_TOOL_QUERY`, pulling DB (order/customer/tier), API (shipment/carrier
status), and KB (Customs Hold SOP) together.

---

## 3. Agent / Node Names

The seven LangGraph nodes, all owned by Person 3 (`AgentNode`, exact names —
do not rename):

1. `intent_classifier`
2. `knowledge_base_agent`
3. `text_to_sql_agent`
4. `api_status_agent`
5. `business_rule_agent`
6. `final_response_agent`
7. `error_handler`

---

## 4. LangGraph State — `CoPilotState`

Internal graph state only — never returned directly over the wire (see §8 for
the wire schema).

| Field              | Type               | Notes                                   |
| ------------------ | ------------------ | --------------------------------------- |
| `session_id`     | `str`            |                                         |
| `user_id`        | `str`            |                                         |
| `raw_query`      | `str`            |                                         |
| `intent`         | `str`            | Primary intent, e.g.`"order_status"`. |
| `sub_intents`    | `list[str]`      | Multiple agents may be required.        |
| `kb_result`      | `dict \| None`    |                                         |
| `sql_result`     | `dict \| None`    |                                         |
| `api_result`     | `dict \| None`    |                                         |
| `rule_result`    | `dict \| None`    |                                         |
| `retry_count`    | `dict[str, int]` | Keyed per node, see §7.                |
| `final_response` | `str \| None`     | See open question, §10.                |
| `error`          | `str \| None`     |                                         |

---

## 5. MCP Tool Interface Stubs

Exact names and typed I/O, owned by Person 2 via MCP (`contracts.py` §5).
Every stub currently raises `NotImplementedError("Owned by Person 2 via MCP")`
— that is intentional, not a bug to fix.

| Tool                    | Signature                    | Returns                                                 |
| ----------------------- | ---------------------------- | ------------------------------------------------------- |
| `kb_search`           | `(query: str, top_k: int)` | `list[KBHit]`                                         |
| `db_query`            | `(sql: str)`               | `DBResult` — `sql` must already be validated (§6) |
| `get_order_status`    | `(order_no: str)`          | `OrderStatus`                                         |
| `get_shipment_status` | `(tracking_no: str)`       | `ShipmentStatus`                                      |
| `get_inventory`       | `(sku: str)`               | `InventoryRecord`                                     |

**`KBHit`** (one `kb_search` result item):

| Field          | Type      |
| -------------- | --------- |
| `content`    | `str`   |
| `source_doc` | `str`   |
| `score`      | `float` |

**`DBResult`**: `rows: list[dict]`

**`OrderStatus`**: `order_no: str`, `status: str`, `promised_delivery_date: str \| None`, `revised_delivery_date: str \| None`

**`ShipmentStatus`**: `tracking_no: str`, `shipment_status: str`, `current_location: str \| None`, `delay_reason: str \| None`

**`InventoryRecord`**: `sku: str`, `quantity_on_hand: int`, `quantity_reserved: int`

---

## 6. Text-to-SQL Constants

Shared contract (`docs/06_backend_schema.md` §4): Person 2 owns this table
list and the `copilot_readonly` role it maps to; Person 3 owns the validator
enforcing it. Neither may change it unilaterally.

**`SQL_TABLE_ALLOWLIST`** (10 tables — `SELECT` only):

```
customers, sales_orders, order_items, inventory, warehouse,
shipment, invoice, payment, carrier_tracking, sla_rules
```

**Denied tables** (never exposed to generated SQL, by omission from the
allowlist): `users`, `audit_log`, `knowledge_documents`, `knowledge_chunks`.

**`SQL_DENIED_KEYWORDS`** (6): `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`

**`SQL_ROW_LIMIT`**: `200`

---

## 7. Retry / Fallback Policy

**`MAX_RETRIES_PER_NODE = 1`** — a whole LangGraph node retries at most once
before falling back to a partial/error response. This is a different layer
from `ai/llm_client.py`'s own failure handling (that module has no
second-provider fallback; a failed call raises `LLMProviderError` directly) —
the two are not to be conflated.

---

## 8. Sources, SLA Status, and the Wire Response Schema

**`Source`** (a citation derived from a `KBHit`):

| Field             | Type             |
| ----------------- | ---------------- |
| `document_name` | `str`          |
| `snippet`       | `str \| None`   |
| `doc_id`        | `int \| None`   |
| `score`         | `float \| None` |

**`SLAStatus`** (matches `docs/06_backend_schema.md` §6 `sla_result` wording):

| Value        |
| ------------ |
| `On Time`  |
| `At Risk`  |
| `Breached` |
| `N/A`      |

SLA breach logic (`docs/06_backend_schema.md` §6, computed by the Business
Rule Agent):

```
delay_days = CURRENT_DATE - promised_delivery_date
IF delay_days > max_delay_days(tier):  Breached
ELIF delay_days > 0:                   At Risk
ELSE:                                  On Time
```

Tiers and `max_delay_days` (`ai/knowledge_base/01_sla_policy.md`):

| Tier     | `max_delay_days` | Escalation Role              |
| -------- | ------------------ | ---------------------------- |
| STANDARD | 3 days             | Logistics Coordinator        |
| GOLD     | 5 days             | Logistics Manager            |
| PLATINUM | 7 days             | Regional Operations Director |

**`CoPilotResponse`** — the wire/structured response: FastAPI → Spring Boot →
Angular (P1.9):

| Field                      | Type                | Notes                                                                         |
| -------------------------- | ------------------- | ----------------------------------------------------------------------------- |
| `answer_text`            | `str`             |                                                                               |
| `intent`                 | `RoutingCategory` |                                                                               |
| `order_status`           | `str \| None`      |                                                                               |
| `shipment_status`        | `str \| None`      |                                                                               |
| `current_location`       | `str \| None`      |                                                                               |
| `delay_reason`           | `str \| None`      |                                                                               |
| `delay_days`             | `int \| None`      |                                                                               |
| `sla_status`             | `SLAStatus`       |                                                                               |
| `recommended_actions`    | `list[str]`       | Default`[]`.                                                                |
| `sources`                | `list[Source]`    | Default`[]`.                                                                |
| `partial`                | `bool`            | Set when a data source was unavailable after 1 retry (§7). Default`False`. |
| `error`                  | `str \| None`      |                                                                               |
| `promised_delivery_date` | `date \| None`     | Added 2026-07-17, see changelog below.                                        |
| `revised_delivery_date`  | `date \| None`     | Added 2026-07-17, see changelog below.                                        |

**Changelog:**

- **2026-07-17** — Amended `CoPilotResponse` to add `promised_delivery_date` /
  `revised_delivery_date` (Person 3 decision, replacing Person 1's provisional
  `AiQueryResponse` subclass in `ai_service/schemas.py`) — pending Person 1 +
  Person 2 confirmation.

---

## 9. Flagship Scenario — SO-45892

Canonical worked example, referenced throughout the knowledge base, the SLA
Policy, and `docs/problem_statement.md`. Facts (`ai/knowledge_base/01_sla_policy.md`
"Worked Example" + `ai/knowledge_base/03_customs_hold_sop.md`):

- Customer tier: **GOLD** (`max_delay_days` = 5)
- `promised_delivery_date`: 2026-07-03
- `revised_delivery_date` (current ETA): 2026-07-09
- Delay: **6 days** past promised delivery
- 6 days > 5-day GOLD threshold → SLA status = **Breached**
- Escalation role triggered: **Logistics Manager**
- Root cause: shipment in `Customs Hold` at Chennai Port due to an **HS code
  mismatch** during customs validation (Customs Hold SOP resolution steps 1–7)
- Live-verified (Day 6, see P3.4 gate closure): the Knowledge Base Agent's
  generated answer for the HS-code-mismatch question reproduces all 7
  resolution steps and every specific fact above, grounded in the Customs
  Hold SOP — no hallucination.

---

## 10. Open Questions (Awaiting Person 1 + Person 2 Sign-off)

**`final_response` shape conflict.** `CoPilotState.final_response` (§4) is
typed `str | None`, matching `docs/02_technical_requirements.md` §3.1
verbatim. `CoPilotResponse` (§8) is a separate, structured wire model, where
`answer_text` is the prose-summary analogue of `final_response`.

Proposed clarification, not yet confirmed: `CoPilotState.final_response`
stays a plain string internally (graph state is not meant to carry the full
structured envelope), and the `final_response_agent` node is responsible for
*building* the structured `CoPilotResponse` from graph state (including
`final_response` as `answer_text`) at the point the API layer needs it. This
avoids duplicating every `CoPilotResponse` field into `CoPilotState`, but
changes what "the final response" means depending on which layer is asking.

**Needs sign-off from Person 1 (owns the FastAPI → Spring Boot → Angular wire
contract) and Person 2 (owns the MCP tool outputs feeding graph state)**
before `final_response_agent` (P3.8) is implemented against either
interpretation.

---

## Approval

- [X] Person 1 — reviewed, no objection to the wire schema (§8) or the open
  question (§10)
- [X] Person 2 — reviewed, no objection to the MCP tool signatures (§5) or
  the SQL allow-list (§6)

---

## 11. MCP Client Decision (Day 11)

Until today, `db_boundary.py` / `api_boundary.py` called the tool-layer
functions directly instead of going over MCP (see their module docstrings) —
a deliberate placeholder pending a whole-team scope call: accept the
direct-call shortcut permanently, or build a real MCP client.

**Decision: build a real MCP client.** `mcp_server/server.py`'s tool surface
is frozen as of today at the 5 live tools (`db_query`, `get_order`,
`get_order_status`, `get_shipment_status`, `get_inventory`); `kb_search`
stays out of scope until routing KB retrieval through MCP earns its keep
(server.py's own trailing note). Both boundary modules now hold a real
`ClientSession` (streamable-http, `MCP_SERVER_URL`) instead of importing
`ai_service/tools/*` directly — see their updated docstrings and
`ai/mcp_client.py`.

**Day 12 follow-up:** `ai/graph/nodes.py` was still importing
`ai_service.tools.db.get_order` directly, bypassing this boundary for the
one tool Day 11 missed. Fixed — `db_boundary.get_order` now routes through
MCP too, and converts the date fields (`order_date`,
`promised_delivery_date`, `revised_delivery_date`) back from the ISO
strings the MCP JSON wire format carries them as into `datetime.date`,
since `business_rule_agent_node` does date arithmetic on them.
