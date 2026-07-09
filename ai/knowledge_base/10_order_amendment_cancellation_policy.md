# Order Amendment & Cancellation Policy

## Purpose

Defines when and how a `sales_orders` record may be amended (quantity,
items, delivery address, delivery date) or cancelled, and the
downstream effects on inventory, invoicing, and shipment records. This
policy exists so amendment and cancellation requests are handled
consistently regardless of which support agent or system surfaces the
request.

## Scope and Applicability

Applies to every `sales_orders` row from creation through delivery or
cancellation, across all customer tiers. Amendment rights are governed
by order stage (`current_status`), not by tier — a PLATINUM customer
does not get a wider amendment window than a STANDARD customer once an
order has dispatched, since the constraint is physical (the shipment is
already in motion), not contractual.

## Definitions / Key Terms

- **Amendment** — any change to `order_items`, delivery address, or
  `promised_delivery_date` on an existing order, short of cancellation.
- **Recall / return-to-sender** — a carrier-initiated action to bring a
  dispatched shipment back rather than complete delivery, functionally
  a cancellation-after-dispatch.
- **Terminal state** — an order status (`Delivered` or `Cancelled`)
  after which no further amendment is possible through this policy.

## Roles and Responsibilities

- **Customer Support Agent** — receives and logs amendment/cancellation
  requests, executes amendments for `Pending` orders directly.
- **Fulfillment Operations** — coordinates carrier-side changes for
  dispatched or in-transit orders (address changes, recalls).
- **Accounts Receivable** — processes voids and refunds resulting from
  cancellation.

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

## Decision Criteria and Thresholds

- `Pending`: unrestricted amendment and cancellation.
- `Dispatched`/`In Transit`: item/quantity changes never allowed;
  address changes only if the carrier's current stage supports it.
- Recall/return-to-sender: only path for cancelling a dispatched order,
  and it typically incurs a return shipping cost passed through to
  standard return-handling accounting.

## SLA Interaction

A `Cancelled` order's SLA status is `N/A` — it is excluded from breach
reporting and escalation once cancellation is confirmed. Orders
cancelled *after* already breaching SLA retain the breach as a
historical fact for internal reporting purposes, but no further
escalation action is required once the order reaches the `Cancelled`
terminal state.

## Exceptions and Edge Cases

- **Amendment request arrives while an order is mid-escalation** (SLA
  `Breached`, actively being worked by a Logistics Manager): amendment
  and escalation proceed in parallel — do not pause escalation to wait
  for an amendment decision, since the underlying delay resolution
  (e.g. customs, carrier) is independent of the requested amendment.
- **Cancellation requested for an order already in a Return/RMA flow**:
  not applicable — once `Delivered`, cancellation is no longer possible
  by definition; redirect to the [Returns / RMA SOP](./11_returns_rma_sop.md).
- **Partial cancellation** (cancel some `order_items` but not others):
  treat as an amendment (reduce quantities/items) followed by
  `total_amount` recomputation, not a full order cancellation.

## Revision and Effective Date

Maintained by Customer Support leadership in coordination with
Fulfillment Operations; reviewed whenever carrier-supported in-transit
amendment capabilities change.

## Related Documents

- [Inventory Shortage SOP](./04_inventory_shortage_sop.md)
- [Returns / RMA SOP](./11_returns_rma_sop.md)
- [Payment Hold SOP](./09_payment_hold_sop.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
