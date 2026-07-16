"""P3.8 completion-gate evaluation.

Runs one representative question per routing path through the compiled
graph and reports, per question, the exact node execution sequence
(via graph.stream(..., stream_mode="updates")) against the nodes the
question is expected to reach — AND, for each of those nodes, whether
its result actually succeeded (no {"error": ...}), not merely that the
node ran. A node can be visited and still silently fail (bad creds, a
downstream service being down, etc.); visitation alone proved routing,
not data. This gate now requires both.

Run from repo root:
    python -m ai.graph.eval

Gate (docs/team_plan.md P3.8): "Knowledge, database, and API questions
each reach the correct path." (P3.9 flagship: all three sources actually
land real data in state, not just get visited.)
"""

from __future__ import annotations

from unittest.mock import patch

from ai.agents.intent_classifier.classifier import IntentResult
from ai.contracts import CoPilotState
from ai.graph.graph import build_graph

# Which state field each data-gathering node writes its result to.
NODE_RESULT_FIELD = {
    "text_to_sql_agent": "sql_result",
    "api_status_agent": "api_result",
    "knowledge_base_agent": "kb_result",
}

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
        "query": "Where is shipment TRK-30001-1 right now?",
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


def _node_succeeded(state: CoPilotState, node: str) -> tuple[bool, str]:
    """True if `node`'s result field is a real payload, not an
    {"error": ...} value. Returns (ok, detail) — detail is the error
    message on failure, or empty on success."""
    field = NODE_RESULT_FIELD[node]
    result = state.get(field)
    if not result:
        return False, f"{field} is empty/None"
    if isinstance(result, dict) and result.get("error"):
        return False, f"{field} error: {result['error']}"
    if isinstance(result, dict) and result.get("abstained"):
        # The KB agent ran without error but explicitly found no evidence
        # (ai/agents/knowledge_base_agent/agent.py) — visitation without a
        # real answer, the same "ran but didn't succeed" case this gate
        # closes for errors.
        return False, f"{field} abstained: no evidence found"
    return True, ""


def run_path_cases() -> tuple[int, int]:
    graph = build_graph()
    passed = 0
    for case in CASES:
        print(f"\n[{case['label']}] Q: {case['query']}")
        path, state = _run(graph, case["query"])
        print(f"  path: {' -> '.join(path)}")
        print(f"  intent={state.get('intent')} sub_intents={state.get('sub_intents')}")
        print(f"  retry_count={state.get('retry_count')}")

        visited_ok = case["must_visit"].issubset(set(path))
        failures = []
        if not visited_ok:
            failures.append(f"not visited: {case['must_visit'] - set(path)}")

        for node in sorted(case["must_visit"]):
            succeeded, detail = _node_succeeded(state, node)
            status = "ok" if succeeded else f"FAILED ({detail})"
            print(f"  {node} -> {NODE_RESULT_FIELD[node]}: {status}")
            if not succeeded:
                failures.append(f"{node} did not succeed: {detail}")

        ok = not failures
        print("  PASS" if ok else f"  FAIL ({'; '.join(failures)})")
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
    print(f"Path gate: {passed}/{total} cases passed (correct routing AND real data, not just visitation).")
    print(f"error_handler routing: {'PASS' if error_handler_ok else 'FAIL'}")
    print("GATE MET" if passed == total and error_handler_ok else "GATE NOT MET")
