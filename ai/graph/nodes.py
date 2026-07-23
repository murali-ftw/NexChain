"""P3.8 LangGraph nodes — thin wrappers around the existing P3.4/P3.5
agents and the P2.7/P2.8 tool layer (via ai/graph/*_boundary.py).

business_rule_agent and final_response_agent are intentionally minimal
here — P3.10 (Day 10) and P3.11 (Day 11) own their real logic. This file
only has to let the graph reach every contract node and close cleanly.
"""

from __future__ import annotations

import datetime
import json

from ai.agents.business_rule_agent.rules import RuleEngineInput, evaluate
from ai.agents.knowledge_base_agent.agent import answer_policy_question
from ai.agents.text_to_sql_agent.agent import generate_sql
from ai.agents.text_to_sql_agent.db_boundary import (
    db_query,
    get_order,
    resolve_tracking_no,
)
from ai.contracts import AgentNode, SLAStatus
from ai.graph.api_boundary import get_shipment_status
from ai.graph.entities import extract_order_no, extract_tracking_no
from ai.graph.retry import call_with_retry
from ai.graph.state import CoPilotState, CoPilotStateUpdate
from ai.llm_client import LLMConfigError, LLMProviderError, generate


def knowledge_base_agent_node(state: CoPilotState) -> CoPilotStateUpdate:
    """For a MULTI_TOOL_QUERY, routing.py always sequences this node after
    text_to_sql_agent/api_status_agent (required_nodes() preserves
    sub_intents order, and DELAY_ANALYSIS's sub_intents put sop_lookup
    last) — so by the time this runs, api_result may already carry the
    shipment's delay_reason (e.g. "HS code mismatch during customs
    validation."). That's a far better semantic-search query than the raw
    multi-part question ("Where is order X, why is it delayed, what
    should we do") — the KB is organized around cause-specific SOPs
    (Customs Hold, Inventory Shortage, ...) phrased close to the delay
    reason itself, not around entity references the retriever has no
    embeddings for. Falls back to the raw query for pure policy
    questions (no api_result yet) and multi-tool queries where the API
    branch didn't produce a cause.
    """
    node = AgentNode.KNOWLEDGE_BASE_AGENT.value
    retry_count = dict(state.get("retry_count") or {})
    attempts_before = retry_count.get(node, 0)

    delay_reason = (state.get("api_result") or {}).get("delay_reason")
    question = delay_reason or state["raw_query"]

    result, error, attempts = call_with_retry(
        attempts_before, lambda: answer_policy_question(question)
    )
    retry_count[node] = attempts
    if error:
        return {"kb_result": {"error": error}, "retry_count": retry_count}
    assert result is not None  # call_with_retry: error is None => result is set
    return {
        "kb_result": {
            "answer": result.answer,
            "sources": [s.model_dump() for s in result.sources],
            "abstained": result.abstained,
        },
        "retry_count": retry_count,
    }


def text_to_sql_agent_node(state: CoPilotState) -> CoPilotStateUpdate:
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
    assert db_result is not None  # call_with_retry: error is None => result is set
    return {
        "sql_result": {"sql": sql, "rows": db_result.rows},
        "retry_count": retry_count,
    }


def api_status_agent_node(state: CoPilotState) -> CoPilotStateUpdate:
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
    assert result is not None  # call_with_retry: error is None => result is set
    return {"api_result": result.model_dump(), "retry_count": retry_count}


