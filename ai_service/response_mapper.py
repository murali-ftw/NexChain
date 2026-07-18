"""P2.10 — maps a finished CoPilotState into the CoPilotResponse wire shape.

The LangGraph nodes (ai/graph/nodes.py, Person 3) write their raw findings
into kb_result / sql_result / api_result / rule_result; this module is the
FastAPI-side translation from those internal shapes into the frozen
CoPilotResponse contract (ai/contracts.py) that Spring Boot consumes.
Lives here, not in ai/graph/, because CoPilotState itself carries none of
these wire fields (see nodes.py's final_response_agent_node docstring) —
this is boundary-layer assembly, not agent logic, matching the separation
ai/graph/api_boundary.py and ai/graph/*_boundary.py already establish
between agent code and the tool/wire layer.
"""

from __future__ import annotations

from ai.contracts import (
    INTENT_TO_ROUTING,
    AgentNode,
    BusinessIntent,
    CoPilotState,
    RoutingCategory,
    SLAStatus,
)
from ai_service.schemas import SourceOut

_FALLBACK_ANSWER = (
    "I couldn't find enough information to answer that question — please try "
    "rephrasing it, or contact support if the issue persists."
)

_RESULT_FIELDS = ("kb_result", "sql_result", "api_result", "rule_result")

# Which state result field, if present, proves the corresponding branch node
# actually ran (ai/graph/graph.py: intent_classifier and final_response_agent
# are on every path; the rest run only when routing.required_nodes() picked
# them). Order matches execution order, not declaration order in CoPilotState.
_BRANCH_NODE_FOR_FIELD = (
    ("sql_result", AgentNode.TEXT_TO_SQL_AGENT),
    ("api_result", AgentNode.API_STATUS_AGENT),
    ("kb_result", AgentNode.KNOWLEDGE_BASE_AGENT),
    ("rule_result", AgentNode.BUSINESS_RULE_AGENT),
)


def _routing_category(state: CoPilotState) -> RoutingCategory:
    intent = state.get("intent") or ""
    try:
        return INTENT_TO_ROUTING[BusinessIntent(intent)]
    except ValueError:
        # No resolvable category (total classification failure via
        # error_handler) — DATABASE_QUERY is an arbitrary but harmless
        # default; the accompanying `error`/`partial` fields carry the
        # real signal, same convention ChatService's old generic mock used.
        return RoutingCategory.DATABASE_QUERY


def _first_error(state: CoPilotState) -> str | None:
    for key in _RESULT_FIELDS:
        result = state.get(key) or {}
        if isinstance(result, dict) and result.get("error"):
            return result["error"]
    return state.get("error")


def _recommended_actions(rule_result: dict) -> list[str]:
    """The SOP-specific list business_rule_agent_node already computed
    (rules.py::corrective_actions) — not reconstructed here, since that would
    just be a worse, uncited approximation of what rule_result already has."""
    return rule_result.get("recommended_actions") or []


def _sources(kb_result: dict) -> list[SourceOut]:
    return [SourceOut(**hit) for hit in kb_result.get("sources") or []]


def _agents_invoked(state: CoPilotState) -> list[str]:
    """Every node this run actually executed, in execution order — for the
    audit log (audit_log.agents_invoked, backend_schema §2.14). intent_classifier
    and final_response_agent are unconditional (see graph.py's edges); the
    branch nodes are included exactly when their result field is present,
    since that field is only ever set by that node's own return value."""
    agents = [AgentNode.INTENT_CLASSIFIER.value]
    agents.extend(
        node.value
        for field, node in _BRANCH_NODE_FOR_FIELD
        if state.get(field) is not None
    )
    agents.append(AgentNode.FINAL_RESPONSE_AGENT.value)
    return agents


def state_to_fields(state: CoPilotState) -> dict:
    """The CoPilotResponse-shaped kwargs derived from a finished graph run.

    `partial`/`error` are unified around one signal: any sub-result (or a
    total classification failure) carrying an error message. A fully
    successful run has both False/None; anything else surfaces the first
    error found and still returns whatever prose final_response_agent_node
    could assemble from the sources that did succeed.
    """
    kb_result = state.get("kb_result") or {}
    api_result = state.get("api_result") or {}
    rule_result = state.get("rule_result") or {}
    sql_result = state.get("sql_result") or {}

    error = _first_error(state)
    sla_status = (
        SLAStatus(rule_result["sla_status"])
        if rule_result.get("sla_status")
        else SLAStatus.NOT_APPLICABLE
    )

    return {
        "answer_text": state.get("final_response") or _FALLBACK_ANSWER,
        "intent": _routing_category(state),
        "order_status": rule_result.get("current_status"),
        "shipment_status": api_result.get("shipment_status"),
        "current_location": api_result.get("current_location"),
        "delay_reason": api_result.get("delay_reason"),
        "delay_days": rule_result.get("delay_days"),
        "sla_status": sla_status,
        "recommended_actions": _recommended_actions(rule_result),
        "sources": _sources(kb_result),
        "partial": error is not None,
        "error": error,
        "promised_delivery_date": rule_result.get("promised_delivery_date"),
        "revised_delivery_date": rule_result.get("revised_delivery_date"),
        "agents_invoked": _agents_invoked(state),
        "generated_sql": sql_result.get("sql"),
    }
