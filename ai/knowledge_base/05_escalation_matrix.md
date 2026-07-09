# Escalation Matrix

## Purpose

Maps delay severity and SLA breach status to the responsible escalation
role and expected response time. This document is the single source of
truth for "who gets notified when" and must stay consistent with the
`escalation_role` values in the `sla_rules` table and the
[SLA Policy](./01_sla_policy.md). It is a reference matrix rather than a
step-by-step procedure — other SOPs perform the diagnosis and
remediation; this document only governs the notification and
ownership layer once a case needs to move up the chain.

## Scope and Applicability

Applies to every `sales_orders` row that reaches `At Risk` or `Breached`
SLA status, across all customer tiers and all delay causes (customs,
inventory, warehouse, carrier, or payment-adjacent). It also applies to
force-majeure-flagged orders for internal reporting purposes, though
the [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md)
suppresses the actual paging step for those cases.

## Definitions / Key Terms

- **Severity** — a four-level classification (Low, Medium, High,
  Critical) derived from SLA status and tier, distinct from SLA status
  itself; SLA status answers "is this order late," severity answers
  "how urgently does a human need to act."
- **Escalation role** — the named operational role (Logistics
  Coordinator, Logistics Manager, or Regional Operations Director)
  responsible for a given tier's breached orders, per `sla_rules`.
- **First response** — the expected time for the escalation role to
  acknowledge the case, not to fully resolve it; resolution time is
  governed by the relevant cause-specific SOP.

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

## Regional Escalation Contacts and Paging

Escalations route through the on-call paging tool during business
hours (08:00–20:00 local warehouse time) and to the after-hours duty
roster outside that window. The Regional Operations Director maintains
the current on-call roster for Logistics Coordinators and Logistics
Managers across all `warehouse` regions; the roster itself is not part
of this document since it changes weekly, but every escalation must be
paged to whoever is currently on-call for the fulfilling warehouse, not
to a fixed named individual.

## Escalation Content Checklist

Every escalation notification must include:
1. Order number (`order_no`) and customer name.
2. `promised_delivery_date` and current `revised_delivery_date`.
3. Delay in days and computed SLA status.
4. Root cause (`shipment.delay_reason` or inventory/warehouse/carrier
   cause) and the SOP being followed.
5. Next action owner and expected next update time.

## Escalation Communication Template

A minimal escalation page should read, in order: order number and
customer name; current SLA status and severity; root cause in one
sentence; the SOP being followed and its typical resolution time; and
the specific ask (e.g., "approve partial fulfillment," "confirm
customs broker submission received"). Escalation pages that omit the
specific ask are considered incomplete and should be re-sent with one
added — a page that only reports status without requesting a decision
or action does not move the case forward.

## Post-Escalation Review Process

Every `Critical` severity escalation, and any `High` severity case that
took longer than 2 business days to resolve after first response,
receives a brief post-incident note from the escalation role: what
happened, what resolved it, and whether a Prevention-track action item
(see the relevant cause-specific SOP) is warranted. These notes feed the
quarterly review referenced in the [SLA Policy](./01_sla_policy.md).

## Multi-Order Escalation (Batch Breach) Handling

When multiple orders from the same customer breach within a rolling
7-day window (the Critical-severity trigger above), escalate as a
single consolidated case rather than one page per order — this avoids
alert fatigue for the Regional Operations Director and gives a truer
picture of customer impact. The consolidated escalation lists every
affected `order_no` and its individual root cause.

## Worked Example — SO-45892

- SLA status: `Breached` (6-day delay vs. 5-day GOLD threshold)
- Severity: **High**
- Escalation role: **Logistics Manager**
- Root cause: Customs Hold, HS code mismatch (see
  [Customs Hold SOP](./03_customs_hold_sop.md))
- Expected first response: within 4 business hours of breach detection

## Exceptions and Edge Cases

- **Force majeure-flagged orders**: still computed and visible at their
  true severity internally, but standard paging is suppressed per the
  [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md).
- **Payment-hold orders**: excluded from severity/escalation
  calculation entirely while the SLA clock is paused, per the
  [Payment Hold SOP](./09_payment_hold_sop.md) — a payment hold is not
  an operational delay and should not page Logistics roles.

## Revision and Effective Date

Reviewed quarterly by the Regional Operations Director alongside the
[SLA Policy](./01_sla_policy.md); any change to tier thresholds or
escalation roles must update both documents in the same change window.

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
- [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md)
