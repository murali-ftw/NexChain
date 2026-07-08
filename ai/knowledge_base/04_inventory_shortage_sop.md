# Inventory Shortage SOP

## Purpose

Standard Operating Procedure for orders that cannot be fully allocated
or dispatched because on-hand inventory at the fulfilling warehouse is
insufficient.

## Scope

Applies when `inventory.quantity_on_hand - inventory.quantity_reserved`
for a SKU is less than the outstanding `order_items.quantity` needed to
fulfill one or more open `sales_orders`, or when
`inventory.quantity_on_hand` falls below `inventory.reorder_level`
for a SKU with open demand.

## Detecting a Shortage

1. For each unfulfilled `order_items` row, compute available quantity as
   `quantity_on_hand - quantity_reserved` from the `inventory` row
   matching `sku` and the order's `warehouse_id`.
2. If available quantity < `order_items.quantity`, the order is short.
3. Cross-check `reorder_level`: if `quantity_on_hand` is at or below
   `reorder_level`, a replenishment order should already be in motion;
   if not, flag for immediate procurement follow-up.

## Step-by-Step Procedure

### 1. Confirm the Shortfall

Verify the shortage isn't a stale read — re-query `inventory` for the
SKU/warehouse pair, since reservations and receipts can change
quantities within the same day.

### 2. Check Alternate Warehouses

Query `inventory` for the same SKU across other `warehouse` rows. If
stock is available elsewhere, evaluate a warehouse re-route: compare the
delivery time impact of shipping from the alternate warehouse against
simply waiting for replenishment at the original warehouse.

### 3. Partial Fulfillment Decision

If only partial quantity is available, decide (with the account or
logistics team) whether to:
- Ship the available quantity now and backorder the remainder, or
- Hold the entire order until full quantity is available.
Default policy: ship partial for PLATINUM and GOLD tier customers to
protect their SLA; hold for STANDARD tier unless the customer explicitly
requests partial shipment.

### 4. Trigger Replenishment

If no alternate warehouse can cover the shortfall, trigger a
replenishment/purchase order through procurement. Typical replenishment
lead time is 5–10 business days domestically, 15–30 days for
internationally sourced SKUs — factor this into the revised ETA.

### 5. Update Order and Notify

Set a realistic `revised_delivery_date` based on either the alternate
warehouse ship date or the replenishment lead time, recompute SLA status
per [SLA Policy](./01_sla_policy.md), and notify the customer per the
[Customer Notification Policy](./06_customer_notification_policy.md).

### 6. Escalate if Breached

If the shortage pushes the order into `Breached` SLA status, escalate
per the [Escalation Matrix](./05_escalation_matrix.md).

## Prevention

Warehouses should maintain `reorder_level` thresholds calibrated to
average weekly demand per SKU. Recurrent shortages on the same SKU
should be flagged to procurement for a reorder-level increase rather
than repeatedly handled as one-off exceptions.

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Warehouse Delay SOP](./07_warehouse_delay_sop.md)
- [SLA Policy](./01_sla_policy.md)
- [Escalation Matrix](./05_escalation_matrix.md)
