# Force Majeure & Exception Handling Policy

## Purpose

Defines how NexChain handles delays and disruptions caused by events
outside the normal operational control of the company, its warehouses,
or its carriers — and how such cases are exempted from standard SLA
breach penalties while still being tracked and communicated.

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

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Carrier Delay Handling SOP](./08_carrier_delay_handling_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
