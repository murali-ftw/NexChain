# Knowledge Base Index

Manifest of all enterprise knowledge documents prepared for RAG
ingestion (P3.2, Day 2; content depth revised Day 3 per P3.3 audit
fix). This is the source list the Day 3 (P3.3) ingestion pipeline reads
to populate the ChromaDB vector store (`ai/chroma_db/`).

Each row's **doc_type** matches the `knowledge_documents.doc_type`
CHECK-style comment in `db/migrations/001_init_schema.sql`
(`SOP, SLA, POLICY`). **source_path** is the intended
`knowledge_documents.source_path` value, relative to the repo root.
Table shape is intentionally unchanged (5 columns) — `ai/rag/loader.py`
parses this exact column layout, so a finer-grained category (SOP /
POLICY / MATRIX) is called out in each description instead of as a
separate column.

| # | Title | doc_type | source_path | Description |
|---|---|---|---|---|
| 1 | SLA Policy | SLA | `ai/knowledge_base/01_sla_policy.md` | [POLICY] Defines STANDARD/GOLD/PLATINUM tiers, `max_delay_days` thresholds, breach determination logic, and escalation roles, with the SO-45892 worked example. |
| 2 | Shipment Delay SOP | SOP | `ai/knowledge_base/02_shipment_delay_sop.md` | [SOP] General-purpose delay detection, diagnosis, ETA revision, and escalation procedure; entry point to cause-specific SOPs. |
| 3 | Customs Hold SOP | SOP | `ai/knowledge_base/03_customs_hold_sop.md` | [SOP] Flagship document: HS code mismatch during customs validation (SO-45892 case) in full operational depth - detection, notification, remediation, resolution time, revised-ETA communication - plus other customs hold causes. |
| 4 | Inventory Shortage SOP | SOP | `ai/knowledge_base/04_inventory_shortage_sop.md` | [SOP] Procedure for orders blocked by insufficient `inventory.quantity_on_hand`, including alternate-warehouse, partial-fulfillment, and replenishment paths. |
| 5 | Escalation Matrix | POLICY | `ai/knowledge_base/05_escalation_matrix.md` | [MATRIX] Reference matrix mapping delay severity and SLA tier to escalation role, paging, and expected response time; not a step-by-step procedure. |
| 6 | Customer Notification Policy | POLICY | `ai/knowledge_base/06_customer_notification_policy.md` | [POLICY] When/how customers are notified of At Risk, Breached, and resolved statuses, including internal-to-customer-facing language translation. |
| 7 | Warehouse Delay SOP | SOP | `ai/knowledge_base/07_warehouse_delay_sop.md` | [SOP] Procedure for picking/packing/QC/staffing delays at the fulfilling warehouse. |
| 8 | Carrier Delay Handling SOP | SOP | `ai/knowledge_base/08_carrier_delay_handling_sop.md` | [SOP] Procedure for post-dispatch carrier-side delays (weather, capacity, mis-route, lost-in-transit). |
| 9 | Payment Hold SOP | SOP | `ai/knowledge_base/09_payment_hold_sop.md` | [SOP] Procedure for orders blocked by failed/pending payment or overdue invoices; SLA clock-pause rule. |
| 10 | Order Amendment & Cancellation Policy | POLICY | `ai/knowledge_base/10_order_amendment_cancellation_policy.md` | [POLICY] Amendment windows by order stage and the cancellation/refund procedure. |
| 11 | Returns / RMA SOP | SOP | `ai/knowledge_base/11_returns_rma_sop.md` | [SOP] Post-delivery return/replacement/refund procedure and tier-differentiated eligibility windows. |
| 12 | Force Majeure & Exception Handling Policy | POLICY | `ai/knowledge_base/12_force_majeure_exception_handling_policy.md` | [POLICY] Defines qualifying disruption events and how affected orders are exempted from standard SLA escalation while still tracked internally. |

## Notes for Day 3 Ingestion (P3.3)

- Each document uses one H1 title and multiple H2 sections — suitable
  chunk boundaries are the H2 sections (matches the `section` metadata
  field called for in `docs/02_technical_requirements.md` §6:
  `doc_id`, `title`, `section`, `source_path`).
- Cross-references between documents use relative markdown links
  (`./NN_name.md`) — preserve these as `related_docs` metadata or strip
  them during chunking, per the ingestion design.
- Terminology (table names, SLA tiers, status strings, escalation
  roles) is kept consistent with `ai/contracts.py` and
  `docs/06_backend_schema.md` throughout; no new status vocabulary was
  introduced. SOP prose never references `users`, `audit_log`,
  `knowledge_documents`, or `knowledge_chunks` — only the 10-table
  Text-to-SQL allowlist in `ai/contracts.py`.
- Every document was expanded on Day 3 (P3.3 audit fix) to ~1,200–2,000
  words of genuine operational content — scope, definitions, trigger
  conditions, named responsible roles, decision thresholds, exceptions,
  and a revision/effective-date line — so each naturally chunks into
  multiple 500–800 token chunks with overlap, instead of one undersized
  chunk per document. None are a placeholder or padded filler; the
  Escalation Matrix (#5) is deliberately reference-heavy by nature (it
  governs notification/ownership, not remediation steps) but was still
  expanded with genuine paging, template, and review-process content
  rather than left artificially short.
- This manifest does not create `knowledge_documents` or
  `knowledge_chunks` rows in Postgres — P3.3 scope is the ChromaDB
  vector store only (see `ai/rag/README.md`).
