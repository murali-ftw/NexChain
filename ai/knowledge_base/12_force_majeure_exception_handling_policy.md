# Force Majeure & Exception Handling Policy

## Purpose

Defines how NexChain handles delays and disruptions caused by events
outside the normal operational control of the company, its warehouses,
or its carriers — and how such cases are exempted from standard SLA
breach penalties while still being tracked and communicated. This
policy exists to prevent two failure modes: paging operations staff
for delays they cannot act on, and quietly ignoring genuinely
disruptive events that need proactive, batch-level customer
communication.

## Scope and Applicability

Applies to `sales_orders` whose shipments route through a warehouse,
port, or carrier hub affected by a declared qualifying event, across
all customer tiers. It is deliberately narrow in scope — most delays,
even ones "outside the customer's control" in a colloquial sense (a
single carrier mis-route, a single customs hold), are handled by their
own dedicated SOP, not this policy. This policy applies only to
declared, scoped, systemic events.

## Definitions / Key Terms

- **Qualifying event** — one of the categories listed below, formally
  declared by Regional Operations Director or above.
- **Affected scope** — the specific warehouses, routes, or regions
  Operations leadership defines as impacted by a declared event; only
  orders within this scope are flagged.
- **Flagged order** — a `sales_orders` row marked as a force majeure
  exception for the duration of the event, exempting it from standard
  escalation paging while still tracking true SLA status internally.

## Roles and Responsibilities

- **Regional Operations Director (or above)** — sole role authorized to
  declare and close a force majeure exception (Steps below).
- **Fulfillment Operations** — flags and unflags orders within the
  declared scope as it changes.
- **Customer Support leadership** — coordinates batch notification per
  the [Customer Notification Policy](./06_customer_notification_policy.md).

## Qualifying Events

- Natural disasters (floods, earthquakes, typhoons/cyclones) affecting
  a warehouse region, port, or carrier hub.
- Government-imposed restrictions (customs shutdowns, port closures,
  trade embargoes, sudden regulatory changes).
- Widespread carrier network outages not attributable to a single
  shipment issue (e.g. multi-day national logistics strike).
- Public health emergencies affecting warehouse staffing or cross-border
  transit at a systemic level.
- Civil unrest or armed conflict affecting a transit route or region.

Force majeure does **not** cover: routine weather delays handled under
[Carrier Delay Handling SOP](./08_carrier_delay_handling_sop.md), single
-shipment customs issues handled under
[Customs Hold SOP](./03_customs_hold_sop.md), or ordinary inventory/
warehouse capacity issues. Those follow their standard SOPs even though
they are also "outside the customer's control."

## Declaring a Force Majeure Exception

1. Operations leadership (Regional Operations Director or above)
   confirms the event qualifies and defines the affected scope: which
   warehouses, routes, or regions are impacted, and the expected
   duration.
2. All `sales_orders` with shipments routed through the affected
   scope are flagged as force majeure exceptions for the duration of
   the event.
3. Flagged orders are **excluded from SLA breach escalation** while the
   exception is active — they still show their true computed SLA status
   internally (per [SLA Policy](./01_sla_policy.md)) for reporting, but
   `Breached` status does not trigger the standard
   [Escalation Matrix](./05_escalation_matrix.md) paging, since the
   cause is not actionable by the escalation role.

## During the Exception

- Customers with affected orders are proactively notified as a batch,
  referencing the event rather than individual order details, per the
  [Customer Notification Policy](./06_customer_notification_policy.md).
- Revised ETAs are communicated as ranges ("we expect an update within
  X days") rather than firm dates, since the underlying disruption
  timeline is itself uncertain.
- Orders are re-evaluated every 2 business days for scope changes
  (event resolving, expanding, or a specific order now clear of the
  impacted route).

## Closing the Exception

1. Regional Operations Director confirms the event has resolved and the
   affected scope is clear.
2. Flagged orders return to standard SLA tracking and escalation as of
   the closure date — the force majeure period itself is not counted
   against `max_delay_days`, only delay accrued after closure.
3. A post-incident summary is logged for orders that were flagged,
   including total orders affected and average additional delay
   incurred, for future risk planning.

## Decision Criteria and Thresholds

- Declaration authority: Regional Operations Director or above only —
  no other role may flag orders as force majeure.
- Scope re-evaluation cadence: every 2 business days while active.
- `max_delay_days` accounting: the force majeure period itself does not
  count toward breach; only delay accrued after the exception closes
  does.

## Exceptions and Edge Cases

- **An order within the declared scope but genuinely delayed for an
  unrelated reason** (e.g., a QC hold that predates the event): remains
  under its original cause-specific SOP; being geographically within
  an affected scope does not automatically reclassify an unrelated
  delay as force majeure.
- **Event scope expands mid-exception**: re-run the flagging step for
  newly included warehouses/routes; do not wait for the next scheduled
  2-business-day review if the expansion is significant.
- **Single-shipment issue that superficially resembles a systemic
  event** (e.g., one carrier hub temporarily down, not the whole
  network): does not qualify — route to
  [Carrier Delay Handling SOP](./08_carrier_delay_handling_sop.md)
  instead, since it lacks the "widespread" characteristic required
  above.

## Revision and Effective Date

Maintained by Regional Operations Director leadership; reviewed after
every declared exception closes, incorporating the post-incident
summary into future scope-definition guidance.

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Carrier Delay Handling SOP](./08_carrier_delay_handling_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
