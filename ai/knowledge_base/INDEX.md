# Knowledge Base Index

Manifest of all enterprise knowledge documents prepared for RAG
ingestion (P3.2, Day 2). This is the source list the Day 3 (P3.3)
ingestion pipeline reads to populate `knowledge_documents` and
`knowledge_chunks`.

Each row's **doc_type** matches the `knowledge_documents.doc_type`
CHECK-style comment in `db/migrations/001_init_schema.sql`
(`SOP, SLA, POLICY`). **source_path** is the intended
`knowledge_documents.source_path` value, relative to the repo root.

| # | Title | doc_type | source_path | Description |
|---|---|---|---|---|
| 1 | SLA Policy | SLA | `ai/knowledge_base/01_sla_policy.md` | Defines STANDARD/GOLD/PLATINUM tiers, `max_delay_days` thresholds, breach determination logic, and escalation roles. |
| 2 | Shipment Delay SOP | SOP | `ai/knowledge_base/02_shipment_delay_sop.md` | General-purpose delay detection, diagnosis, ETA revision, and escalation procedure; entry point to cause-specific SOPs. |
| 3 | Customs Hold SOP | SOP | `ai/knowledge_base/03_customs_hold_sop.md` | Covers HS code mismatch during customs validation (SO-45892 flagship case) plus other customs hold causes and resolution times. |
| 4 | Inventory Shortage SOP | SOP | `ai/knowledge_base/04_inventory_shortage_sop.md` | Procedure for orders blocked by insufficient `inventory.quantity_on_hand`, including alternate-warehouse and replenishment paths. |
| 5 | Escalation Matrix | POLICY | `ai/knowledge_base/05_escalation_matrix.md` | Maps delay severity and SLA tier to escalation role and expected response time. |
| 6 | Customer Notification Policy | POLICY | `ai/knowledge_base/06_customer_notification_policy.md` | When/how customers are notified of At Risk, Breached, and resolved statuses. |
| 7 | Warehouse Delay SOP | SOP | `ai/knowledge_base/07_warehouse_delay_sop.md` | Procedure for picking/packing/QC/staffing delays at the fulfilling warehouse. |
| 8 | Carrier Delay Handling SOP | SOP | `ai/knowledge_base/08_carrier_delay_handling_sop.md` | Procedure for post-dispatch carrier-side delays (weather, capacity, mis-route, lost-in-transit). |
| 9 | Payment Hold SOP | SOP | `ai/knowledge_base/09_payment_hold_sop.md` | Procedure for orders blocked by failed/pending payment or overdue invoices. |
| 10 | Order Amendment & Cancellation Policy | POLICY | `ai/knowledge_base/10_order_amendment_cancellation_policy.md` | Amendment windows by order stage and the cancellation/refund procedure. |
| 11 | Returns / RMA SOP | SOP | `ai/knowledge_base/11_returns_rma_sop.md` | Post-delivery return/replacement/refund procedure and eligibility windows. |
| 12 | Force Majeure & Exception Handling Policy | POLICY | `ai/knowledge_base/12_force_majeure_exception_handling_policy.md` | Defines qualifying disruption events and how affected orders are exempted from standard SLA escalation. |

## Notes for Day 3 Ingestion (P3.3)

- Each document uses one H1 title and multiple H2 sections — suitable
  chunk boundaries are the H2 sections (matches the `section` metadata
  field called for in `docs/02_technical_requirements.md` §5.2:
  `doc_id`, `title`, `section`, `source_path`).
- Cross-references between documents use relative markdown links
  (`./NN_name.md`) — preserve these as `related_docs` metadata or strip
  them during chunking, per the ingestion design.
- Terminology (table names, SLA tiers, status strings, escalation
  roles) is kept consistent with `ai/contracts.py` and
  `docs/06_backend_schema.md` throughout; no new status vocabulary was
  introduced.
- This manifest does not create `knowledge_documents` or
  `knowledge_chunks` rows — that is Day 3 (P3.3) ingestion pipeline
  work, out of scope for P3.2.
