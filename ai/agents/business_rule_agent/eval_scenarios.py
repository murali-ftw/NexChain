"""Hardcoded known scenarios for the P3.10 completion gate — every scenario
asserts EXACT equality against a documented expected output, not a
threshold or fuzzy match. Covers: the flagship (Breached/GOLD), At-Risk at
both Medium and Low severity, On-Time, N/A (pre-dispatch), and each tier's
breach threshold boundary (at-threshold = still At Risk; one day over =
Breached).
"""

from __future__ import annotations

from datetime import date

from ai.agents.business_rule_agent.rules import RuleEngineInput, RuleEngineOutput
from ai.contracts import SLAStatus

SCENARIOS: list[dict[str, object]] = [
    {
        "label": "Flagship SO-45892 (frozen per CONTRACTS.md §9, as_of=revised ETA 2026-07-09)",
        "input": RuleEngineInput(
            order_no="SO-45892",
            sla_tier="GOLD",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 3),
            revised_delivery_date=date(2026, 7, 9),
            as_of_date=date(2026, 7, 9),
            shipment_status="Customs Hold",
            delay_reason="HS code mismatch during customs validation.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.BREACHED,
            delay_days=6,
            max_delay_days=5,
            severity="High",
            escalation_role="Logistics Manager",
            recommended_actions=[
                "Verify the HS code in the commercial invoice against product "
                "master data (Customs Hold SOP step 1).",
                "Send the corrected commercial invoice to the customs broker "
                "for re-validation (Customs Hold SOP step 3).",
                "Escalate to the Logistics Manager (Customs Hold SOP step 6 / Escalation Matrix).",
                "Notify the customer with the revised ETA per the Customer "
                "Notification Policy (Customs Hold SOP step 7).",
            ],
        ),
    },
    {
        "label": "At-Risk, Medium severity (>half of max_delay_days elapsed)",
        "input": RuleEngineInput(
            order_no="SO-90001",
            sla_tier="STANDARD",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 10),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 12),
            shipment_status="In Transit",
            delay_reason="Carrier running behind schedule.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.AT_RISK,
            delay_days=2,
            max_delay_days=3,
            severity="Medium",
            escalation_role="Logistics Coordinator",
            recommended_actions=[
                "Escalate to Logistics Coordinator for a proactive check-in "
                "per the Escalation Matrix (Medium severity)."
            ],
        ),
    },
    {
        "label": "At-Risk, Low severity (<=half of max_delay_days elapsed, no escalation)",
        "input": RuleEngineInput(
            order_no="SO-90002",
            sla_tier="STANDARD",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 10),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 11),
            shipment_status="In Transit",
            delay_reason="Carrier running behind schedule.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.AT_RISK,
            delay_days=1,
            max_delay_days=3,
            severity="Low",
            escalation_role=None,
            recommended_actions=[],
        ),
    },
    {
        "label": "On-Time (not yet past promised date)",
        "input": RuleEngineInput(
            order_no="SO-90003",
            sla_tier="PLATINUM",
            current_status="Dispatched",
            promised_delivery_date=date(2026, 7, 20),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 15),
            shipment_status="In Transit",
            delay_reason=None,
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.ON_TIME,
            delay_days=0,
            max_delay_days=7,
            severity="Low",
            escalation_role=None,
            recommended_actions=[],
        ),
    },
    {
        "label": "N/A (Pending — never dispatched)",
        "input": RuleEngineInput(
            order_no="SO-90004",
            sla_tier="GOLD",
            current_status="Pending",
            promised_delivery_date=date(2026, 7, 20),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 15),
            shipment_status=None,
            delay_reason=None,
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.NOT_APPLICABLE,
            delay_days=None,
            max_delay_days=5,
            severity="N/A",
            escalation_role=None,
            recommended_actions=[],
        ),
    },
    {
        "label": "STANDARD boundary: at threshold (delay_days == max_delay_days -> still At Risk)",
        "input": RuleEngineInput(
            order_no="SO-90005",
            sla_tier="STANDARD",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 10),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 13),
            shipment_status="In Transit",
            delay_reason="Carrier running behind schedule.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.AT_RISK,
            delay_days=3,
            max_delay_days=3,
            severity="Medium",
            escalation_role="Logistics Coordinator",
            recommended_actions=[
                "Escalate to Logistics Coordinator for a proactive check-in "
                "per the Escalation Matrix (Medium severity)."
            ],
        ),
    },
    {
        "label": "STANDARD boundary: one day over threshold -> Breached",
        "input": RuleEngineInput(
            order_no="SO-90006",
            sla_tier="STANDARD",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 10),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 14),
            shipment_status="In Transit",
            delay_reason="Carrier running behind schedule.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.BREACHED,
            delay_days=4,
            max_delay_days=3,
            severity="High",
            escalation_role="Logistics Coordinator",
            recommended_actions=[
                "Investigate root cause: In Transit (Escalation Matrix checklist item 4).",
                "Escalate to the Logistics Coordinator per the Escalation Matrix.",
                "Notify the customer with the revised ETA per the Customer Notification Policy.",
            ],
        ),
    },
    {
        "label": "GOLD boundary: at threshold (delay_days == max_delay_days -> still At Risk)",
        "input": RuleEngineInput(
            order_no="SO-90007",
            sla_tier="GOLD",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 3),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 8),
            shipment_status="In Transit",
            delay_reason="Carrier running behind schedule.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.AT_RISK,
            delay_days=5,
            max_delay_days=5,
            severity="Medium",
            escalation_role="Logistics Coordinator",
            recommended_actions=[
                "Escalate to Logistics Coordinator for a proactive check-in "
                "per the Escalation Matrix (Medium severity)."
            ],
        ),
    },
    {
        "label": "PLATINUM boundary: at threshold (delay_days == max_delay_days -> still At Risk)",
        "input": RuleEngineInput(
            order_no="SO-90008",
            sla_tier="PLATINUM",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 1),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 8),
            shipment_status="Warehouse Delay",
            delay_reason="Backordered SKU awaiting restock.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.AT_RISK,
            delay_days=7,
            max_delay_days=7,
            severity="Medium",
            escalation_role="Logistics Coordinator",
            recommended_actions=[
                "Escalate to Logistics Coordinator for a proactive check-in "
                "per the Escalation Matrix (Medium severity)."
            ],
        ),
    },
    {
        "label": "PLATINUM boundary: one day over threshold -> Breached + Critical severity",
        "input": RuleEngineInput(
            order_no="SO-90009",
            sla_tier="PLATINUM",
            current_status="Delayed",
            promised_delivery_date=date(2026, 7, 1),
            revised_delivery_date=None,
            as_of_date=date(2026, 7, 9),
            shipment_status="Warehouse Delay",
            delay_reason="Backordered SKU awaiting restock.",
        ),
        "expected": RuleEngineOutput(
            sla_status=SLAStatus.BREACHED,
            delay_days=8,
            max_delay_days=7,
            severity="Critical",
            escalation_role="Regional Operations Director",
            recommended_actions=[
                "Investigate root cause: Warehouse Delay (Escalation Matrix checklist item 4).",
                "Escalate to the Regional Operations Director per the Escalation Matrix.",
                "Notify the customer with the revised ETA per the Customer Notification Policy.",
            ],
        ),
    },
]
