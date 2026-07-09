# Customs Hold SOP

## Purpose

Standard Operating Procedure for shipments placed on `Customs Hold`
(`shipment.shipment_status = 'Customs Hold'`), including the most common
cause seen in NexChain's export lanes: an **HS code mismatch during
customs validation**. This SOP directly supports the SO-45892 flagship
scenario referenced throughout the knowledge base and the SLA Policy,
and it is the primary document the Knowledge Base Agent should surface
whenever a user asks why a shipment is held at customs, what an HS code
mismatch is, or what action to take for a customs-related delay.

## Scope and Applicability

Applies to any shipment where `shipment_status = 'Customs Hold'`,
typically surfaced alongside a `delay_reason` describing the specific
customs issue and a `current_location` at a port or customs facility
(e.g. "Chennai Port"). This SOP applies to all export and cross-border
lanes regardless of customer `sla_tier` — the customs remediation steps
themselves do not vary by tier, though the escalation timing and
customer communication tone do (see
[SLA Policy](./01_sla_policy.md) and
[Customer Notification Policy](./06_customer_notification_policy.md)).
It does not apply to domestic-only shipments, which by definition never
enter a customs checkpoint.

## Definitions / Key Terms

- **HS code (Harmonized System code)** — the standardized numeric
  classification code used internationally to categorize traded goods
  for customs duty and regulatory purposes. Each `order_items.sku` maps
  to exactly one correct HS code based on current product
  classification.
- **Commercial invoice** — the shipping document submitted to customs
  that declares the goods, their value, and their HS code(s); this is
  the document corrected when an HS code mismatch is found.
