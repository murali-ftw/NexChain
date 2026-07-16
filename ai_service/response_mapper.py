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


def _recommended_actions(rule_result: dict, api_result: dict) -> list[str]:
    actions: list[str] = []
    if rule_result.get("sla_status") == SLAStatus.BREACHED.value:
        escalation_role = rule_result.get("escalation_role")
        if escalation_role:
            actions.append(f"Escalate to the {escalation_role}.")
    delay_reason = api_result.get("delay_reason")
    if delay_reason:
        actions.append(f"Review the root cause ({delay_reason}) and follow the applicable SOP.")
    if rule_result.get("revised_delivery_date"):
        actions.append("Notify the customer with the revised delivery estimate.")
    return actions


def _sources(kb_result: dict) -> list[SourceOut]:
    return [SourceOut(**hit) for hit in kb_result.get("sources") or []]


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

    error = _first_error(state)
    sla_status = (
        SLAStatus(rule_result["sla_status"]) if rule_result.get("sla_status") else SLAStatus.NOT_APPLICABLE
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
        "recommended_actions": _recommended_actions(rule_result, api_result),
        "sources": _sources(kb_result),
        "partial": error is not None,
        "error": error,
        "promised_delivery_date": rule_result.get("promised_delivery_date"),
        "revised_delivery_date": rule_result.get("revised_delivery_date"),
    }