def business_rule_agent_node(state: CoPilotState) -> CoPilotStateUpdate:
    """P3.10 — SLA breach detection, delay calculation, escalation severity,
    and corrective-action selection, delegated to the pure, unit-tested rule
    engine (ai/agents/business_rule_agent/rules.py — 10/10 exact-match
    against hardcoded scenarios including the flagship, both severity tiers
    of At Risk, and every tier's breach threshold boundary). This node's job
    is only to fetch the real order data and translate it into
    RuleEngineInput/Output; the deterministic classification logic itself
    lives in rules.py so it's testable without a live DB.

    Re-fetches the order via db.get_order() rather than reading
    sql_result — text_to_sql_agent's SQL is LLM-generated from the raw
    question and has no guaranteed shape, whereas get_order() is the
    fixed, authoritative query that already joins customers.sla_tier
    (db.py's own docstring: "the Business Rule Agent needs the
    customer's sla_tier ... to decide breach/escalation").

    Tier thresholds/escalation roles come from rules.TIER_RULES (sourced
    from 01_sla_policy.md / 05_escalation_matrix.md) rather than a live
    sla_rules query — those are documented constants, not operational data
    expected to change without a doc update, so this also drops a DB
    round-trip the previous inline version made per call.

    Every branch of next_pending_node's routing (ai/graph/routing.py)
    passes through this node, including single-source queries with no
    order number (inventory, generic SOP lookups) — those correctly
    produce sla_status N/A rather than an error.
    """
    node = AgentNode.BUSINESS_RULE_AGENT.value
    retry_count = dict(state.get("retry_count") or {})
    attempts_before = retry_count.get(node, 0)

    order_no = extract_order_no(state["raw_query"])
    if not order_no:
        return {"rule_result": {"sla_status": SLAStatus.NOT_APPLICABLE.value}}

    order, error, attempts = call_with_retry(
        attempts_before, lambda: get_order(order_no)
    )
    retry_count[node] = attempts
    if error:
        return {"rule_result": {"error": error}, "retry_count": retry_count}
    if order is None:
        # Not an error: a query naming an order that doesn't exist is a fact
        # about the data, not a pipeline degradation (same distinction
        # ToolNotFound draws from ToolUnavailable in ai_service/tools/errors.py)
        # — no "error" key here, so response_mapper doesn't mark this partial.
        return {
            "rule_result": {
                "order_no": order_no,
                "sla_status": SLAStatus.NOT_APPLICABLE.value,
            },
            "retry_count": retry_count,
        }

    current_status = order.get("current_status")
    promised = order.get("promised_delivery_date")
    revised = order.get("revised_delivery_date")
    # "Delay days" per policy is CURRENT_DATE - promised_delivery_date, but once a
    # cause-specific SOP has set a revised ETA that's the best current estimate of
    # actual delivery, so it's used in preference to today's date (matching the
    # policy's own worked example: 2026-07-09 revised vs. 2026-07-03 promised = 6
    # days, not a figure that would keep climbing every day the ETA holds steady).
    as_of_date = revised or datetime.date.today()

    result = evaluate(
        RuleEngineInput(
            order_no=order_no,
            sla_tier=order.get("sla_tier"),
            current_status=current_status,
            promised_delivery_date=promised,
            revised_delivery_date=revised,
            as_of_date=as_of_date,
            shipment_status=(state.get("api_result") or {}).get("shipment_status"),
            delay_reason=(state.get("api_result") or {}).get("delay_reason"),
        )
    )

    return {
        "rule_result": {
            "order_no": order_no,
            "current_status": current_status,
            "promised_delivery_date": promised.isoformat() if promised else None,
            "revised_delivery_date": revised.isoformat() if revised else None,
            "delay_days": result.delay_days,
            "sla_status": result.sla_status.value,
            "sla_tier": order.get("sla_tier"),
            "severity": result.severity,
            "escalation_role": result.escalation_role,
            "recommended_actions": result.recommended_actions,
        },
        "retry_count": retry_count,
    }


