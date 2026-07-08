# Customer Notification Policy

## Purpose

Defines when and how customers are notified about order delays, SLA
breaches, and resolutions, so that communication is consistent across
support agents, the Co-Pilot, and automated systems.

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

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
