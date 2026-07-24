"""P3.10 completion-gate evaluation.

Runs every hardcoded scenario (eval_scenarios.py) through the pure rule
engine (rules.evaluate) and asserts EXACT equality against the documented
expected output — no LLM calls, no live services needed.

Run from repo root:
    python -m ai.agents.business_rule_agent.eval

Gate (docs/team_plan.md P3.10): "known scenarios produce expected
deterministic outcomes" — any mismatch on any field is a FAIL.
"""

from __future__ import annotations

from typing import cast

from ai.agents.business_rule_agent.rules import RuleEngineInput, evaluate
from ai.agents.business_rule_agent.eval_scenarios import SCENARIOS


def run() -> tuple[int, int]:
    passed = 0
    for case in SCENARIOS:
        # SCENARIOS is dict[str, object] because each entry also mixes in a
        # plain str label — the cast narrows "input" back to its actual type.
        result = evaluate(cast(RuleEngineInput, case["input"]))
        expected = case["expected"]
        ok = result == expected
        print(f"\n[{case['label']}]")
        print(f"  expected: {expected}")
        print(f"  actual:   {result}")
        if not ok:
            for field_name in (
                "sla_status",
                "delay_days",
                "max_delay_days",
                "severity",
                "escalation_role",
                "recommended_actions",
            ):
                exp_val = getattr(expected, field_name)
                act_val = getattr(result, field_name)
                if exp_val != act_val:
                    print(
                        f"  MISMATCH {field_name}: expected={exp_val!r} actual={act_val!r}"
                    )
        print("  PASS" if ok else "  FAIL")
        if ok:
            passed += 1
    return passed, len(SCENARIOS)


if __name__ == "__main__":
    passed, total = run()
    print(f"\n{'=' * 60}")
    print(f"Scenario gate: {passed}/{total} exact-match.")
    print("GATE MET" if passed == total else "GATE NOT MET")
