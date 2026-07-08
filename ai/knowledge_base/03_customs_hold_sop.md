# Customs Hold SOP

## Purpose

Standard Operating Procedure for shipments placed on `Customs Hold`
(`shipment.shipment_status = 'Customs Hold'`), including the most common
cause seen in NexChain's export lanes: an **HS code mismatch during
customs validation**. This SOP directly supports the SO-45892 flagship
scenario referenced throughout the knowledge base and the SLA Policy.

## Scope

Applies to any shipment where `shipment_status = 'Customs Hold'`,
typically surfaced alongside a `delay_reason` describing the specific
customs issue and a `current_location` at a port or customs facility
(e.g. "Chennai Port").

## Common Cause: HS Code Mismatch During Customs Validation

### What it means

The Harmonized System (HS) code declared on the commercial invoice or
shipping manifest does not match the HS code customs authorities
associate with the declared goods category. Customs will not clear the
shipment until the discrepancy is resolved, because the HS code
determines duty rate, import eligibility, and regulatory classification.

### Why it happens

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
   `product_name` for every line item on the affected order.
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

## Related Documents

- [Shipment Delay SOP](./02_shipment_delay_sop.md)
- [SLA Policy](./01_sla_policy.md)
- [Escalation Matrix](./05_escalation_matrix.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
