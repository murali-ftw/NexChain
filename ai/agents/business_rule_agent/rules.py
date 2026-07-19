"""P3.10 pure rule engine — SLA breach detection, delay calculation,
escalation level, and corrective-action selection.

Deterministic Python only: no LLM calls, no I/O. `evaluate()` is a pure
function of `RuleEngineInput` — callers (the graph node) own fetching the
real order/shipment data and passing `as_of_date` explicitly; this module
never reads the system clock itself, so the same input always produces
the same output.

Source of truth for every threshold/role below: `ai/knowledge_base/01_sla_policy.md`
(tiers, breach formula) and `ai/knowledge_base/05_escalation_matrix.md`
(severity levels, severity-based vs. tier-based escalation roles).
`docs/06_backend_schema.md` §6 has the canonical breach SQL this mirrors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import cast

from ai.contracts import SLAStatus

# 01_sla_policy.md "SLA Tiers" table. Not in ai/contracts.py — that file
# only defines the SLAStatus *result* enum, not these input thresholds.
TIER_RULES: dict[str, dict[str, object]] = {
    "STANDARD": {"max_delay_days": 3, "escalation_role": "Logistics Coordinator"},
    "GOLD": {"max_delay_days": 5, "escalation_role": "Logistics Manager"},
    "PLATINUM": {
        "max_delay_days": 7,
        "escalation_role": "Regional Operations Director",
    },
}

# 01_sla_policy.md "Scope and Applicability": pre-dispatch / never-dispatched
# orders are N/A regardless of dates.
NON_DISPATCHED_STATUSES: frozenset[str] = frozenset({"Pending", "Cancelled"})


@dataclass(frozen=True)
class RuleEngineInput:
    order_no: str | None
    sla_tier: str | None
    current_status: str | None
    promised_delivery_date: date | None
    revised_delivery_date: date | None
    as_of_date: date
    shipment_status: str | None
    delay_reason: str | None


@dataclass(frozen=True)
class RuleEngineOutput:
    sla_status: SLAStatus
    delay_days: int | None
    max_delay_days: int | None
    severity: str
    escalation_role: str | None
    recommended_actions: list[str] = field(default_factory=list)


def compute_delay_days(promised_delivery_date: date, as_of_date: date) -> int:
    """01_sla_policy.md Definitions: "Delay days — CURRENT_DATE -
    promised_delivery_date, computed only when that value is positive" —
    clamped to zero for an order not yet past its promised date."""
    return max((as_of_date - promised_delivery_date).days, 0)


def sla_status(
    delay_days: int | None, max_delay_days: int | None, current_status: str | None
) -> SLAStatus:
    """docs/06_backend_schema.md §6 breach formula, plus the N/A carve-out
    for pre-dispatch/cancelled orders (01_sla_policy.md Scope)."""
    if current_status in NON_DISPATCHED_STATUSES:
        return SLAStatus.NOT_APPLICABLE
    if delay_days is None or max_delay_days is None:
        return SLAStatus.NOT_APPLICABLE
    if delay_days > max_delay_days:
        return SLAStatus.BREACHED
    if delay_days > 0:
        return SLAStatus.AT_RISK
    return SLAStatus.ON_TIME


def severity(
    status: SLAStatus,
    delay_days: int | None,
    max_delay_days: int | None,
    tier: str | None,
) -> str:
    """05_escalation_matrix.md "Severity Levels": Low/Medium/High/Critical.
    Critical requires Breached + PLATINUM (single-order case only — the
    matrix's other Critical trigger, multiple breached orders for the same
    customer in a rolling 7-day window, needs cross-order data this
    per-order engine doesn't have; not implemented, flagged as a known
    limitation, not silently approximated)."""
    if status == SLAStatus.NOT_APPLICABLE:
        return "N/A"
    if status == SLAStatus.ON_TIME:
        return "Low"
    if status == SLAStatus.BREACHED:
        return "Critical" if tier == "PLATINUM" else "High"
    # AT_RISK: Medium once more than half the tier's max_delay_days has elapsed.
    if max_delay_days and delay_days is not None and delay_days > max_delay_days / 2:
        return "Medium"
    return "Low"


def escalation_role(status: SLAStatus, sev: str, tier: str | None) -> str | None:
    """05_escalation_matrix.md "Escalation Role by Severity": Medium
    severity always routes to Logistics Coordinator regardless of tier —
    only High/Critical (Breached) use the tier-based role from
    "Escalation Role by SLA Tier". Low/N/A get no escalation."""
    if sev == "Medium":
        return "Logistics Coordinator"
    if sev in ("High", "Critical"):
        rule = TIER_RULES.get(tier or "")
        return cast("str | None", rule["escalation_role"]) if rule else None
    return None


def corrective_actions(
    status: SLAStatus,
    sev: str,
    shipment_status: str | None,
    delay_reason: str | None,
    role: str | None,
) -> list[str]:
    """Ordered action list. The Customs Hold / HS-code-mismatch sequence is
    the flagship's exact path (03_customs_hold_sop.md Resolution Steps
    1/3/6/7 — the customer/operator-facing subset, excluding internal
    tracking-only steps 2/4/5). Other Breached causes fall back to the
    generic Escalation Matrix checklist (root cause, escalate, notify) since
    only the Customs Hold SOP's action sequence was in scope for Day 10."""
    if status in (SLAStatus.ON_TIME, SLAStatus.NOT_APPLICABLE):
        return []
    if status == SLAStatus.AT_RISK:
        if sev == "Medium":
            return [
                f"Escalate to {role} for a proactive check-in per the "
                "Escalation Matrix (Medium severity)."
            ]
        return []  # Low severity: automated monitoring only, no escalation.

    # BREACHED
    cause = (shipment_status or "").strip().lower()
    reason = (delay_reason or "").lower()
    if cause == "customs hold" and "hs code" in reason:
        return [
            "Verify the HS code in the commercial invoice against product "
            "master data (Customs Hold SOP step 1).",
            "Send the corrected commercial invoice to the customs broker "
            "for re-validation (Customs Hold SOP step 3).",
            f"Escalate to the {role} (Customs Hold SOP step 6 / Escalation Matrix).",
            "Notify the customer with the revised ETA per the Customer "
            "Notification Policy (Customs Hold SOP step 7).",
        ]
    return [
        f"Investigate root cause: {shipment_status or delay_reason or 'unspecified'} "
        "(Escalation Matrix checklist item 4).",
        f"Escalate to the {role} per the Escalation Matrix.",
        "Notify the customer with the revised ETA per the Customer Notification Policy.",
    ]


def evaluate(inp: RuleEngineInput) -> RuleEngineOutput:
    if (
        inp.current_status in NON_DISPATCHED_STATUSES
        or inp.promised_delivery_date is None
    ):
        delay_days = None
    else:
        delay_days = compute_delay_days(inp.promised_delivery_date, inp.as_of_date)

    # TIER_RULES values are dict[str, object] because each entry mixes an int
    # (max_delay_days) and a str (escalation_role) — the cast narrows what's a
    # hardcoded, always-int literal back for callers that need int | None.
    max_dd = cast(
        "int | None", TIER_RULES.get(inp.sla_tier or "", {}).get("max_delay_days")
    )
    status = sla_status(delay_days, max_dd, inp.current_status)
    sev = severity(status, delay_days, max_dd, inp.sla_tier)
    role = escalation_role(status, sev, inp.sla_tier)
    actions = corrective_actions(
        status, sev, inp.shipment_status, inp.delay_reason, role
    )

    return RuleEngineOutput(
        sla_status=status,
        delay_days=delay_days,
        max_delay_days=max_dd,
        severity=sev,
        escalation_role=role,
        recommended_actions=actions,
    )
