# Shipment Delay SOP

## Purpose

Standard Operating Procedure for handling any shipment that will not
arrive by its `promised_delivery_date`, regardless of cause. This SOP is
the general-purpose delay procedure; cause-specific SOPs (Customs Hold,
Warehouse Delay, Carrier Delay) extend it with cause-specific steps and
should be consulted alongside this document.

## Scope

Applies to any `sales_orders` row whose linked `shipment.shipment_status`
indicates the order will miss, or has already missed,
`promised_delivery_date`. Common statuses that trigger this SOP:
`Delayed` (on `sales_orders.current_status`), or a `shipment_status` of
`Customs Hold`, `In Transit` with a carrier-reported delay, or similar.

## Step-by-Step Procedure

### 1. Detect

Delay detection happens automatically via the SLA breach calculation
(see [SLA Policy](./01_sla_policy.md)) comparing `CURRENT_DATE` against
`promised_delivery_date`. Any order computed as `At Risk` or `Breached`
enters this SOP.

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

### 3. Estimate Revised ETA

Set `shipment.revised_delivery_date` on `sales_orders` (via
`revised_delivery_date`) based on the cause-specific SOP's typical
resolution time. If no cause-specific estimate is available yet, use a
conservative placeholder of current date + 3 business days and flag it
as provisional in the customer notification.

### 4. Compute SLA Impact

Recompute SLA status per [SLA Policy](./01_sla_policy.md) using the
revised ETA against `promised_delivery_date` and the customer's
`sla_tier`. This determines whether escalation is required.

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
role.

## Related Documents

- [SLA Policy](./01_sla_policy.md)
- [Customs Hold SOP](./03_customs_hold_sop.md)
- [Inventory Shortage SOP](./04_inventory_shortage_sop.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
