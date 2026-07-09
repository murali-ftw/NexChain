# Shipment Delay SOP

## Purpose

Standard Operating Procedure for handling any shipment that will not
arrive by its `promised_delivery_date`, regardless of cause. This SOP is
the general-purpose delay procedure; cause-specific SOPs (Customs Hold,
Inventory Shortage, Warehouse Delay, Carrier Delay) extend it with
cause-specific steps and should be consulted alongside this document.
Think of this SOP as the triage layer: it tells operations staff how to
detect a delay, where to route the investigation, and how to close the
loop once a cause-specific SOP has produced a resolution.

## Scope and Applicability

Applies to any `sales_orders` row whose linked `shipment.shipment_status`
indicates the order will miss, or has already missed,
`promised_delivery_date`. Common statuses that trigger this SOP:
`Delayed` (on `sales_orders.current_status`), or a `shipment_status` of
`Customs Hold`, `In Transit` with a carrier-reported delay, or similar.
It applies to every customer tier and every fulfilling `warehouse` —
there is no tier-specific delay-detection variant, only tier-specific
escalation timing once a delay is confirmed (see
[SLA Policy](./01_sla_policy.md)). It does not apply to orders still in
`Pending` status that have not yet been dispatched; those are handled
under normal order processing, not delay management, unless the
pending state itself becomes the delay (see
[Warehouse Delay SOP](./07_warehouse_delay_sop.md)).

## Definitions / Key Terms

- **Delay cause** — the underlying operational reason a shipment will
  miss its promised date: customs, inventory, warehouse processing, or
  carrier transit. Every delay must be attributed to exactly one
  primary cause for reporting purposes, even if secondary factors
  contributed.
- **Revised ETA** — the operations team's current best estimate of
  actual delivery date, stored in `sales_orders.revised_delivery_date`.
  It is always an estimate, not a guarantee, and must be re-evaluated
  as new information arrives.
- **Provisional estimate** — a placeholder revised ETA used when no
  cause-specific estimate is yet available (see Step 3 below);
  provisional estimates must be flagged as such to the customer.

## Roles and Responsibilities

- **Fulfillment Operations** — first responder for delay detection and
  diagnosis (Steps 1–2).
- **Logistics Coordinator** (STANDARD tier) / **Logistics Manager**
  (GOLD tier) / **Regional Operations Director** (PLATINUM tier) —
  owns escalated cases per the [Escalation Matrix](./05_escalation_matrix.md).
- **Customer Support Agent** — executes customer notification per the
  [Customer Notification Policy](./06_customer_notification_policy.md)
  once the escalation role has approved the messaging for `Breached`
  cases.

## Step-by-Step Procedure

### 1. Detect

Delay detection happens automatically via the SLA breach calculation
(see [SLA Policy](./01_sla_policy.md)) comparing `CURRENT_DATE` against
`promised_delivery_date`. Any order computed as `At Risk` or `Breached`
enters this SOP. Fulfillment Operations reviews the daily delay report
each morning as the primary detection checkpoint; shipment-status
webhook events (where available) provide a secondary, real-time
detection path.

### 2. Diagnose

Identify the delay cause by inspecting, in order:
1. `shipment.delay_reason` — free-text reason set by operations or the
   carrier integration (e.g. "HS code mismatch during customs
   validation").
2. `shipment.shipment_status` — categorical status (`Customs Hold`,
   `In Transit`, etc.).
3. `carrier_tracking` events for the shipment — the most recent
   `event_status` and `event_location` give the latest ground truth.

Route to the matching cause-specific SOP:
- Customs-related → [Customs Hold SOP](./03_customs_hold_sop.md)
- Inventory shortfall blocking dispatch → [Inventory Shortage SOP](./04_inventory_shortage_sop.md)
- Warehouse processing delay → [Warehouse Delay SOP](./07_warehouse_delay_sop.md)
- Carrier-side delay (weather, capacity, mis-route) → [Carrier Delay Handling SOP](./08_carrier_delay_handling_sop.md)

If diagnosis is ambiguous between two causes (for example, a shipment
shows both a warehouse dispatch delay and a subsequent carrier
mis-route), attribute the primary cause as whichever occurred first in
the timeline, and note the secondary factor in the escalation record.

### 3. Estimate Revised ETA

Set `revised_delivery_date` on `sales_orders` based on the
cause-specific SOP's typical resolution time. If no cause-specific
estimate is available yet, use a conservative placeholder of current
date + 3 business days and flag it as provisional in the customer
notification. Provisional estimates must be revisited within 1
business day once the cause-specific SOP produces a firmer number.

### 4. Compute SLA Impact

Recompute SLA status per [SLA Policy](./01_sla_policy.md) using the
revised ETA against `promised_delivery_date` and the customer's
`sla_tier`. This determines whether escalation is required. This step
must be re-run every time the revised ETA changes, not just once at
initial detection.

### 5. Escalate if Breached

If SLA status is `Breached`, escalate immediately per the
[Escalation Matrix](./05_escalation_matrix.md). If `At Risk`, monitor
and re-evaluate daily; no escalation required yet, but proactive
notification is still recommended (see
[Customer Notification Policy](./06_customer_notification_policy.md)).

### 6. Notify

Notify the customer according to the
[Customer Notification Policy](./06_customer_notification_policy.md),
including the delay reason, revised ETA, and (if breached) the
escalation contact.

### 7. Resolve and Close

Once the shipment is delivered, mark `sales_orders.current_status =
'Delivered'` and archive the delay record. No further action is
required unless a post-incident review is requested by the escalation
role. For `Breached` cases, the escalation role should confirm closure
explicitly rather than relying on the status change alone, so that the
customer notification of resolution (see
[Customer Notification Policy](./06_customer_notification_policy.md))
is sent promptly.

## Decision Criteria and Thresholds

- Delay detection runs at least once daily; real-time triggers on
  `shipment_status` change take priority when available.
- Provisional ETA placeholder: current date + 3 business days, revisited
  within 1 business day.
- Escalation timing follows tier-based SLA thresholds (3/5/7 days for
  STANDARD/GOLD/PLATINUM per [SLA Policy](./01_sla_policy.md)), not a
  fixed calendar deadline independent of tier.

## Exceptions and Edge Cases

- **Multi-cause delays**: attribute to the earliest-occurring primary
  cause; log the secondary cause for trend reporting.
- **Force majeure-flagged orders**: follow this SOP for diagnosis and
  ETA estimation, but suppress standard escalation paging per the
  [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md).
- **Already-cancelled orders**: if an order is cancelled mid-delay
  investigation, close this SOP immediately without further ETA
  estimation — cancellation supersedes delay management.

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Customs Hold SOP](./03_customs_hold_sop.md)
- [Inventory Shortage SOP](./04_inventory_shortage_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)

## Revision and Effective Date

This SOP is maintained by Fulfillment Operations and reviewed whenever a
cause-specific SOP it references is updated, to keep routing logic (Step
2) accurate.
