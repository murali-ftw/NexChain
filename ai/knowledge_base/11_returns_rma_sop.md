# Returns / RMA SOP

## Purpose

Standard Operating Procedure for handling customer-initiated returns
(Return Merchandise Authorization) for orders with
`sales_orders.current_status = 'Delivered'`. This SOP governs the
post-delivery lifecycle: eligibility, classification, shipping
logistics, and the refund or replacement decision.

## Scope and Applicability

Applies once an order has been delivered and the customer requests a
return, replacement, or refund for one or more `order_items`. Applies
across all customer tiers, though the eligibility window (below) is
tier-differentiated. Does not apply to orders still in transit or
pending — those are handled under the
[Order Amendment & Cancellation Policy](./10_order_amendment_cancellation_policy.md)
instead.

## Definitions / Key Terms

- **RMA (Return Merchandise Authorization)** — the record opened to
  track a return request from initiation through refund/replacement
  and restocking.
- **NexChain fault** — a return reason attributable to NexChain's
  fulfillment process (damaged on arrival, wrong item, quality issue),
  as opposed to customer preference.
- **Reverse leg** — the return shipment from customer back to the
  receiving warehouse, tracked the same way an outbound shipment is.

## Roles and Responsibilities

- **Customer Support Agent** — opens the RMA (Step 1), classifies the
  return (Step 2), and closes the case (Step 6).
- **Warehouse Inventory Analyst** — inspects returned inventory and
  decides restock vs. dispose (Step 5).
- **Accounts Receivable** — processes the refund against the original
  `payment` record (Step 4).

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
Verify the request falls within the eligibility window for the
customer's tier before proceeding — a request outside the window (and
not a damaged/wrong-item exemption) should be declined at this step,
not carried through the full procedure.

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

## Decision Criteria and Thresholds

- Eligibility windows: 14 days (STANDARD), 21 days (GOLD), 30 days
  (PLATINUM, plus director-approved exceptions), 60 days
  (damaged/wrong-item, all tiers).
- Refund timeline: 5–7 business days after inspection.
- NexChain-fault returns: no cost to customer including return
  shipping; customer-preference returns: refund minus return shipping.

## Exceptions and Edge Cases

- **Item returned after the eligibility window with no damage/wrong-item
  claim**: default is to decline; PLATINUM-tier case-by-case exceptions
  require explicit Regional Operations Director approval, not agent
  discretion.
- **Return classified as customer preference but inspection reveals a
  genuine quality issue**: reclassify as NexChain fault retroactively
  and adjust the refund to full (including return shipping) before
  closing the RMA.
- **Replacement requested but the SKU is now short** (see
  [Inventory Shortage SOP](./04_inventory_shortage_sop.md)): the
  replacement order follows standard fulfillment, including standard
  shortage handling — it is not fast-tracked past inventory
  availability just because it originated from a return.

## Revision and Effective Date

Maintained by Customer Support leadership; reviewed annually alongside
tier benefit reviews, since eligibility windows are a tier-differentiated
benefit.

## Related Documents

- [Order Amendment & Cancellation Policy](./10_order_amendment_cancellation_policy.md)
- [Payment Hold SOP](./09_payment_hold_sop.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
