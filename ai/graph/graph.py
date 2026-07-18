"""P3.8 graph assembly — supervisor + conditional routing + all 7 nodes.

MULTI_TOOL_QUERY sequences its required branches (text_to_sql_agent,
api_status_agent, knowledge_base_agent) one per graph step rather than
running them in parallel — see ai/graph/routing.py for why the frozen,
non-Annotated CoPilotState makes that the safe choice.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ai.contracts import AgentNode
from ai.graph.nodes import (
    api_status_agent_node,
    business_rule_agent_node,
    error_handler_node,
    final_response_agent_node,
    knowledge_base_agent_node,
    text_to_sql_agent_node,
)
from ai.graph.routing import (
    ALL_ROUTE_TARGETS,
    next_pending_node,
    route_after_supervisor,
)
from ai.graph.state import CoPilotState
from ai.graph.supervisor import supervisor_node

_BRANCH_NODES = (
    AgentNode.KNOWLEDGE_BASE_AGENT,
    AgentNode.TEXT_TO_SQL_AGENT,
    AgentNode.API_STATUS_AGENT,
)

_BRANCH_NODE_FN = {
    AgentNode.KNOWLEDGE_BASE_AGENT.value: knowledge_base_agent_node,
    AgentNode.TEXT_TO_SQL_AGENT.value: text_to_sql_agent_node,
    AgentNode.API_STATUS_AGENT.value: api_status_agent_node,
}

_ROUTE_PATH_MAP = {target: target for target in ALL_ROUTE_TARGETS}


def build_graph():
    graph = StateGraph(CoPilotState)
    graph.add_node(AgentNode.INTENT_CLASSIFIER.value, supervisor_node)
    for node in _BRANCH_NODES:
        graph.add_node(node.value, _BRANCH_NODE_FN[node.value])
    graph.add_node(AgentNode.BUSINESS_RULE_AGENT.value, business_rule_agent_node)
    graph.add_node(AgentNode.FINAL_RESPONSE_AGENT.value, final_response_agent_node)
    graph.add_node(AgentNode.ERROR_HANDLER.value, error_handler_node)

    graph.add_edge(START, AgentNode.INTENT_CLASSIFIER.value)
    graph.add_conditional_edges(
        AgentNode.INTENT_CLASSIFIER.value, route_after_supervisor, _ROUTE_PATH_MAP
    )
    # Each branch, once done (success or a recorded per-branch failure),
    # routes to the next still-pending required branch, or on to
    # business_rule_agent once none remain — same path function the
    # supervisor uses, since "what's left" only depends on state.
    for node in _BRANCH_NODES:
        graph.add_conditional_edges(node.value, next_pending_node, _ROUTE_PATH_MAP)

    graph.add_edge(
        AgentNode.BUSINESS_RULE_AGENT.value, AgentNode.FINAL_RESPONSE_AGENT.value
    )
    graph.add_edge(AgentNode.ERROR_HANDLER.value, AgentNode.FINAL_RESPONSE_AGENT.value)
    graph.add_edge(AgentNode.FINAL_RESPONSE_AGENT.value, END)

    return graph.compile()
