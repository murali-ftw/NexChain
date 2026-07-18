"""P3.8 supervisor node — classifies the query; routing lives in routing.py.

Populates CoPilotState.intent / sub_intents by calling the existing P3.7
classifier (ai/agents/intent_classifier/classifier.py) and never
reinterprets its decision — INTENT_TO_ROUTING (ai/contracts.py) is the
only source of truth for which node(s) a query reaches.
"""

from __future__ import annotations

from ai.agents.intent_classifier.classifier import classify
from ai.contracts import AgentNode
from ai.graph.retry import call_with_retry
from ai.graph.state import CoPilotState


def supervisor_node(state: CoPilotState) -> CoPilotState:
    """Classify state['raw_query'] and record intent + sub_intents.

    Routing itself happens in routing.route_after_supervisor, not here —
    this node only decides *what* the query is, not *where* it goes.

    Wrapped in call_with_retry for consistency with every other node's
    MAX_RETRIES_PER_NODE budget — though classify() itself already catches
    LLMConfigError/LLMProviderError internally and returns an IntentResult
    rather than raising, so this doesn't yet cause a second attempt; it's
    here so classify() gets the same retry budget the moment it raises
    instead of swallowing a transient failure.
    """
    node = AgentNode.INTENT_CLASSIFIER.value
    retry_count = dict(state.get("retry_count") or {})
    attempts_before = retry_count.get(node, 0)

    result, _, attempts = call_with_retry(
        attempts_before, lambda: classify(state["raw_query"])
    )
    retry_count[node] = attempts
    assert result is not None  # classify() doesn't raise; call_with_retry always returns it

    if result.routing_category is None:
        return {
            "intent": result.intent or "",
            "sub_intents": result.sub_intents,
            "error": result.error or "intent classification failed",
            "retry_count": retry_count,
        }
    return {
        "intent": result.intent or "",
        "sub_intents": result.sub_intents,
        "error": None,
        "retry_count": retry_count,
    }
