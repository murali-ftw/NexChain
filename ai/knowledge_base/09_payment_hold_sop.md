# Payment Hold SOP

## Purpose

Standard Operating Procedure for orders blocked or at risk due to
payment issues — a `payment.payment_status` of `Failed` or `Pending`
beyond the expected window, or an `invoice.invoice_status` of `Overdue`.

## Scope

Applies to any `sales_orders` linked to an `invoice` where:
- `invoice.invoice_status = 'Overdue'`, or
- The linked `payment.payment_status = 'Failed'`, or
- `payment.payment_status = 'Pending'` for longer than the customer's
  standard payment processing window (typically 2 business days for
  card/bank transfer, up to 5 business days for cheque).

## Step-by-Step Procedure

### 1. Confirm the Payment State

Check `invoice.invoice_status` and the linked `payment` row(s) for the
order via `invoice.order_id`. Note `payment_method` — resolution paths
differ by method.

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

## Related Documents

- [Order Amendment & Cancellation Policy](./10_order_amendment_cancellation_policy.md)
- [Customer Notification Policy](./06_customer_notification_policy.md)
