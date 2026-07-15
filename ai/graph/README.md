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

Neither `db_boundary.py` (`ai/agents/text_to_sql_agent/`) nor
`api_boundary.py` (here) talks to a real MCP client — none exists in this
repo yet. Both call the same tool-layer functions the MCP server itself
calls (`ai_service/tools/db.py`, `ai_service/tools/api_client.py`), so the
code path is identical to going over MCP. When a real `ClientSession`
exists project-wide, only these two files change — nothing above them
(agents, validator, prompts, graph nodes) does.

`retry.py` enforces `MAX_RETRIES_PER_NODE=1` uniformly: one retry on a
retryable failure (`ToolError.retryable`, or any LLM call failure), then
the node degrades gracefully — its result field carries `{"error": ...}`
instead of the graph crashing.

## STATUS (Day 8)

- **Routing gate MET** — all 4 required paths (`KNOWLEDGE_QUERY`,
  `DATABASE_QUERY`, `API_QUERY`, `MULTI_TOOL_QUERY`) verified via
  `python -m ai.graph.eval`, including the flagship SO-45892 case.
  `error_handler` and `retry_count`/`MAX_RETRIES_PER_NODE` verified too.
- **Live-data correctness is Day 9** (P3.9) — the DB and mock APIs are
  offline in dev right now, so today's run proved graceful degradation
  under real tool failures, not correctness against real rows/responses.
- **`business_rule_agent` and `final_response_agent` are stubs** — Day 10
  (P3.10) and Day 11 (P3.11) own their real logic.
- **Order → tracking-number resolution is an unowned gap.** The flagship
  question gives an order number, not a tracking number; `api_status_agent`
  currently reports "no tracking number found in query" for it, since
  cross-referencing one to the other is multi-agent integration work
  (P3.9), not something any P3.x day explicitly owns yet. Needs a decision
  at standup.
