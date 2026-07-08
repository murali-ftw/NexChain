# Warehouse Delay SOP

## Purpose

Standard Operating Procedure for delays caused by warehouse-side
processing — picking, packing, quality checks, or dispatch scheduling —
rather than inventory availability or carrier transit.

## Scope

Applies when `sales_orders.current_status` remains `Pending` or has not
progressed to `Dispatched` within the warehouse's normal processing
window, even though inventory is confirmed available (see
[Inventory Shortage SOP](./04_inventory_shortage_sop.md) if the root
cause is actually a stock shortfall, not a processing delay).

## Common Causes

- Warehouse operating at or above picking/packing capacity for the day.
- Quality control hold on the SKU (batch recall, damaged stock found
  during picking).
- Staffing shortfall (holiday, absence spike) at the fulfilling
  `warehouse`.
- Dispatch scheduling conflict with the carrier's pickup window.
- System/label printing outage at the warehouse.

## Step-by-Step Procedure

### 1. Confirm the Order Is Warehouse-Blocked, Not Inventory-Blocked

Re-verify `inventory.quantity_on_hand - quantity_reserved` covers all
`order_items` for the order. If inventory is the actual constraint,
switch to the [Inventory Shortage SOP](./04_inventory_shortage_sop.md).

### 2. Identify the Processing Bottleneck

Check with the fulfilling `warehouse` (via `warehouse_code`) for the
specific cause: capacity, QC hold, staffing, or system outage.

### 3. Set Expedite Priority (If Applicable)

For GOLD and PLATINUM tier customers, or orders already `At Risk`,
request the warehouse prioritize picking/packing ahead of standard
queue order.

### 4. Estimate Revised Dispatch Date

Typical resolution times:
- Capacity backlog: 1–2 business days.
- QC hold: 2–5 business days depending on inspection scope.
- Staffing shortfall: 1–3 business days.
- System/label outage: same day to 1 business day once IT resolves it.

### 5. Update and Recompute SLA

Set `revised_delivery_date` factoring in the warehouse delay plus normal
transit time, and recompute SLA status per
[SLA Policy](./01_sla_policy.md).

### 6. Escalate if Breached

If the recomputed SLA status is `Breached`, escalate per the
[Escalation Matrix](./05_escalation_matrix.md).

### 7. Notify

Notify the customer per the
[Customer Notification Policy](./06_customer_notification_policy.md),
framing the cause as "fulfillment processing" rather than internal
warehouse operational detail.

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Inventory Shortage SOP](./04_inventory_shortage_sop.md)
- [SLA Policy](./01_sla_policy.md)
