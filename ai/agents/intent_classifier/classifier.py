
"""P3.7 Intent Classifier.

Hybrid: a deterministic keyword/pattern fast path (rules.py, zero API
calls) tries first; only ambiguous queries fall through to one LLM
classification call. Output always conforms to the frozen contract
(ai/contracts.py) — the RoutingCategory is looked up via the existing
INTENT_TO_ROUTING mapping, never independently guessed, so it can never
drift from that frozen dict.

Standalone: this module only DECIDES the route. Wiring the decision
into the LangGraph graph (CoPilotState, conditional edges, invoking
knowledge_base_agent/text_to_sql_agent/api_status_agent) is P3.8, not
this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.agents.intent_classifier.prompts import build_prompt
from ai.agents.intent_classifier.rules import classify_by_rules
from ai.contracts import INTENT_TO_ROUTING, BusinessIntent, RoutingCategory
from ai.llm_client import LLMConfigError, LLMProviderError, generate

# How a compound BusinessIntent decomposes into single-source intents,
# so downstream fan-out (P3.8/P3.9) knows which agents to invoke.
_SUB_INTENTS: dict[BusinessIntent, list[str]] = {
    BusinessIntent.SLA_CHECK: [
        BusinessIntent.ORDER_STATUS.value,
        BusinessIntent.SHIPMENT_STATUS.value,
    ],
    BusinessIntent.DELAY_ANALYSIS: [
        BusinessIntent.ORDER_STATUS.value,
        BusinessIntent.SHIPMENT_STATUS.value,
        BusinessIntent.SOP_LOOKUP.value,
    ],
}

_VALID_CATEGORY_VALUES = {c.value for c in RoutingCategory}

# The LLM fallback (prompts.py) only disambiguates at the RoutingCategory
# level, not the finer BusinessIntent level (that's what it's asked for).
# When it resolves a query, `intent` is filled with a representative
# BusinessIntent for that category, so CoPilotState.intent always carries
# a value — but `routing_category` (the actual routing decision) is
# always exactly what the LLM said, never reinterpreted.
_CATEGORY_TO_INTENT: dict[RoutingCategory, BusinessIntent] = {
    RoutingCategory.KNOWLEDGE_QUERY: BusinessIntent.SOP_LOOKUP,
    RoutingCategory.API_QUERY: BusinessIntent.SHIPMENT_STATUS,
    RoutingCategory.DATABASE_QUERY: BusinessIntent.REPORT,
    RoutingCategory.MULTI_TOOL_QUERY: BusinessIntent.DELAY_ANALYSIS,
}


@dataclass
class IntentResult:
    intent: str | None
    routing_category: RoutingCategory | None
    sub_intents: list[str] = field(default_factory=list)
    resolved_by: str = "rules"  # "rules" | "llm"
    error: str | None = None


def _to_result(intent: BusinessIntent, resolved_by: str) -> IntentResult:
    return IntentResult(
        intent=intent.value,
        routing_category=INTENT_TO_ROUTING[intent],
        sub_intents=_SUB_INTENTS.get(intent, []),
        resolved_by=resolved_by,
    )


def classify(query: str) -> IntentResult:
    """Classify a natural-language question into the frozen routing contract.

    Tries the zero-cost rule fast-path first; only calls the LLM for
    genuinely ambiguous queries. Abstains explicitly (routing_category is
    None, `error` set) rather than guessing a category, if the LLM call
    fails or returns something outside the frozen enum — matching the
    KB/SQL agents' existing "fail honestly, don't fabricate" convention.
    """
    rule_intent = classify_by_rules(query)
    if rule_intent is not None:
        return _to_result(rule_intent, resolved_by="rules")

    try:
        raw = generate(build_prompt(query))
    except (LLMConfigError, LLMProviderError) as exc:
        return IntentResult(
            intent=None,
            routing_category=None,
            resolved_by="llm",
            error=f"LLM classification failed: {exc}",
        )

    category_value = raw.strip().upper()
    if category_value not in _VALID_CATEGORY_VALUES:
        return IntentResult(
            intent=None,
            routing_category=None,
            resolved_by="llm",
            error=f"LLM returned an unrecognized category: {raw!r}",
        )

    category = RoutingCategory(category_value)
    intent = _CATEGORY_TO_INTENT[category]
    return _to_result(intent, resolved_by="llm")