def final_response_agent_node(state: CoPilotState) -> CoPilotStateUpdate:
    """P3.11 — assembles the prose answer_text from whatever kb/sql/api/rule
    results this query gathered. The structured wire fields (order_status,
    delay_days, sla_status, sources, ...) are read directly off CoPilotState
    by the FastAPI boundary (ai_service/response_mapper.py) since
    CoPilotState itself is frozen and carries no such fields — this node
    only has to produce the human-readable summary sentence.
    """
    kb_result = state.get("kb_result") or {}
    api_result = state.get("api_result") or {}
    rule_result = state.get("rule_result") or {}
    sql_result = state.get("sql_result") or {}

    sentences: list[str] = []

    order_no = rule_result.get("order_no")
    current_status = rule_result.get("current_status")
    if order_no and current_status:
        sentences.append(f"Order {order_no} is currently {current_status}.")

    # Plain DATABASE_QUERY answers (inventory, reporting, anything with no
    # order number for business_rule_agent to look up) have no rule_result
    # to draw from — sql_result's rows are the only gathered data, so they're
    # the answer. Skipped when rule_result already produced an order-status
    # sentence above, since that's the more precise, authoritative source
    # for the same question (get_order() vs. arbitrary LLM-generated SQL).
    sql_rows = sql_result.get("rows")
    if sql_rows is not None and not current_status:
        sentences.append(_describe_rows(state["raw_query"], sql_rows))

    shipment_status = api_result.get("shipment_status")
    location = api_result.get("current_location")
    delay_reason = api_result.get("delay_reason")
    if shipment_status:
        where = f" at {location}" if location else ""
        sentences.append(f"Shipment status: {shipment_status}{where}.")
    if delay_reason:
        sentences.append(f"Cause: {delay_reason}")

    sla_status = rule_result.get("sla_status")
    delay_days = rule_result.get("delay_days")
    if sla_status and sla_status != SLAStatus.NOT_APPLICABLE.value:
        sentences.append(
            f"SLA status: {sla_status} ({delay_days} day(s) past the promised date)."
        )
        escalation_role = rule_result.get("escalation_role")
        if escalation_role:
            sentences.append(f"Escalated to: {escalation_role}.")

    # The KB's prose answer is only appended for queries it's actually meant
    # to ground (pure policy/SOP lookups). For a query that already resolved
    # concrete order/shipment facts, knowledge_base_agent_node still searched
    # on the raw question text (P3.8) — not tuned for entity lookups — and
    # its "I have no record of order X" answer would flatly contradict the
    # operational facts just stated above. Its sources are still surfaced as
    # citations either way (response_mapper.state_to_fields), just without
    # this sentence riding along.
    kb_answer = kb_result.get("answer")
    has_operational_facts = bool(order_no or shipment_status)
    if kb_answer and not kb_result.get("abstained") and not has_operational_facts:
        sentences.append(kb_answer)

    if sentences:
        return {"final_response": " ".join(sentences)}

    # Nothing gathered anything usable (every branch abstained/erred, or this
    # was a total classification failure already routed through error_handler).
    error = (
        state.get("error")
        or rule_result.get("error")
        or api_result.get("error")
        or kb_result.get("error")
        or sql_result.get("error")
    )
    return {
        "final_response": None,
        "error": error or "no data available to answer this question",
    }


_DESCRIBE_ROWS_PROMPT = """You are answering a supply-chain question using ONLY the database rows below \
— do not use any outside knowledge, and do not invent facts that are not present in the rows.

Question: {question}

Rows (JSON): {rows_json}

Write a single, natural, concise answer (one or two sentences). State the facts plainly; do not \
mention SQL, databases, rows, or that this data came from a query."""


def _describe_rows(question: str, rows: list[dict], limit: int = 20) -> str:
    """Phrases text_to_sql_agent's rows as a natural answer to the original
    question. The query and its columns are LLM-generated per-question
    (ai/agents/text_to_sql_agent) — there's no fixed schema to hang a
    template off of, so an LLM call (already this codebase's pattern for
    turning retrieved data into prose — see knowledge_base_agent) reads
    far better than a raw key=value dump. Falls back to that dump if the
    LLM call itself fails, so a degraded LLM never means a degraded answer
    for data that's already sitting right there.
    """
    if not rows:
        return "No matching records were found."
    prompt = _DESCRIBE_ROWS_PROMPT.format(
        question=question, rows_json=json.dumps(rows[:limit], default=str)
    )
    try:
        return generate(prompt).strip()
    except (LLMConfigError, LLMProviderError):
        return _summarize_rows(rows)


def _summarize_rows(rows: list[dict], limit: int = 5) -> str:
    """Generic, column-agnostic prose rendering of text_to_sql_agent's rows —
    the fallback for _describe_rows when the LLM call itself fails.
    Accurate-but-plain beats silently dropping real data."""
    if not rows:
        return "No matching records were found."
    lines = [
        ", ".join(f"{key}={value}" for key, value in row.items())
        for row in rows[:limit]
    ]
    summary = "; ".join(lines) + "."
    if len(rows) > limit:
        summary += f" ({len(rows) - limit} more row(s) not shown.)"
    return summary


def error_handler_node(state: CoPilotState) -> CoPilotStateUpdate:
    """Reached only when intent classification itself fails outright (no
    routable business_intent) — per-branch tool failures degrade
    gracefully in place instead (see ai/graph/routing.py)."""
    return {"final_response": None, "error": state.get("error") or "unhandled error"}
