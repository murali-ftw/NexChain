# Order Amendment & Cancellation Policy

## Purpose

Defines when and how a `sales_orders` record may be amended (quantity,
items, delivery address, delivery date) or cancelled, and the
downstream effects on inventory, invoicing, and shipment records.

## Amendment Windows

| Order Stage (`current_status`) | Amendment Allowed? | Notes |
|---|---|---|
| `Pending` | Yes, freely | No inventory reserved for dispatch yet beyond standard reservation; amend `order_items` directly. |
| `Dispatched` | Limited | Item/quantity changes not allowed; delivery address or delivery date changes may be possible depending on carrier stage — check `shipment.shipment_status`. |
| `In Transit` | Very limited | Only carrier-supported actions (e.g. address correction via carrier portal). Item/quantity changes not possible. |
| `Delayed` | Same as underlying stage | Follow the amendment rule for whatever `shipment_status` currently applies; a delay does not itself unlock amendment options. |
| `Delivered` | No | Use the [Returns / RMA SOP](./11_returns_rma_sop.md) instead. |
| `Cancelled` | No | Order is terminal. |

## Amendment Procedure

1. Confirm current `sales_orders.current_status` and, if dispatched,
   `shipment.shipment_status`.
2. For item/quantity changes on `Pending` orders: update `order_items`,
   re-verify `inventory` availability for the new quantities (see
   [Inventory Shortage SOP](./04_inventory_shortage_sop.md) if the
   amendment creates a shortfall), and recompute `total_amount` on
   `sales_orders`.
3. For delivery date changes: update `promised_delivery_date` only with
   explicit customer confirmation, since this directly affects SLA
   calculation baselines. Log the change reason.
4. For delivery address changes post-dispatch: route through the
   carrier's in-transit address change process; not all carriers or
   shipment stages support this. If unsupported, the order must
   complete delivery to the original address or be handled as a return.

## Cancellation Procedure

1. Cancellation is permitted for `Pending` orders without restriction.
2. Cancellation of `Dispatched` or `In Transit` orders requires a
   recall/return-to-sender request through the carrier — not a simple
   status change — and typically incurs return shipping cost. Coordinate
   with the [Returns / RMA SOP](./11_returns_rma_sop.md).
3. On approved cancellation:
   - Set `sales_orders.current_status = 'Cancelled'`.
   - Release any `inventory.quantity_reserved` held against the order's
     `order_items`.
   - If an `invoice` exists and is unpaid, void it. If paid, initiate a
     refund via the linked `payment` record.
4. Notify the customer of the cancellation confirmation and, if
   applicable, refund timeline, per the
   [Customer Notification Policy](./06_customer_notification_policy.md).

## SLA Interaction

A `Cancelled` order's SLA status is `N/A` — it is excluded from breach
reporting and escalation once cancellation is confirmed. Orders
cancelled *after* already breaching SLA retain the breach in historical
`audit_log` records for reporting purposes, but no further escalation
action is required.

## Related Documents

- [Inventory Shortage SOP](./04_inventory_shortage_sop.md)
- [Returns / RMA SOP](./11_returns_rma_sop.md)
- [Payment Hold SOP](./09_payment_hold_sop.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
