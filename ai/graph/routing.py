"""Shared routing helpers for P3.8's conditional edges.

MULTI_TOOL_QUERY can require more than one branch, but CoPilotState
(ai/contracts.py) is a frozen, plain TypedDict — none of its fields carry
an Annotated merge reducer, so LangGraph cannot accept concurrent writes
to the same key (retry_count, in particular) from parallel branches in
one superstep. Multi-tool queries are therefore sequenced, not
parallel-fanned-out: each branch, on finishing, routes to the next still-
pending branch via next_pending_node, then to business_rule_agent once
every required branch has a result (success or a recorded per-branch
failure).
"""

from __future__ import annotations

from ai.contracts import AgentNode, BusinessIntent, INTENT_TO_ROUTING, RoutingCategory
from ai.graph.state import CoPilotState

_ROUTING_TO_NODE: dict[RoutingCategory, str] = {
    RoutingCategory.KNOWLEDGE_QUERY: AgentNode.KNOWLEDGE_BASE_AGENT.value,
    RoutingCategory.DATABASE_QUERY: AgentNode.TEXT_TO_SQL_AGENT.value,
    RoutingCategory.API_QUERY: AgentNode.API_STATUS_AGENT.value,
}

_RESULT_FIELD_FOR_NODE: dict[str, str] = {
    AgentNode.KNOWLEDGE_BASE_AGENT.value: "kb_result",
    AgentNode.TEXT_TO_SQL_AGENT.value: "sql_result",
    AgentNode.API_STATUS_AGENT.value: "api_result",
}

ALL_ROUTE_TARGETS: tuple[str, ...] = (
    AgentNode.KNOWLEDGE_BASE_AGENT.value,
    AgentNode.TEXT_TO_SQL_AGENT.value,
    AgentNode.API_STATUS_AGENT.value,
    AgentNode.BUSINESS_RULE_AGENT.value,
    AgentNode.ERROR_HANDLER.value,
)


def required_nodes(state: CoPilotState) -> list[str] | None:
    """The ordered set of branch nodes this query must visit, or None if
    intent/sub_intents can't be resolved against the frozen contract at
    all (a total classification failure, not a per-branch tool failure)."""
    intent = state.get("intent") or ""
    try:
        business_intent = BusinessIntent(intent)
    except ValueError:
        return None

    category = INTENT_TO_ROUTING[business_intent]
    if category != RoutingCategory.MULTI_TOOL_QUERY:
        return [_ROUTING_TO_NODE[category]]

    sub_intents = state.get("sub_intents") or [intent]
    nodes: list[str] = []
    for sub in sub_intents:
        try:
            sub_category = INTENT_TO_ROUTING[BusinessIntent(sub)]
        except ValueError:
            continue
        node = _ROUTING_TO_NODE.get(sub_category)
        if node and node not in nodes:
            nodes.append(node)
    return nodes or None


def next_pending_node(state: CoPilotState) -> str:
    """First required node with no result yet, or business_rule_agent
    once every required node has already run (success or recorded
    failure), or error_handler if the required set can't be resolved."""
    nodes = required_nodes(state)
    if not nodes:
        return AgentNode.ERROR_HANDLER.value
    for node in nodes:
        field = _RESULT_FIELD_FOR_NODE[node]
        if state.get(field) is None:
            return node
    return AgentNode.BUSINESS_RULE_AGENT.value


def route_after_supervisor(state: CoPilotState) -> str:
    if state.get("error"):
        return AgentNode.ERROR_HANDLER.value
    return next_pending_node(state)
