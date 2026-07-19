# LangGraph Supervisor (P3.8, Day 8)

Stateful orchestration over the existing P3.4/P3.5/P3.7 agents: classify a
query, route it to the node(s) it requires, and converge on a single
terminal response.

## Nodes (`ai/contracts.py`, frozen, do not rename)

1. `intent_classifier` (`supervisor.py`) — calls the P3.7 classifier, writes
   `intent` + `sub_intents`.
2. `knowledge_base_agent` (`nodes.py`) — wraps the P3.4 KB agent, writes
   `kb_result`.
3. `text_to_sql_agent` (`nodes.py`) — wraps the P3.5 SQL agent, executes the
   validated SQL via `db_boundary.db_query`, writes `sql_result`.
4. `api_status_agent` (`nodes.py`) — new this task. Wraps Person 2's
   operational API tools via `api_boundary.py`, writes `api_result`.
5. `business_rule_agent` (`nodes.py`) — **stub** (Day 10).
6. `final_response_agent` (`nodes.py`) — **minimal placeholder** (Day 11).
7. `error_handler` (`nodes.py`) — reached only when intent classification
   itself can't resolve a `routing_category` at all.

## Routing model (`routing.py`)

Single-source intents (`order_status`, `inventory`, `report` →
`text_to_sql_agent`; `shipment_status` → `api_status_agent`; `sop_lookup` →
`knowledge_base_agent`) route straight to their one node via
`INTENT_TO_ROUTING`.

`MULTI_TOOL_QUERY` (`sla_check`, `delay_analysis`) visits every node its
`sub_intents` require — but **sequentially, not in parallel**: each branch,
on finishing, routes to the next still-pending required branch
(`next_pending_node`), then to `business_rule_agent` once none remain.
This is deliberate: `CoPilotState` (`ai/contracts.py`, frozen) is a plain
`TypedDict` with no `Annotated` merge reducers, so LangGraph cannot accept
concurrent writes to a shared key (`retry_count`, in particular) from
parallel branches in one superstep. Changing that would mean amending a
frozen shared contract without a name; sequencing avoids the conflict
entirely while still reaching every required node.

## Swap-point pattern

`db_boundary.py` (`ai/agents/text_to_sql_agent/`) and `api_boundary.py`
(here) both talk to a real MCP client as of Day 11 (`ai/CONTRACTS.md` §11,
`ai/mcp_client.py`) — a `ClientSession` over the independently-running
`mcp_server` service, not the direct tool-layer calls
(`ai_service/tools/db.py`, `ai_service/tools/api_client.py`) they used while
no MCP client existed. Only these two files (plus `mcp_client.py` itself)
know MCP exists — nothing above them (agents, validator, prompts, graph
nodes) changed.

`retry.py` enforces `MAX_RETRIES_PER_NODE=1` uniformly: one retry on a
retryable failure (`ToolError.retryable`, or any LLM call failure), then
the node degrades gracefully — its result field carries `{"error": ...}`
instead of the graph crashing.

## STATUS

**Day 8 (P3.8):** LangGraph supervisor — all 4 paths route to correct
nodes; retry + error_handler proven.

**Day 9 (P3.9): MET (live)** — the flagship (SO-45892) gathers real data
from DB + API + KB into graph state. Order → tracking-number resolution,
the gap Day 8 flagged as unowned, is now resolved live: `api_status_agent`
falls back from `extract_tracking_no` to `db_boundary.resolve_tracking_no`
when the query gives an order number but no tracking number, cross-
referencing `sales_orders` → `shipment` (SO-45892 → TRK-45892-1) against
the live DB.

**DAY-10 FOLLOW-UPS (not gaps in D8/D9):**
- KB retrieval doesn't surface the Customs Hold SOP for the flagship
  phrasing — `business_rule_agent` should re-query/re-rank KB using the
  delay cause the API branch discovers, rather than the bare raw query.
- SLA-breach math must query `promised_delivery_date`/`revised_delivery_date`
  explicitly, not rely on whatever columns `text_to_sql_agent` happened to
  select for a given phrasing.

**Still stubbed:** `business_rule_agent` (Day 10), `final_response_agent`
(Day 11).
