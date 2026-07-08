# Escalation Matrix

## Purpose

Maps delay severity and SLA breach status to the responsible escalation
role and expected response time. This document is the single source of
truth for "who gets notified when" and must stay consistent with the
`escalation_role` values in the `sla_rules` table and the
[SLA Policy](./01_sla_policy.md).

## Severity Levels

| Severity | Definition |
|---|---|
| Low | Order is `On Time`, or `At Risk` with fewer than half the tier's `max_delay_days` elapsed. No customer-visible risk yet. |
| Medium | Order is `At Risk`, more than half the tier's `max_delay_days` elapsed but not yet breached. |
| High | Order is `Breached` per SLA Policy calculation. |
| Critical | Order is `Breached` **and** affects a PLATINUM-tier customer, or `Breached` for multiple orders from the same customer within a rolling 7-day window. |

## Escalation Role by SLA Tier (from `sla_rules`)

| SLA Tier | max_delay_days | Escalation Role (on Breach) |
|---|---|---|
| STANDARD | 3 days | Logistics Coordinator |
| GOLD | 5 days | Logistics Manager |
| PLATINUM | 7 days | Regional Operations Director |

## Escalation Role by Severity (cross-cutting, applies regardless of tier)

| Severity | Escalation Role | Expected First Response |
|---|---|---|
| Low | No escalation — handled by automated monitoring | N/A |
| Medium | Logistics Coordinator (proactive check-in) | Within 1 business day |
| High (Breached) | Escalation role per tier table above | Within 4 business hours |
| Critical | Escalation role per tier table above, **plus** cc to Regional Operations Director | Within 1 business hour |

## Escalation Content Checklist

Every escalation notification must include:
1. Order number (`order_no`) and customer name.
2. `promised_delivery_date` and current `revised_delivery_date`.
3. Delay in days and computed SLA status.
4. Root cause (`shipment.delay_reason` or inventory/warehouse/carrier
   cause) and the SOP being followed.
5. Next action owner and expected next update time.

## Worked Example — SO-45892

- SLA status: `Breached` (6-day delay vs. 5-day GOLD threshold)
- Severity: **High**
- Escalation role: **Logistics Manager**
- Root cause: Customs Hold, HS code mismatch (see
  [Customs Hold SOP](./03_customs_hold_sop.md))
- Expected first response: within 4 business hours of breach detection

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
