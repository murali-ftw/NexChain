# Returns / RMA SOP

## Purpose

Standard Operating Procedure for handling customer-initiated returns
(Return Merchandise Authorization) for orders with
`sales_orders.current_status = 'Delivered'`.

## Scope

Applies once an order has been delivered and the customer requests a
return, replacement, or refund for one or more `order_items`.

## Return Eligibility Window

- Standard eligibility: 14 calendar days from delivery date.
- GOLD tier: 21 calendar days from delivery date.
- PLATINUM tier: 30 calendar days from delivery date, plus case-by-case
  exceptions approved by the Regional Operations Director.
- Damaged-on-arrival or wrong-item-shipped claims are exempt from the
  standard window and accepted up to 60 days, since these are NexChain
  fulfillment errors rather than buyer's-remorse returns.

## Step-by-Step Procedure

### 1. Open the RMA

Confirm the order is `Delivered`, capture the `order_id`, the specific
`order_items` being returned, quantity, and reason category:
`Damaged`, `Wrong Item`, `No Longer Needed`, `Quality Issue`, `Other`.

### 2. Classify the Return

- **NexChain fault** (damaged on arrival, wrong item, quality issue
  traceable to fulfillment): full refund or replacement at no cost to
  customer, including return shipping.
- **Customer preference** (no longer needed, ordered wrong item): refund
  minus return shipping cost, subject to eligibility window above.

### 3. Issue Return Shipping Instructions

Provide a return shipping label/instructions referencing the original
`order_no`. Track the return shipment the same way outbound shipments
are tracked, using a new `shipment`-style record for the reverse leg.

### 4. Process Refund or Replacement

- **Refund:** issue against the original `payment` record for the
  invoice tied to the order; update `payment_status` accordingly once
  processed. Refund timeline: 5–7 business days after the returned item
  is received and inspected.
- **Replacement:** create a new `sales_orders` record referencing the
  original as context (not a schema foreign key — track the
  relationship in the customer notification/support ticket), and route
  it through standard fulfillment.

### 5. Restock or Dispose

Inspect returned inventory. If resalable, increase
`inventory.quantity_on_hand` for the SKU at the receiving warehouse. If
damaged/unsalable, dispose per warehouse quality procedures and do not
restock.

### 6. Close the RMA

Confirm refund or replacement completion with the customer per the
[Customer Notification Policy](./06_customer_notification_policy.md).

## Related Documents

- [Order Amendment & Cancellation Policy](./10_order_amendment_cancellation_policy.md)
- [Payment Hold SOP](./09_payment_hold_sop.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
