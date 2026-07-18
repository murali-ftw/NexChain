"""P3.11 completion-gate evaluation — the structured CoPilotResponse Person 1
consumes, assembled end-to-end through the real compiled graph plus
ai_service/response_mapper.py::state_to_fields(). Complements
business_rule_agent/eval.py (pure rule engine only) and graph/eval.py
(routing/visitation only) by pinning the actual wire-shape fields a live run
produces, and by proving a failed agent path degrades gracefully instead of
crashing or silently mangling the shape.

Gate (docs/team_plan.md P3.11): "Person 1 can render the response without
parsing free-form prose" — every one of order_status, shipment_status,
delay_reason, delay_days, sla_status, recommended_actions, sources is a
first-class structured field, and a retry-exhausted agent still returns a
well-formed CoPilotResponse (partial=True, error set), never an exception.

Run from repo root:
    python -m ai.graph.eval_final_response
"""

from __future__ import annotations

from unittest.mock import patch

from ai.contracts import CoPilotState, SLAStatus
from ai.graph.graph import build_graph
from ai.llm_client import LLMProviderError
from ai_service.response_mapper import state_to_fields
from ai_service.tools.errors import ToolUnavailable

FLAGSHIP_QUERY = (
    "Where is customer order SO-45892? Why is it delayed and what action should we take?"
)

EXPECTED_FLAGSHIP = {
    "order_status": "Delayed",
    "shipment_status": "Customs Hold",
    "current_location": "Chennai Port",
    "delay_reason": "HS code mismatch during customs validation.",
    "delay_days": 6,
    "sla_status": SLAStatus.BREACHED,
    "recommended_actions": [
        "Verify the HS code in the commercial invoice against product master data (Customs Hold SOP step 1).",
        "Send the corrected commercial invoice to the customs broker for re-validation (Customs Hold SOP step 3).",
        "Escalate to the Logistics Manager (Customs Hold SOP step 6 / Escalation Matrix).",
        "Notify the customer with the revised ETA per the Customer Notification Policy (Customs Hold SOP step 7).",
    ],
    "partial": False,
    "error": None,
}


def _initial_state(query: str) -> CoPilotState:
    return {
        "session_id": "eval-session",
        "user_id": "eval-user",
        "raw_query": query,
        "intent": "",
        "sub_intents": [],
        "kb_result": None,
        "sql_result": None,
        "api_result": None,
        "rule_result": None,
        "retry_count": {},
        "final_response": None,
        "error": None,
    }


def run_flagship_case() -> bool:
    print(f"\n[flagship structured response] Q: {FLAGSHIP_QUERY}")
    graph = build_graph()
    final_state = graph.invoke(_initial_state(FLAGSHIP_QUERY))
    fields = state_to_fields(final_state)

    failures = []
    for key, expected in EXPECTED_FLAGSHIP.items():
        actual = fields.get(key)
        if actual != expected:
            failures.append(f"{key}: expected {expected!r}, got {actual!r}")

    ok = not failures
    print(f"  promised_delivery_date={fields.get('promised_delivery_date')!r} "
          f"revised_delivery_date={fields.get('revised_delivery_date')!r}")
    print(f"  sources: {len(fields.get('sources') or [])} citation(s)")
    print("  PASS" if ok else f"  FAIL ({'; '.join(failures)})")
    return ok


# Each entry forces one data-gathering node's wrapped call to fail past its
# one retry (ai/contracts.py MAX_RETRIES_PER_NODE=1) via the same
# call_with_retry mechanism business_rule_agent/get_order already proved.
# Only business_rule_agent's own failure (get_order) is expected to zero out
# recommended_actions — a KB or SQL failure doesn't touch business_rule_agent's
# output at all, and an api_status_agent failure only drops delay_reason (so
# rules.py falls back to its generic action list, not an empty one) — so
# beyond the shared partial/error/answer_text checks, each case only asserts
# what its own failure actually changes.
FALLBACK_CASES = [
    {
        "label": "business_rule_agent (get_order)",
        "patch_target": "ai.graph.nodes.get_order",
        "exception": ToolUnavailable("get_order", "simulated: DB unavailable"),
        "expect_no_recommended_actions": True,
    },
    {
        "label": "knowledge_base_agent (answer_policy_question)",
        "patch_target": "ai.graph.nodes.answer_policy_question",
        "exception": LLMProviderError("simulated: LLM unavailable"),
        "expect_no_recommended_actions": False,
    },
    {
        "label": "text_to_sql_agent (generate_sql)",
        "patch_target": "ai.graph.nodes.generate_sql",
        "exception": LLMProviderError("simulated: LLM unavailable"),
        "expect_no_recommended_actions": False,
    },
    {
        "label": "api_status_agent (get_shipment_status)",
        "patch_target": "ai.graph.nodes.get_shipment_status",
        "exception": ToolUnavailable("get_shipment_status", "simulated: carrier API unavailable"),
        "expect_no_recommended_actions": False,
    },
]


def run_fallback_case(case: dict) -> bool:
    """Confirm the mapped response degrades to a well-formed CoPilotResponse
    — partial=True, an error message, non-empty prose, no exception —
    instead of crashing when case['patch_target'] fails past its retry."""
    print(f"\n[fallback] {case['label']}: retry exhausted")
    graph = build_graph()
    with patch(case["patch_target"], side_effect=case["exception"]):
        final_state = graph.invoke(_initial_state(FLAGSHIP_QUERY))
    fields = state_to_fields(final_state)

    failures = []
    if fields.get("partial") is not True:
        failures.append(f"partial: expected True, got {fields.get('partial')!r}")
    if not fields.get("error"):
        failures.append("error: expected a message, got none")
    if not fields.get("answer_text"):
        failures.append("answer_text: expected non-empty prose even in the degraded case")
    if case["expect_no_recommended_actions"] and fields.get("recommended_actions") != []:
        failures.append(
            f"recommended_actions: expected [] fallback, got {fields.get('recommended_actions')!r}"
        )

    ok = not failures
    print(f"  partial={fields.get('partial')} error={fields.get('error')!r}")
    print(f"  recommended_actions={fields.get('recommended_actions')!r}")
    print("  PASS" if ok else f"  FAIL ({'; '.join(failures)})")
    return ok


if __name__ == "__main__":
    flagship_ok = run_flagship_case()
    fallback_results = [run_fallback_case(case) for case in FALLBACK_CASES]

    print(f"\n{'=' * 60}")
    print(f"Flagship structured-response case: {'PASS' if flagship_ok else 'FAIL'}")
    for case, ok in zip(FALLBACK_CASES, fallback_results):
        print(f"Fallback ({case['label']}): {'PASS' if ok else 'FAIL'}")
    print("GATE MET" if flagship_ok and all(fallback_results) else "GATE NOT MET")
