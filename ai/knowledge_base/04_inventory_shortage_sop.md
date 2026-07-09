# Inventory Shortage SOP

## Purpose

Standard Operating Procedure for orders that cannot be fully allocated
or dispatched because on-hand inventory at the fulfilling warehouse is
insufficient. This SOP exists to prevent shortages from silently
becoming delivery delays — every shortage must be diagnosed, decided on,
and communicated within a bounded time, not left to resolve itself.

## Scope and Applicability

Applies when `inventory.quantity_on_hand - inventory.quantity_reserved`
for a SKU is less than the outstanding `order_items.quantity` needed to
fulfill one or more open `sales_orders`, or when
`inventory.quantity_on_hand` falls below `inventory.reorder_level`
for a SKU with open demand. Applies across all `warehouse` locations and
all customer tiers, though the fulfillment decision in Step 3 below is
tier-differentiated. Does not apply once an order has already dispatched
— a post-dispatch stock discrepancy is a warehouse or carrier issue, not
an inventory shortage, and should be routed to the
[Warehouse Delay SOP](./07_warehouse_delay_sop.md) or
[Carrier Delay Handling SOP](./08_carrier_delay_handling_sop.md) instead.

## Definitions / Key Terms

- **Available quantity** — `quantity_on_hand - quantity_reserved` for a
  SKU at a specific warehouse; this is the true dispatchable quantity,
  not raw `quantity_on_hand`.
- **Reorder level** — the `inventory.reorder_level` threshold below
  which replenishment should already be triggered; falling below it
  with open demand is itself a shortage signal even before a specific
  order fails allocation.
- **Partial fulfillment** — shipping the available portion of an order
  now and backordering the remainder, as opposed to holding the entire
  order until full quantity is available.
- **Replenishment lead time** — the time between triggering a purchase
  order and new stock being receivable at the warehouse.

## Roles and Responsibilities

- **Warehouse Inventory Analyst** — detects and confirms shortfalls
  (Steps 1–2).
- **Procurement Analyst** — owns replenishment triggering (Step 4) and
  reorder-level tuning (Prevention section).
- **Logistics Coordinator / Manager / Regional Operations Director** —
  owns the partial-fulfillment decision (Step 3) for GOLD/PLATINUM
  orders and any resulting escalation.

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
quantities within the same day. A shortage confirmed against stale data
can trigger an unnecessary warehouse re-route or customer notification,
so this step is not optional even under time pressure.

### 2. Check Alternate Warehouses

Query `inventory` for the same SKU across other `warehouse` rows. If
stock is available elsewhere, evaluate a warehouse re-route: compare the
delivery time impact of shipping from the alternate warehouse against
simply waiting for replenishment at the original warehouse. As a rule of
thumb, re-route only if the alternate warehouse's added transit time is
less than the estimated replenishment lead time at the original
warehouse.

### 3. Partial Fulfillment Decision

If only partial quantity is available, decide (with the account or
logistics team) whether to:
- Ship the available quantity now and backorder the remainder, or
- Hold the entire order until full quantity is available.

Default policy: ship partial for PLATINUM and GOLD tier customers to
protect their SLA; hold for STANDARD tier unless the customer explicitly
requests partial shipment. This default reflects the same tier logic
used throughout the knowledge base — higher tiers get more tolerance on
delivery date but faster, more proactive intervention when a shortfall
occurs.

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

## Decision Criteria and Thresholds

- Re-route to alternate warehouse only if its added transit time is
  shorter than the original warehouse's replenishment lead time.
- Partial fulfillment default: ship for GOLD/PLATINUM, hold for
  STANDARD unless the customer requests otherwise.
- Domestic replenishment lead time: 5–10 business days. International:
  15–30 business days.

## Exceptions and Edge Cases

- **Recurring shortages on the same SKU**: do not keep handling as
  one-off exceptions — escalate to Procurement for a reorder-level
  increase (see Prevention below).
- **Shortage discovered after partial reservation for multiple open
  orders on the same SKU**: allocate available stock in order of
  `promised_delivery_date` (earliest first), then by tier if dates tie,
  so no single large order silently exhausts stock reserved implicitly
  for smaller, more time-sensitive orders.
- **Shortage caused by a data entry error** (e.g., `reorder_level` set
  too low for actual demand velocity): treat as a Prevention-track
  issue, not a one-time exception — correct the threshold immediately
  rather than waiting for the quarterly review.

## Prevention

Warehouses should maintain `reorder_level` thresholds calibrated to
average weekly demand per SKU. Recurrent shortages on the same SKU
should be flagged to procurement for a reorder-level increase rather
than repeatedly handled as one-off exceptions. Procurement Analysts
review reorder levels quarterly against the prior quarter's demand
velocity, and immediately following any SKU that triggered two or more
shortages in a single quarter.

## Revision and Effective Date

Maintained jointly by Warehouse Inventory Analysts and Procurement;
reviewed quarterly alongside the reorder-level calibration cycle
described in Prevention.

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Warehouse Delay SOP](./07_warehouse_delay_sop.md)
- [SLA Policy](./01_sla_policy.md)
- [Escalation Matrix](./05_escalation_matrix.md)
