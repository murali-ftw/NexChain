# Customer Notification Policy

## Purpose

Defines when and how customers are notified about order delays, SLA
breaches, and resolutions, so that communication is consistent across
support agents, the Co-Pilot, and automated systems. Consistency matters
here specifically because delay causes are frequently technical (an HS
code mismatch, a warehouse QC hold, a carrier mis-route) and must be
translated into plain, non-alarming customer language without losing
accuracy.

## Scope and Applicability

Applies to every customer-facing communication triggered by a change in
`sales_orders.current_status`, `shipment.shipment_status`, or computed
SLA status, across all tiers and all delay causes. It governs tone and
timing, not the underlying diagnosis or remediation — those come from
the relevant cause-specific SOP (Customs Hold, Inventory Shortage,
Warehouse Delay, Carrier Delay, Payment Hold). It does not cover
marketing or account-management communication, only operational status
updates.

## Definitions / Key Terms

- **Proactive notification** — a message sent before the customer asks,
  triggered by an SLA status change.
- **Reactive notification** — a response to an inbound customer
  inquiry; must still follow the same content and tone rules as
  proactive notifications.
- **Escalation contact** — the named role (not necessarily a named
  individual) responsible for a `Breached` case, per the
  [Escalation Matrix](./05_escalation_matrix.md).

## Roles and Responsibilities

- **Customer Support Agent** — sends the majority of notifications
  using the templates and timing below.
- **Logistics Manager / Regional Operations Director** — approves
  messaging for `Breached` and `Critical` severity cases before it goes
  out, per the [Escalation Matrix](./05_escalation_matrix.md).
- **Account Management** — must be consulted before any compensating
  action (fee waiver, credit) is promised to the customer.

## When to Notify

| Trigger | Notify? | Timing |
|---|---|---|
| Order dispatched on schedule | No proactive notification required | N/A |
| SLA status becomes `At Risk` | Yes, for GOLD and PLATINUM tiers | Within 1 business day of detection |
| SLA status becomes `At Risk` | Optional for STANDARD tier | Only if customer has an open inquiry |
| SLA status becomes `Breached` | Yes, all tiers | Within 4 business hours of detection |
| Delay cause changes materially (e.g. new revised ETA) | Yes, all tiers | Within 1 business day |
| Issue resolved / order delivered | Yes, all tiers | Within 1 business day of resolution |

## What to Include

Every delay or breach notification must include, in plain language:
1. Order number and a one-line status summary.
2. The reason for the delay (translate internal SOP language into
   customer-facing terms — e.g. "a customs paperwork correction is in
   progress" rather than "HS code mismatch during customs validation").
3. The current best-estimate revised delivery date.
4. What NexChain is doing about it (reference the relevant SOP action,
   not the SOP name itself).
5. For `Breached` status: an apology, and the name/role of the
   escalation contact now managing the case (see
   [Escalation Matrix](./05_escalation_matrix.md)).

## Translation Reference: Internal Cause to Customer-Facing Language

| Internal cause (SOP language) | Customer-facing phrasing |
|---|---|
| HS code mismatch during customs validation | A customs paperwork correction is in progress |
| Inventory shortfall / replenishment triggered | We're securing additional stock to complete your order |
| Warehouse QC hold | A quality check is being completed before your order ships |
| Carrier mis-route or capacity delay | Your shipment is experiencing a carrier network delay |
| Payment hold | We're finalizing your payment before dispatch |

Never state the SOP name itself (e.g. "Customs Hold SOP") to a
customer — it is internal terminology and adds no value to the message.

## Channel and Tone

- Default channel: the contact email on file (`customers.contact_email`).
  Use `contact_phone` for Critical-severity escalations if email has not
  been acknowledged within the expected response window.
- Tone: factual, non-defensive, and specific. Avoid vague language like
  "delays beyond our control" without stating the actual cause.
- Never expose internal system identifiers (SKUs, warehouse codes,
  internal ticket IDs) unless the customer specifically asks for them.

## SLA-Status-Specific Messaging

- **On Time**: no notification needed; if asked, confirm the promised
  delivery date and current shipment status.
- **At Risk**: proactively state the order may arrive later than
  planned, give the best-known revised ETA, and note the SLA has not
  been breached yet.
- **Breached**: acknowledge the breach directly, state the revised ETA,
  name the escalation contact, and state any compensating action if
  applicable per the customer's contract (e.g. expedited shipping fee
  waiver — confirm with account management before promising this).
- **N/A**: use only for cancelled orders or pre-dispatch orders; do not
  use "N/A" language in customer-facing text — instead state the actual
  order stage.

## Decision Criteria and Thresholds

- `Breached` notification window: 4 business hours from detection, all
  tiers.
- `At Risk` notification window: 1 business day, mandatory for
  GOLD/PLATINUM, optional for STANDARD.
- Escalation to phone contact: only after email goes unacknowledged
  past the expected response window for the case's severity (see
  [Escalation Matrix](./05_escalation_matrix.md)).

## Exceptions and Edge Cases

- **Force majeure batch notifications**: sent as a batch referencing
  the event, not per-order detail, per the
  [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md) —
  the standard per-order timing table above does not apply during an
  active exception.
- **Payment-hold notifications**: framed as "finalizing payment," never
  as a delivery delay, since the delay is customer-controlled, not
  operational (see [Payment Hold SOP](./09_payment_hold_sop.md)).
- **Repeat notifications for the same unresolved cause**: do not resend
  the identical message; each follow-up must include what has changed
  since the last update, even if the answer is "still pending broker
  response."

## Revision and Effective Date

Maintained by Customer Support leadership; reviewed whenever a new
delay-cause translation is added to the reference table above.

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
