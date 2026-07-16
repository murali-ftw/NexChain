"""P3.8 LangGraph nodes — thin wrappers around the existing P3.4/P3.5
agents and the P2.7/P2.8 tool layer (via ai/graph/*_boundary.py).

business_rule_agent and final_response_agent are intentionally minimal
here — P3.10 (Day 10) and P3.11 (Day 11) own their real logic. This file
only has to let the graph reach every contract node and close cleanly.
"""

from __future__ import annotations

from ai.agents.knowledge_base_agent.agent import answer_policy_question
from ai.agents.text_to_sql_agent.agent import generate_sql
from ai.agents.text_to_sql_agent.db_boundary import db_query, resolve_tracking_no
from ai.contracts import AgentNode
from ai.graph.api_boundary import get_shipment_status
from ai.graph.entities import extract_order_no, extract_tracking_no
from ai.graph.retry import call_with_retry
from ai.graph.state import CoPilotState


def knowledge_base_agent_node(state: CoPilotState) -> CoPilotState:
    node = AgentNode.KNOWLEDGE_BASE_AGENT.value
    retry_count = dict(state.get("retry_count") or {})
    attempts_before = retry_count.get(node, 0)

    result, error, attempts = call_with_retry(
        attempts_before, lambda: answer_policy_question(state["raw_query"])
    )
    retry_count[node] = attempts
    if error:
        return {"kb_result": {"error": error}, "retry_count": retry_count}
    return {
        "kb_result": {
            "answer": result.answer,
            "sources": [s.model_dump() for s in result.sources],
            "abstained": result.abstained,
        },
        "retry_count": retry_count,
    }


def text_to_sql_agent_node(state: CoPilotState) -> CoPilotState:
    node = AgentNode.TEXT_TO_SQL_AGENT.value
    retry_count = dict(state.get("retry_count") or {})
    attempts_before = retry_count.get(node, 0)

    # generate_sql() calls the LLM directly (ai/llm_client.generate) — wrapped
    # here, like the db_query call below and knowledge_base_agent_node's own
    # LLM call, so an LLM outage/misconfiguration degrades this node's result
    # (tech-req §7) instead of crashing the whole graph invocation.
    generation, error, attempts = call_with_retry(
        attempts_before,
        lambda: generate_sql(state["raw_query"], intent_hint=state.get("intent")),
    )
    retry_count[node] = attempts
    if error:
        return {
            "sql_result": {"sql": None, "error": error},
            "retry_count": retry_count,
        }
    assert generation is not None  # call_with_retry: error is None => result is set
    sql = generation.sql
    if generation.abstained or not sql:
        return {
            "sql_result": {
                "sql": None,
                "error": generation.reason or "SQL generation abstained",
            },
            "retry_count": retry_count,
        }

    db_result, error, attempts = call_with_retry(attempts, lambda: db_query(sql))
    retry_count[node] = attempts
    if error:
        return {
            "sql_result": {"sql": sql, "error": error},
            "retry_count": retry_count,
        }
    return {
        "sql_result": {"sql": sql, "rows": db_result.rows},
        "retry_count": retry_count,
    }


def api_status_agent_node(state: CoPilotState) -> CoPilotState:
    """Resolves a tracking number two ways: directly from the query text
    (TRK-...), or — when the query only gives an order number, as the
    flagship phrasing does — via a live DB lookup (db_boundary.
    resolve_tracking_no) from sales_orders to the order's shipment."""
    node = AgentNode.API_STATUS_AGENT.value
    retry_count = dict(state.get("retry_count") or {})
    attempts_before = retry_count.get(node, 0)

    tracking_no = extract_tracking_no(state["raw_query"])
    order_no = None
    if not tracking_no:
        order_no = extract_order_no(state["raw_query"])
        if order_no:
            # Its own fresh MAX_RETRIES_PER_NODE budget, not the leftover
            # from this lookup threaded into the shipment-status call below
            # — otherwise a transient failure here silently costs the
            # shipment-status call its only retry too.
            tracking_no, error, resolve_attempts = call_with_retry(
                attempts_before, lambda: resolve_tracking_no(order_no)
            )
            if error:
                retry_count[node] = resolve_attempts
                return {"api_result": {"error": error}, "retry_count": retry_count}

    if not tracking_no:
        retry_count[node] = attempts_before
        detail = (
            f"order {order_no} has no shipment yet"
            if order_no
            else "no tracking or order number found in query"
        )
        return {"api_result": {"error": detail}, "retry_count": retry_count}

    result, error, attempts = call_with_retry(
        attempts_before, lambda: get_shipment_status(tracking_no)
    )
    retry_count[node] = attempts
    if error:
        return {"api_result": {"error": error}, "retry_count": retry_count}
    return {"api_result": result.model_dump(), "retry_count": retry_count}


def business_rule_agent_node(state: CoPilotState) -> CoPilotState:
    """STUB — P3.10 (Day 10) owns real SLA/delay/escalation logic. This
    only lets the graph proceed to final_response_agent with whatever
    kb/sql/api results were gathered."""
    return {"rule_result": {"stub": True}}


def final_response_agent_node(state: CoPilotState) -> CoPilotState:
    """MINIMAL placeholder — P3.11 (Day 11) owns real structured-response
    assembly (order/shipment status, delay days, SLA status, recommended
    actions, sources). This only echoes what was gathered so the graph
    has a defined terminal value to test against today."""
    parts = []
    if state.get("kb_result"):
        parts.append(f"kb_result={state['kb_result']}")
    if state.get("sql_result"):
        parts.append(f"sql_result={state['sql_result']}")
    if state.get("api_result"):
        parts.append(f"api_result={state['api_result']}")
    if state.get("error"):
        parts.append(f"error={state['error']}")
    return {"final_response": "; ".join(parts) or "no data gathered"}


def error_handler_node(state: CoPilotState) -> CoPilotState:
    """Reached only when intent classification itself fails outright (no
    routable business_intent) — per-branch tool failures degrade
    gracefully in place instead (see ai/graph/routing.py)."""
    return {"final_response": None, "error": state.get("error") or "unhandled error"}
