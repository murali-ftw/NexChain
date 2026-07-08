# Carrier Delay Handling SOP

## Purpose

Standard Operating Procedure for delays that originate with the
third-party carrier after a shipment has been dispatched — as opposed to
customs holds (see [Customs Hold SOP](./03_customs_hold_sop.md)), which
are a specific carrier-adjacent case with its own dedicated procedure.

## Scope

Applies when `shipment.shipment_status = 'In Transit'` (or similar) and
`carrier_tracking` events indicate the shipment is behind the carrier's
originally committed transit time, for reasons attributable to the
carrier rather than customs, inventory, or warehouse processing.

## Common Causes

- Weather disruption affecting a transit hub or route.
- Carrier network capacity constraints (peak season volume).
- Mis-routing or mis-sort at a carrier hub.
- Mechanical/logistics failure (vehicle breakdown, missed connection).
- Lost-in-transit (rare; requires a separate claims process, see below).

## Step-by-Step Procedure

### 1. Confirm the Delay Is Carrier-Side

Review the latest `carrier_tracking.event_status` and `event_location`
for the shipment. Carrier-side delay is confirmed when tracking shows no
progress for longer than the carrier's normal inter-checkpoint interval,
or an explicit exception event (e.g. "Delayed due to weather",
"Mis-sorted, rerouting").

### 2. Contact the Carrier

Open a trace/inquiry with the carrier using `shipment.tracking_no` and
`carrier_name`. Request an updated transit estimate and root cause
confirmation.

### 3. Classify Severity

- **Minor** (1–2 day slip, carrier confirms recovery in transit): monitor,
  no customer notification required unless tier policy says otherwise.
- **Moderate** (3+ day slip, or hub mis-route requiring reroute): update
  revised ETA, notify customer.
- **Severe** (lost-in-transit suspected, no tracking update for 5+ days):
  escalate immediately and open a carrier claims investigation in
  parallel with customer notification.

### 4. Estimate Revised ETA

Typical resolution times:
- Weather disruption: 1–3 business days once the route reopens.
- Capacity constraint: 2–4 business days.
- Mis-route: 2–5 business days depending on how far off-route the
  shipment traveled.
- Lost-in-transit: no reliable ETA until the carrier claims process
  locates the shipment or confirms loss (can take 10+ business days);
  treat as a high-severity exception per
  [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md)
  if unresolved beyond 10 business days.

### 5. Update and Recompute SLA

Set `revised_delivery_date`, recompute SLA status per
[SLA Policy](./01_sla_policy.md).

### 6. Escalate if Breached

Escalate per the [Escalation Matrix](./05_escalation_matrix.md). Severe
cases (lost-in-transit) escalate immediately regardless of computed SLA
status, since resolution time is unpredictable.

### 7. Notify

Notify per the
[Customer Notification Policy](./06_customer_notification_policy.md).
For lost-in-transit cases, be explicit that an investigation is
underway rather than promising a specific delivery date.

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [Customs Hold SOP](./03_customs_hold_sop.md)
- [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md)
- [SLA Policy](./01_sla_policy.md)
