"""P3.8 supervisor node — classifies the query; routing lives in routing.py.

Populates CoPilotState.intent / sub_intents by calling the existing P3.7
classifier (ai/agents/intent_classifier/classifier.py) and never
reinterprets its decision — INTENT_TO_ROUTING (ai/contracts.py) is the
only source of truth for which node(s) a query reaches.
"""

from __future__ import annotations

from ai.agents.intent_classifier.classifier import classify
from ai.graph.state import CoPilotState


def supervisor_node(state: CoPilotState) -> CoPilotState:
    """Classify state['raw_query'] and record intent + sub_intents.

    Routing itself happens in routing.route_after_supervisor, not here —
    this node only decides *what* the query is, not *where* it goes.
    """
    result = classify(state["raw_query"])
    if result.routing_category is None:
        return {
            "intent": result.intent or "",
            "sub_intents": result.sub_intents,
            "error": result.error or "intent classification failed",
        }
    return {
        "intent": result.intent or "",
        "sub_intents": result.sub_intents,
        "error": None,
    }
