# Payment Hold SOP

## Purpose

Standard Operating Procedure for orders blocked or at risk due to
payment issues — a `payment.payment_status` of `Failed` or `Pending`
beyond the expected window, or an `invoice.invoice_status` of
`Overdue`. This SOP exists to make clear that payment-driven delay is
handled differently from operational delay: the customer, not NexChain,
controls resolution time, and the SLA clock reflects that.

## Scope and Applicability

Applies to any `sales_orders` linked to an `invoice` where:
- `invoice.invoice_status = 'Overdue'`, or
- The linked `payment.payment_status = 'Failed'`, or
- `payment.payment_status = 'Pending'` for longer than the customer's
  standard payment processing window (typically 2 business days for
  card/bank transfer, up to 5 business days for cheque).

Applies across all customer tiers and all `payment_method` values on
file. Does not apply to orders that have already dispatched before a
payment failure occurred — those are handled per Step 2's fulfillment
policy below, not recalled.

## Definitions / Key Terms

- **Overdue invoice** — an `invoice` whose payment was never attempted
  or completed within the expected window from `invoice_date`.
- **Failed payment** — a payment attempt that was declined or rejected
  by the payment gateway, bank, or card issuer.
- **Pending payment** — a payment attempt that has not yet cleared but
  has not been explicitly declined; some methods legitimately take
  several business days.
- **Credit terms agreement** — a pre-approved arrangement (tracked by
  Finance/Accounts Receivable, not in the core schema) allowing an
  order to dispatch despite an outstanding invoice.

## Roles and Responsibilities

- **Accounts Receivable** — owns payment-state confirmation (Step 1),
  overdue invoice follow-up (Step 4), and escalation past 5–10 business
  days.
- **Customer Support Agent** — notifies the customer of payment
  failures and requests an alternate method or retry (Step 3).
- **Finance** — approves credit terms exceptions to the default
  fulfillment policy.

## Step-by-Step Procedure

### 1. Confirm the Payment State

Check `invoice.invoice_status` and the linked `payment` row(s) for the
order via `invoice.order_id`. Note `payment_method` — resolution paths
differ by method. Accounts Receivable is the authoritative source for
payment-gateway-side detail not captured in the core schema (e.g. the
specific decline reason code).

### 2. Determine Fulfillment Policy

NexChain's default policy: **do not dispatch** an order while its
invoice is `Overdue` or the payment is `Failed`, unless the customer has
a pre-approved credit terms agreement on file (check with Finance/
Accounts Receivable — not tracked in the core schema). Orders already
`Dispatched` before a payment failure are not recalled; the payment
issue is resolved independently of the shipment.

### 3. Failed Payment

1. Notify the customer of the failure and the specific reason if the
   payment gateway/bank provided one (e.g. insufficient funds, card
   declined, cheque bounced).
2. Request an alternate payment method or a retry.
3. Hold order fulfillment until `payment_status = 'Completed'` on a
   replacement payment.
4. If unresolved after 5 business days, escalate to Accounts Receivable
   and consider order cancellation per the
   [Order Amendment & Cancellation Policy](./10_order_amendment_cancellation_policy.md).

### 4. Overdue Invoice (Payment Never Attempted)

1. Send a payment reminder referencing `invoice.invoice_no` and
   `amount`.
2. If the customer has open orders awaiting dispatch, hold them per the
   default policy above.
3. Escalate to Accounts Receivable if the invoice remains unpaid 10+
   business days past `invoice_date`.

### 5. Pending Payment Beyond Window

1. Check with the payment processor/bank for status (some methods, like
   bank transfer, can legitimately take 3–5 business days to clear).
2. If still pending beyond the expected window with no processor-side
   explanation, treat as a soft failure and follow the Failed Payment
   steps above.

### 6. Impact on Delivery SLA

A payment hold pauses the delivery SLA clock — `promised_delivery_date`
is not considered breached while an order is legitimately held for
payment reasons, since the customer controls resolution time.
`revised_delivery_date` should be recalculated as (payment resolution
date + normal fulfillment lead time) once payment clears, not treated as
a carrier/warehouse delay.

## Decision Criteria and Thresholds

- Standard payment processing window: 2 business days (card/bank
  transfer), up to 5 business days (cheque).
- Escalate to Accounts Receivable: 5 business days unresolved for a
  failed payment; 10 business days unresolved for an overdue invoice
  with no attempt.
- SLA clock: paused, not breached, while a payment hold is legitimately
  active.

## Exceptions and Edge Cases

- **Customer with a pre-approved credit terms agreement**: dispatch
  proceeds despite `Overdue` status per Finance's arrangement; this SOP
  still applies for tracking and eventual payment collection, but not
  for fulfillment blocking.
- **Payment fails after dispatch**: the shipment is not recalled;
  Accounts Receivable pursues payment collection independently while
  the shipment SOP (Shipment Delay, Customs Hold, etc.) continues
  unaffected.
- **Partial payment received**: treat as still `Pending`/`Failed` for
  fulfillment-blocking purposes unless Finance explicitly approves
  partial-payment dispatch under a specific customer agreement.

## Revision and Effective Date

Maintained jointly by Accounts Receivable and Finance; reviewed whenever
standard payment processing windows change (e.g., a new payment gateway
with different clearing times).

## Related Documents

- [Order Amendment & Cancellation Policy](./10_order_amendment_cancellation_policy.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
- [SLA Policy](./01_sla_policy.md)
