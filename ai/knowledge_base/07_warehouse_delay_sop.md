# Warehouse Delay SOP

## Purpose

Standard Operating Procedure for delays caused by warehouse-side
processing — picking, packing, quality checks, or dispatch scheduling —
rather than inventory availability or carrier transit. This SOP exists
to separate "we have the stock but can't get it out the door fast
enough" from a true inventory shortfall, since the two have different
root causes and different remediation paths.

## Scope and Applicability

Applies when `sales_orders.current_status` remains `Pending` or has not
progressed to `Dispatched` within the warehouse's normal processing
window, even though inventory is confirmed available (see
[Inventory Shortage SOP](./04_inventory_shortage_sop.md) if the root
cause is actually a stock shortfall, not a processing delay). Applies
to every `warehouse` location and every customer tier; the expedite
step (Step 3) is tier-differentiated but detection and diagnosis are
not.

## Definitions / Key Terms

- **Normal processing window** — the expected time from order
  confirmation to dispatch under standard warehouse load, used as the
  baseline against which a delay is measured.
- **QC hold** — a quality-control stop placed on a SKU or batch,
  independent of order-specific issues, that blocks picking until
  cleared.
- **Expedite priority** — reordering an order ahead of the standard
  first-in-first-out picking queue.

## Roles and Responsibilities

- **Warehouse Shift Supervisor** — first responder for diagnosis (Steps
  1–2) and executes expedite requests (Step 3).
- **Quality Control Inspector** — owns QC hold clearance timing.
- **Logistics Coordinator / Manager** — requests expedite priority for
  GOLD/PLATINUM orders and owns escalation if the SLA breaches.

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
This confirmation step exists because the two failure modes present
identically to the customer (order not dispatching) but require
completely different remediation, so misdiagnosis here wastes the
entire resolution window.

### 2. Identify the Processing Bottleneck

Check with the fulfilling `warehouse` (via `warehouse_code`) for the
specific cause: capacity, QC hold, staffing, or system outage. The
Warehouse Shift Supervisor is the authoritative source for this
diagnosis — do not guess the cause from order data alone, since
multiple causes can look identical from `sales_orders` and `inventory`
data.

### 3. Set Expedite Priority (If Applicable)

For GOLD and PLATINUM tier customers, or orders already `At Risk`,
request the warehouse prioritize picking/packing ahead of standard
queue order. The Warehouse Shift Supervisor confirms whether expedite
is operationally feasible given the current bottleneck — a capacity
backlog can often be expedited for a single order, but a QC hold on an
entire batch generally cannot be bypassed for any one order.

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

## Decision Criteria and Thresholds

- Expedite eligibility: GOLD/PLATINUM tier, or any tier already `At
  Risk`.
- Revised dispatch estimate ranges by cause, as listed in Step 4 above;
  always add normal transit time on top of the dispatch estimate to get
  the full revised delivery date.

## Exceptions and Edge Cases

- **QC hold affecting an entire batch**: cannot be expedited
  order-by-order; the Warehouse Shift Supervisor should communicate a
  single batch-wide resolution estimate to all affected orders rather
  than individually re-estimating each one.
- **System/label outage during a high-volume period**: if the outage
  extends past 1 business day, treat as a capacity backlog on top of
  the outage itself once systems are restored, not just the outage
  duration alone.
- **Misdiagnosed inventory shortfall** discovered mid-SOP: switch to the
  [Inventory Shortage SOP](./04_inventory_shortage_sop.md) immediately;
  do not continue warehouse-side remediation on a stock problem.

## Revision and Effective Date

Maintained by Warehouse Operations leadership; reviewed whenever a
warehouse's normal processing window baseline changes materially (e.g.
after a facility capacity expansion).

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Inventory Shortage SOP](./04_inventory_shortage_sop.md)
- [SLA Policy](./01_sla_policy.md)
- [Escalation Matrix](./05_escalation_matrix.md)