- **Customs broker** — the third-party agent (or, for self-managed
  clearance customers, the customer's own import agent) who submits
  documentation to customs authorities on NexChain's or the customer's
  behalf and manages the clearance process.
- **Re-validation** — the customs authority's re-review of a corrected
  commercial invoice, tracked via `carrier_tracking` events.

## Common Cause: HS Code Mismatch During Customs Validation

### What It Means

The Harmonized System (HS) code declared on the commercial invoice or
shipping manifest does not match the HS code customs authorities
associate with the declared goods category. Customs will not clear the
shipment until the discrepancy is resolved, because the HS code
determines duty rate, import eligibility, and regulatory classification.
This is the single most common cause of `Customs Hold` status in
NexChain's shipment history and is the root cause of the SO-45892
flagship scenario.

### Detection

An HS code mismatch is typically first surfaced by one of two signals:
1. `shipment.shipment_status` transitions to `Customs Hold` and
   `shipment.delay_reason` is populated with text such as "HS code
   mismatch during customs validation."
2. A `carrier_tracking` event with `event_status` such as "Held at
   customs — documentation discrepancy" appears at a port or customs
   facility `event_location` (e.g. "Chennai Port").

Fulfillment Operations should treat either signal as sufficient to open
this SOP; there is no need to wait for both.

### Who Is Notified

On detection, Fulfillment Operations notifies the assigned Customs
Compliance Specialist (or, where no dedicated specialist exists,
routes directly to the Logistics Coordinator/Manager per tier) to begin
Step 1 of the Resolution Steps below. If the recomputed SLA status is
already `At Risk` or `Breached` at time of detection, the relevant
escalation role from the [Escalation Matrix](./05_escalation_matrix.md)
is notified in parallel, not sequentially, so remediation and
escalation proceed at the same time rather than one waiting on the
other.

### Why It Happens

- Product classification was updated by the manufacturer but the
  shipping paperwork used a stale HS code.
- A multi-SKU shipment declared a single HS code that doesn't cover all
  items in `order_items`.
- Data entry error when the commercial invoice was generated.
- Destination country recently revised its HS code schedule.

### Resolution Steps

1. **Verify the HS code in the commercial invoice.** Compare the
   declared HS code against the product's current classification in the
   product master data. Confirm against `order_items.sku` and
   `product_name` for every line item on the affected order. This is
   done by the Customs Compliance Specialist or, in their absence, the
   Logistics Coordinator/Manager assigned to the order.
2. **Identify the correct HS code(s).** If the shipment has multiple
   SKUs with different classifications, each may need its own HS code
   line on the invoice.
3. **Send the corrected document to the customs broker.** The customs
   broker (or, if the customer manages their own clearance, the
   customer's import agent) submits the corrected commercial invoice for
   re-validation.
4. **Track re-validation status via `carrier_tracking`.** Expect an
   `event_status` update such as "Customs re-validation submitted"
   followed eventually by "Cleared customs" once resolved.
5. **Update `shipment.shipment_status`** to `In Transit` once customs
   clears the corrected paperwork, and set a realistic
   `revised_delivery_date` on the order.
6. **Escalate to the Logistics Manager** if the hold is not resolved
   within 2 business days of the corrected invoice being submitted, or
   immediately if the recomputed SLA status is `Breached` (see
   [Escalation Matrix](./05_escalation_matrix.md)).
7. **Notify the customer** with the revised ETA and a plain-language
   summary of the cause, per the
   [Customer Notification Policy](./06_customer_notification_policy.md).

### Typical Resolution Time

An HS code mismatch typically resolves within **2 to 4 business days**
from the moment the corrected invoice is submitted to customs, assuming
no additional regulatory review is triggered. Complex multi-SKU
shipments or destinations with stricter customs review can extend this
to 5–7 business days. Operations should set the initial
`revised_delivery_date` estimate at **promised delivery date + 6 days**
for HS code mismatch cases unless a broker provides a more specific
estimate — this matches the flagship SO-45892 scenario, where the
6-day delay pushed the SLA status to `Breached` under the customer's
GOLD tier (5-day threshold).

### How the Revised ETA Is Communicated

Once the revised delivery date is set (Step 5), Customer Support Agent
sends the notification per the
[Customer Notification Policy](./06_customer_notification_policy.md),
translating "HS code mismatch during customs validation" into
customer-facing language such as "a customs paperwork correction is in
progress," stating the revised ETA, and — because this is a `Breached`
scenario at the GOLD tier and above — naming the Logistics Manager as
the escalation contact now managing the case. The notification must go
out within 4 business hours of the SLA status becoming `Breached`, per
the [Escalation Matrix](./05_escalation_matrix.md) High-severity
response window.

## Other Customs Hold Causes (Brief)

- **Missing or incomplete import documentation** — certificate of
  origin, license, or permit not attached. Resolve by sourcing the
  missing document from the customer or supplier; typical resolution
  1–3 business days.
- **Random compliance inspection** — customs selects the shipment for
  physical inspection independent of any paperwork issue. No action
  possible beyond monitoring; typical resolution 3–5 business days.
- **Under/over-valuation flag** — declared value flagged as inconsistent
  with the goods category. Resolve by providing supporting
  commercial documentation (purchase order, price list); typical
  resolution 2–4 business days.

## Decision Criteria and Thresholds

- Escalate to Logistics Manager if unresolved 2+ business days after
  corrected invoice submission, or immediately on `Breached` SLA status.
- Default revised-ETA assumption for HS code mismatch: promised delivery
  date + 6 days, pending broker confirmation.
- Customer notification for `Breached` HS-code-mismatch cases: within 4
  business hours of breach detection.

## Exceptions and Edge Cases

- **Random compliance inspections** have no actionable remediation step
  (unlike HS code mismatches, there is no document to correct) — the
  case remains open for monitoring only, and escalation should focus on
  proactive customer communication rather than a false promise of
  active remediation.
- **Repeat HS code mismatches on the same SKU** across multiple orders
  should be escalated to product master data ownership (outside this
  SOP's scope) to fix the root classification, rather than corrected
  order-by-order indefinitely.
- **Destinations under active force majeure** (e.g., a customs shutdown
  event): follow the
  [Force Majeure & Exception Handling Policy](./12_force_majeure_exception_handling_policy.md)
  instead of the standard 2-business-day escalation trigger, since the
  delay is not attributable to a correctable paperwork issue.

## Revision and Effective Date

This SOP is the canonical reference for customs-hold handling and is
reviewed whenever a destination country materially changes its customs
documentation requirements. The SO-45892 worked example is kept current
as the flagship demonstration scenario and should not be altered without
updating the corresponding facts in the [SLA Policy](./01_sla_policy.md)
and [Escalation Matrix](./05_escalation_matrix.md).

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [SLA Policy](./01_sla_policy.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
