# SLA Policy

## Purpose

This document defines the Service Level Agreement (SLA) tiers offered to
NexChain customers, the delivery-delay thresholds that determine SLA
breach status, and the escalation path triggered at each tier. It is the
canonical reference for the Business Rule Agent's SLA breach calculation
and for any customer-facing SLA question. Every other document in this
knowledge base that mentions SLA status, breach, or escalation defers to
this policy as the source of truth.

## Scope and Applicability

This policy applies to every `sales_orders` row regardless of order
type, product category, or fulfillment channel, from the moment
`current_status` moves to `Dispatched` through final delivery or
cancellation. It applies uniformly across all NexChain warehouse
regions (currently Chennai and the other `warehouse` locations on
file); there is no region-specific SLA variance — tier, not
geography, determines the delay threshold. It does not apply to
pre-dispatch stages (`Pending`) or to orders that never reach dispatch
because they were cancelled; those are `N/A` per the Breach
Determination Logic below. Business, government, and marketplace
reseller accounts are all assigned a standard `sla_tier` like any other
customer — there is no separate SLA schedule for account type, only
for tier.

## Definitions / Key Terms

- **`sla_tier`** — the tier value on the `customers` table:
  `STANDARD`, `GOLD`, or `PLATINUM`. Assigned at account creation and
  changeable only by account management, not by a single order.
- **`max_delay_days`** — the number of days past
  `promised_delivery_date` that a given tier tolerates before an order
  is considered in breach. Stored per tier in `sla_rules`.
- **`escalation_role`** — the operational role responsible for a
  breached order of a given tier, also stored in `sla_rules`.
- **Delay days** — `CURRENT_DATE - promised_delivery_date`, computed
  only when that value is positive (an order not yet past its promised
  date has zero delay days for SLA purposes).
- **SLA status** — one of exactly four values: `On Time`, `At Risk`,
  `Breached`, `N/A`. This is a computed field, never stored verbatim;
  it must always be recalculated from current data, not cached from a
  prior check.

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

## Trigger Conditions (When SLA Status Is Evaluated)

SLA status must be recomputed, not just read from a prior calculation,
whenever any of the following occurs:

1. A scheduled daily batch check runs against every `sales_orders` row
   with `current_status` in (`Dispatched`, `In Transit`, `Delayed`).
2. `shipment.shipment_status` changes (e.g., moves into `Customs Hold`,
   or moves from `In Transit` to `Delivered`).
3. `revised_delivery_date` is set or updated by any of the
   cause-specific SOPs (Customs Hold, Inventory Shortage, Warehouse
   Delay, Carrier Delay).
4. A user or the Co-Pilot explicitly asks about an order's delay or SLA
   status — the answer must reflect a fresh calculation, not a cached
   value, since `CURRENT_DATE` changes daily even with no other data
   changes.

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

Concretely, for an order with delay days `d` and tier threshold
`max_delay_days = m`:

- `d <= 0` → `On Time`
- `0 < d <= m` → `At Risk`
- `d > m` → `Breached`

## Escalation on Breach

The moment an order's computed SLA status becomes `Breached`, the order
must be routed to the `escalation_role` for its tier (see table above).
This routing is automatic and does not wait for a human to notice the
breach — the daily batch check (see Trigger Conditions) is the primary
detection mechanism, with real-time recomputation on shipment status
changes as a secondary trigger. See the
[Escalation Matrix](./05_escalation_matrix.md) for the full
severity-to-role mapping and response-time expectations once escalated.

## Exceptions and Edge Cases

- **Force majeure events** (natural disasters, port closures, carrier
  network outages): affected orders are flagged per the
  [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md)
  and excluded from escalation paging while the exception is active,
  even though their true SLA status is still computed and visible.
- **Payment holds**: per the [Payment Hold SOP](./09_payment_hold_sop.md),
  the delivery SLA clock is paused while an order is legitimately held
  for payment reasons — the customer, not NexChain operations, controls
  resolution time, so payment-hold delay does not count toward
  `max_delay_days`.
- **Multiple revisions to `revised_delivery_date`**: SLA status is
  always computed against the original `promised_delivery_date`, never
  against a revised estimate. A revised ETA changes customer
  communication, not the breach math.
- **Same-day dispatch and delivery**: if `promised_delivery_date`
  equals the actual delivery date, the order is `On Time`, not `At
  Risk` — the threshold is strictly "past," not "on."

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

## Revision and Effective Date

This policy is effective as of the current fiscal year and is reviewed
quarterly by the Regional Operations Director alongside the
[Escalation Matrix](./05_escalation_matrix.md). Any change to
`max_delay_days` or `escalation_role` values requires updating both this
document and the `sla_rules` table in the same change window — the two
must never diverge.

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Customs Hold SOP](./03_customs_hold_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
- [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md)
