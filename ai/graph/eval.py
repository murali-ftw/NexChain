"""P3.8 completion-gate evaluation.

Runs one representative question per routing path through the compiled
graph and reports, per question, the exact node execution sequence
(via graph.stream(..., stream_mode="updates")) against the nodes the
question is expected to reach.

Run from repo root:
    python -m ai.graph.eval

Gate (docs/team_plan.md P3.8): "Knowledge, database, and API questions
each reach the correct path."
"""

from __future__ import annotations

from unittest.mock import patch

from ai.agents.intent_classifier.classifier import IntentResult
from ai.contracts import CoPilotState
from ai.graph.graph import build_graph

CASES = [
    {
        "label": "KNOWLEDGE_QUERY",
        "query": "What is our SLA policy for customs holds?",
        "must_visit": {"knowledge_base_agent"},
    },
    {
        "label": "DATABASE_QUERY",
        "query": "What is the status of order SO-10001?",
        "must_visit": {"text_to_sql_agent"},
    },
    {
        "label": "API_QUERY",
        "query": "Where is shipment TRK-10001-1 right now?",
        "must_visit": {"api_status_agent"},
    },
    {
        "label": "MULTI_TOOL_QUERY (flagship)",
        "query": (
            "Where is customer order SO-45892? Why is it delayed and "
            "what action should we take?"
        ),
        "must_visit": {"text_to_sql_agent", "api_status_agent", "knowledge_base_agent"},
    },
]


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


def _run(graph, query: str) -> tuple[list[str], CoPilotState]:
    path: list[str] = []
    final_state: CoPilotState = _initial_state(query)
    for update in graph.stream(_initial_state(query), stream_mode="updates"):
        for node, partial in update.items():
            path.append(node)
            final_state.update(partial)
    return path, final_state


def run_path_cases() -> tuple[int, int]:
    graph = build_graph()
    passed = 0
    for case in CASES:
        print(f"\n[{case['label']}] Q: {case['query']}")
        path, state = _run(graph, case["query"])
        print(f"  path: {' -> '.join(path)}")
        print(f"  intent={state.get('intent')} sub_intents={state.get('sub_intents')}")
        print(f"  retry_count={state.get('retry_count')}")
        ok = case["must_visit"].issubset(set(path))
        print("  PASS" if ok else f"  FAIL (missing {case['must_visit'] - set(path)})")
        if ok:
            passed += 1
    return passed, len(CASES)


def run_error_handler_case() -> bool:
    """Force classify() to fail to resolve a routing_category (no live LLM
    call needed) and confirm the graph routes to error_handler."""
    print("\n[error_handler] simulated total classification failure")
    graph = build_graph()
    with patch(
        "ai.graph.supervisor.classify",
        return_value=IntentResult(
            intent=None, routing_category=None, error="simulated: unrecognized category"
        ),
    ):
        path, state = _run(graph, "gibberish query for testing")
    print(f"  path: {' -> '.join(path)}")
    print(f"  error={state.get('error')} final_response={state.get('final_response')!r}")
    ok = path == ["intent_classifier", "error_handler", "final_response_agent"]
    print("  PASS" if ok else "  FAIL")
    return ok


if __name__ == "__main__":
    passed, total = run_path_cases()
    error_handler_ok = run_error_handler_case()

    print(f"\n{'=' * 60}")
    print(f"Path gate: {passed}/{total} required-node-visit checks passed.")
    print(f"error_handler routing: {'PASS' if error_handler_ok else 'FAIL'}")
    print("GATE MET" if passed == total and error_handler_ok else "GATE NOT MET")
