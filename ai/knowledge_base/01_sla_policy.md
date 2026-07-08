# SLA Policy

## Purpose

This document defines the Service Level Agreement (SLA) tiers offered to
NexChain customers, the delivery-delay thresholds that determine SLA
breach status, and the escalation path triggered at each tier. It is the
canonical reference for the Business Rule Agent's SLA breach calculation
and for any customer-facing SLA question.

## SLA Tiers

NexChain customers are assigned one `sla_tier` value on the `customers`
table: `STANDARD`, `GOLD`, or `PLATINUM`. Each tier maps to a row in
`sla_rules` with a `max_delay_days` threshold and an `escalation_role`.

| Tier | max_delay_days | Escalation Role | Typical Customer Profile |
|---|---|---|---|
| STANDARD | 3 days | Logistics Coordinator | Standard-contract customers, no premium SLA add-on |
| GOLD | 5 days | Logistics Manager | Mid-tier accounts with a negotiated delivery guarantee |
| PLATINUM | 7 days | Regional Operations Director | Strategic / enterprise accounts with contractual delivery guarantees |

`max_delay_days` is the number of days past `promised_delivery_date` that
are tolerated before the order is considered in breach. Note that a
higher-tier customer is granted **more** tolerance days, not less — this
reflects that PLATINUM accounts typically ship larger, more complex
international orders where minor customs or carrier variance is expected
contractually, and the guarantee is instead backed by a dedicated
escalation contact and faster remediation, not a tighter delivery window.

## Breach Determination Logic

SLA status is computed by comparing the current date against
`promised_delivery_date`, gated by the customer's `sla_tier` threshold:

- **On Time** — order has not passed `promised_delivery_date`, or has
  already delivered on or before it.
- **At Risk** — order has passed `promised_delivery_date` by 1 or more
  days, but the delay is still within the tier's `max_delay_days`.
- **Breached** — order has passed `promised_delivery_date` by more days
  than the tier's `max_delay_days` allows.
- **N/A** — SLA status does not apply (e.g. order cancelled, no shipment
  record yet, or order not yet dispatched).

These four values (`On Time`, `At Risk`, `Breached`, `N/A`) are the only
valid SLA status strings surfaced to customers or agents. Do not use
synonyms such as "Late" or "Delayed" when reporting SLA status — those
terms describe `sales_orders.current_status` or `shipment.shipment_status`,
which are separate fields from SLA status.

## Escalation on Breach

The moment an order's computed SLA status becomes `Breached`, the order
must be routed to the `escalation_role` for its tier (see table above).
See the [Escalation Matrix](./05_escalation_matrix.md) for the full
severity-to-role mapping and response-time expectations once escalated.

## Worked Example — SO-45892 (Flagship Scenario)

- Customer tier: GOLD (`max_delay_days` = 5)
- `promised_delivery_date`: 2026-07-03
- `revised_delivery_date` (current ETA): 2026-07-09
- Delay: 6 days past promised delivery
- Since 6 days > 5-day GOLD threshold, SLA status = **Breached**
- Escalation role triggered: **Logistics Manager**
- Root cause: shipment held in Customs Hold at Chennai Port due to an
  HS code mismatch during customs validation (see
  [Customs Hold SOP](./03_customs_hold_sop.md))

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Customs Hold SOP](./03_customs_hold_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
