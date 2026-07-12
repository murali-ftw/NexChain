-- P2.3 Realistic Dummy Data — docs/06_backend_schema.md §7 seed guidance,
-- docs/team_plan.md P2.3 gate: >= 10 predefined business scenarios queryable.
--
--   psql -v ON_ERROR_STOP=1 -d nexchain -f db/seed_data.sql
--   psql -v ON_ERROR_STOP=1 -d nexchain -f db/verify_scenarios.sql   # proves the gate
--
-- Idempotent: truncates and rebuilds the 10 Text-to-SQL-allowlisted tables
-- (ai/contracts.py SQL_TABLE_ALLOWLIST) every run. Never touches users or
-- audit_log. Dates for non-fixed scenarios are relative to CURRENT_DATE so
-- "N days delayed" stays true no matter when this is run; the flagship order
-- keeps the exact fixed dates the whole team's mocks already assume.
BEGIN;

TRUNCATE customers, warehouse, sales_orders, order_items, inventory,
         shipment, carrier_tracking, invoice, payment, sla_rules
    RESTART IDENTITY CASCADE;

-- 1. Warehouses (3, includes Chennai per seed guidance)
INSERT INTO warehouse (warehouse_code, warehouse_name, location, address) VALUES
 ('WH-CHN', 'Chennai Main', 'Chennai', '14 Harbour Estate Road, Chennai 600001'),
 ('WH-BLR', 'Bangalore Hub', 'Bangalore', '221 Electronics City Phase 1, Bangalore 560100'),
 ('WH-BOM', 'Mumbai Port Warehouse', 'Mumbai', '9 Dockyard Road, Mumbai 400010');

-- 2. Customers (6, spanning all three SLA tiers)
INSERT INTO customers (customer_code, customer_name, contact_email, contact_phone, region, sla_tier) VALUES
 ('CUST-001', 'Acme Industries', 'ops@acmeindustries.example', '+91-44-2345-6789', 'APAC', 'GOLD'),
 ('CUST-002', 'Bluewave Retail', 'supply@bluewaveretail.example', '+91-44-3456-7890', 'APAC', 'STANDARD'),
 ('CUST-003', 'Continental Traders', 'procurement@continentaltraders.example', '+44-20-7946-0958', 'EMEA', 'STANDARD'),
 ('CUST-004', 'Delta Manufacturing', 'logistics@deltamfg.example', '+91-80-4567-8901', 'APAC', 'PLATINUM'),
 ('CUST-005', 'Everline Logistics', 'orders@everline.example', '+49-30-1234-5678', 'EMEA', 'GOLD'),
 ('CUST-006', 'Frontier Exports', 'contact@frontierexports.example', '+1-212-555-0148', 'AMER', 'STANDARD');

-- 3. SLA rules — exact tiers/roles from ai/knowledge_base/01_sla_policy.md and
--    05_escalation_matrix.md, so Business Rule Agent output matches KB prose.
INSERT INTO sla_rules (sla_tier, max_delay_days, escalation_role, description) VALUES
 ('STANDARD', 3, 'Logistics Coordinator', 'Standard-contract customers, no premium SLA add-on.'),
 ('GOLD', 5, 'Logistics Manager', 'Mid-tier accounts with a negotiated delivery guarantee.'),
 ('PLATINUM', 7, 'Regional Operations Director', 'Strategic / enterprise accounts with contractual delivery guarantees.');

-- 4. Inventory (10 SKUs). SKU-1001's 240-units-at-Chennai figure matches the
--    existing Spring Boot mock (ChatService.java) and Angular fixture
--    (chat-fixtures.ts INVENTORY_RESPONSE) so the real data agrees with the
--    demo the rest of the team already built against. SKU-1006 is
--    deliberately near-empty for the inventory-shortage scenario below.
INSERT INTO inventory (sku, product_name, warehouse_id, quantity_on_hand, quantity_reserved, reorder_level) VALUES
 ('SKU-1001', 'Widget Type A', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'), 240, 40, 50),
 ('SKU-1002', 'Widget Type B', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'), 500, 60, 100),
 ('SKU-1003', 'Steel Bracket Assembly', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BLR'), 150, 20, 40),
 ('SKU-1004', 'Industrial Sensor Kit', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BLR'), 80, 10, 30),
 ('SKU-1005', 'Hydraulic Valve Unit', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BOM'), 300, 45, 60),
 ('SKU-1006', 'Precision Bearing Set', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'), 5, 2, 50),
 ('SKU-1007', 'Control Panel Module', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BOM'), 120, 15, 40),
 ('SKU-1008', 'Conveyor Belt Segment', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BLR'), 200, 25, 50),
 ('SKU-1009', 'Packaging Carton Bulk', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'), 1000, 100, 200),
 ('SKU-1010', 'Circuit Board Rev C', (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BOM'), 60, 8, 25);

-- ---------------------------------------------------------------------------
-- 5. Named scenario orders — each is one of the >=10 predefined business
--    scenarios the P2.3 gate requires, covering every category team_plan.md
--    names: on-time, shortage, customs hold, payment hold, carrier delay,
--    warehouse delay, SLA breach. db/verify_scenarios.sql asserts each one.
-- ---------------------------------------------------------------------------

-- 5a. SO-45892 — the flagship scenario (problem_statement.md §7). Fixed dates:
--     GOLD customer so escalation_role = 'Logistics Manager', matching the
--     recommended action every mock in the repo already gives.
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          revised_delivery_date, current_status, total_amount) VALUES
 ('SO-45892',
  (SELECT customer_id FROM customers WHERE customer_code = 'CUST-001'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'),
  DATE '2026-06-20', DATE '2026-07-03', DATE '2026-07-09', 'Delayed', 4200.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-45892'), 'SKU-1001', 'Widget Type A', 10, 150.00),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-45892'), 'SKU-1002', 'Widget Type B', 27, 100.00);

INSERT INTO shipment (order_id, tracking_no, carrier_name, dispatch_date, current_location,
                      shipment_status, delay_reason) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-45892'), 'TRK-45892-1', 'BlueDart Global',
  DATE '2026-06-25', 'Chennai Port', 'Customs Hold', 'HS code mismatch during customs validation.');

INSERT INTO carrier_tracking (shipment_id, event_timestamp, event_location, event_status, raw_payload) VALUES
 ((SELECT shipment_id FROM shipment WHERE tracking_no = 'TRK-45892-1'),
  TIMESTAMP '2026-06-25 09:00:00', 'Chennai Warehouse', 'Dispatched from warehouse', '{"source": "carrier_api", "code": "DISPATCHED"}'),
 ((SELECT shipment_id FROM shipment WHERE tracking_no = 'TRK-45892-1'),
  TIMESTAMP '2026-06-26 14:30:00', 'Chennai Port', 'Arrived at port', '{"source": "carrier_api", "code": "ARRIVED_PORT"}'),
 ((SELECT shipment_id FROM shipment WHERE tracking_no = 'TRK-45892-1'),
  TIMESTAMP '2026-07-04 11:15:00', 'Chennai Port', 'Customs hold - HS code mismatch', '{"source": "carrier_api", "code": "CUSTOMS_HOLD"}');

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-45892'), 'INV-45892', DATE '2026-06-21', 4200.00, 'Sent');

INSERT INTO payment (invoice_id, payment_date, amount_paid, payment_method, payment_status) VALUES
 ((SELECT invoice_id FROM invoice WHERE invoice_no = 'INV-45892'), NULL, 0.00, NULL, 'Pending');

-- 5b-5e. Reporting scenario — the four Chennai delayed orders Person 1's
-- ChatService/chat-fixtures already hardcode ("4 orders from the Chennai
-- warehouse are currently delayed: SO-10241 (2 days), SO-10288 (5 days),
-- SO-10299 (1 day), SO-10310 (3 days)"). Dates are CURRENT_DATE-relative so
-- the delay-day counts stay correct regardless of when this seed runs.
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-10241', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-002'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'),
  CURRENT_DATE - 12, CURRENT_DATE - 2, 'Delayed', 860.00),
 ('SO-10288', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-003'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'),
  CURRENT_DATE - 15, CURRENT_DATE - 5, 'Delayed', 1450.00),
 ('SO-10299', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-006'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'),
  CURRENT_DATE - 11, CURRENT_DATE - 1, 'Delayed', 320.00),
 ('SO-10310', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-002'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'),
  CURRENT_DATE - 13, CURRENT_DATE - 3, 'Delayed', 990.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10241'), 'SKU-1003', 'Steel Bracket Assembly', 4, 215.00),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10288'), 'SKU-1005', 'Hydraulic Valve Unit', 5, 290.00),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10299'), 'SKU-1002', 'Widget Type B', 3, 106.67),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10310'), 'SKU-1008', 'Conveyor Belt Segment', 6, 165.00);

INSERT INTO shipment (order_id, tracking_no, carrier_name, dispatch_date, current_location, shipment_status, delay_reason) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10241'), 'TRK-10241-1', 'Delhivery Freight',
  CURRENT_DATE - 8, 'Bangalore Hub', 'In Transit', 'Minor routing delay via secondary hub.'),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10288'), 'TRK-10288-1', 'BlueDart Global',
  CURRENT_DATE - 11, 'Chennai Port', 'In Transit', 'Carrier congestion at destination hub.'),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10299'), 'TRK-10299-1', 'Delhivery Freight',
  CURRENT_DATE - 7, 'Chennai Warehouse', 'Dispatched', 'Awaiting final-mile carrier pickup.'),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10310'), 'TRK-10310-1', 'FedEx Cargo',
  CURRENT_DATE - 9, 'Chennai Port', 'In Transit', 'Documentation review in progress.');

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10241'), 'INV-10241', CURRENT_DATE - 11, 860.00, 'Sent'),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10288'), 'INV-10288', CURRENT_DATE - 14, 1450.00, 'Sent'),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10299'), 'INV-10299', CURRENT_DATE - 10, 320.00, 'Sent'),
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-10310'), 'INV-10310', CURRENT_DATE - 12, 990.00, 'Sent');

-- 5f. On-time delivered order (PLATINUM tier).
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-30001', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-004'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BLR'),
  CURRENT_DATE - 20, CURRENT_DATE - 10, 'Delivered', 2150.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30001'), 'SKU-1004', 'Industrial Sensor Kit', 10, 215.00);

INSERT INTO shipment (order_id, tracking_no, carrier_name, dispatch_date, current_location, shipment_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30001'), 'TRK-30001-1', 'Delhivery Freight',
  CURRENT_DATE - 15, 'Delivered to customer', 'Delivered');

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30001'), 'INV-30001', CURRENT_DATE - 19, 2150.00, 'Paid');

INSERT INTO payment (invoice_id, payment_date, amount_paid, payment_method, payment_status) VALUES
 ((SELECT invoice_id FROM invoice WHERE invoice_no = 'INV-30001'), CURRENT_DATE - 18, 2150.00, 'Bank Transfer', 'Completed');

-- 5g. Inventory shortage — SKU-1006 has only 5 units on hand, order wants 50.
--     Blocked pre-dispatch, per ai/knowledge_base/04_inventory_shortage_sop.md.
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-30002', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-005'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'),
  CURRENT_DATE - 3, CURRENT_DATE + 5, 'Pending', 5000.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30002'), 'SKU-1006', 'Precision Bearing Set', 50, 100.00);

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30002'), 'INV-30002', CURRENT_DATE - 2, 5000.00, 'Draft');

-- 5h. Payment hold — overdue invoice, failed payment, blocked pre-dispatch
--     per ai/knowledge_base/09_payment_hold_sop.md's SLA clock-pause rule.
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-30003', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-002'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BOM'),
  CURRENT_DATE - 10, CURRENT_DATE - 4, 'Pending', 1780.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30003'), 'SKU-1007', 'Control Panel Module', 4, 445.00);

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30003'), 'INV-30003', CURRENT_DATE - 9, 1780.00, 'Overdue');

INSERT INTO payment (invoice_id, payment_date, amount_paid, payment_method, payment_status) VALUES
 ((SELECT invoice_id FROM invoice WHERE invoice_no = 'INV-30003'), CURRENT_DATE - 6, 0.00, 'Card', 'Failed');

-- 5i. Carrier delay — dispatched, in transit, delayed by the carrier
--     post-dispatch, per ai/knowledge_base/08_carrier_delay_handling_sop.md.
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-30004', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-006'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BLR'),
  CURRENT_DATE - 9, CURRENT_DATE - 1, 'Delayed', 660.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30004'), 'SKU-1008', 'Conveyor Belt Segment', 4, 165.00);

INSERT INTO shipment (order_id, tracking_no, carrier_name, dispatch_date, current_location, shipment_status, delay_reason) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30004'), 'TRK-30004-1', 'FedEx Cargo',
  CURRENT_DATE - 6, 'Regional Transit Hub - Hyderabad', 'In Transit',
  'Carrier capacity constraint causing multi-day transit delay.');

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30004'), 'INV-30004', CURRENT_DATE - 8, 660.00, 'Sent');

-- 5j. Warehouse delay — never dispatched, blocked by picking/QC/staffing
--     backlog at the fulfilling warehouse itself, per
--     ai/knowledge_base/07_warehouse_delay_sop.md.
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-30005', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-003'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BOM'),
  CURRENT_DATE - 8, CURRENT_DATE - 2, 'Delayed', 1140.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30005'), 'SKU-1010', 'Circuit Board Rev C', 12, 95.00);

INSERT INTO shipment (order_id, tracking_no, carrier_name, dispatch_date, current_location, shipment_status, delay_reason) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30005'), 'TRK-30005-1', NULL,
  NULL, 'Mumbai Port Warehouse', 'Delayed', 'Picking and QC backlog at fulfilling warehouse.');

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30005'), 'INV-30005', CURRENT_DATE - 7, 1140.00, 'Sent');

-- 5k. Cancelled order — never invoiced.
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-30006', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-001'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'),
  CURRENT_DATE - 5, CURRENT_DATE + 3, 'Cancelled', 480.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30006'), 'SKU-1009', 'Packaging Carton Bulk', 40, 12.00);

-- 5l. PLATINUM tier at-risk — 4 days late against a 7-day threshold, so it
--     stays At Risk rather than Breached (tier-tolerance edge case).
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount) VALUES
 ('SO-30007', (SELECT customer_id FROM customers WHERE customer_code = 'CUST-004'),
  (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-BLR'),
  CURRENT_DATE - 14, CURRENT_DATE - 4, 'Delayed', 3200.00);

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30007'), 'SKU-1005', 'Hydraulic Valve Unit', 8, 400.00);

INSERT INTO shipment (order_id, tracking_no, carrier_name, dispatch_date, current_location, shipment_status, delay_reason) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30007'), 'TRK-30007-1', 'BlueDart Global',
  CURRENT_DATE - 10, 'Chennai Port', 'In Transit', 'Awaiting customs clearance documentation.');

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status) VALUES
 ((SELECT order_id FROM sales_orders WHERE order_no = 'SO-30007'), 'INV-30007', CURRENT_DATE - 13, 3200.00, 'Sent');

-- ---------------------------------------------------------------------------
-- 6. Filler orders — bulk realistic volume so the table isn't just the named
--    scenarios (team_plan.md P2.3 calls for 30-50 sales_orders total).
--    Deterministic (no random()) so reruns are reproducible; the same g-based
--    formula is repeated in each INSERT so items/shipment/invoice values agree
--    with the order they belong to.
-- ---------------------------------------------------------------------------
INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date,
                          current_status, total_amount)
SELECT
    'SO-2' || lpad(g::text, 4, '0'),
    1 + (g % 6),
    1 + (g % 3),
    CASE (g % 7)
        WHEN 3 THEN CURRENT_DATE - (10 + g)              -- Delivered: safely in the past
        WHEN 5 THEN CURRENT_DATE - (10 + g)              -- Cancelled: also in the past
        WHEN 6 THEN CURRENT_DATE - (1 + (g % 4)) - 10    -- Delayed: order placed 10 days before promised
        ELSE CURRENT_DATE + (1 + (g % 14)) - 10          -- Pending/Dispatched/In Transit: order placed 10 days before promised
    END,
    CASE (g % 7)
        WHEN 3 THEN CURRENT_DATE - (10 + g)
        WHEN 5 THEN CURRENT_DATE + (g % 10)
        WHEN 6 THEN CURRENT_DATE - (1 + (g % 4))
        ELSE CURRENT_DATE + (1 + (g % 14))
    END,
    (ARRAY['Pending', 'Dispatched', 'In Transit', 'Delivered', 'Pending', 'Cancelled', 'Delayed'])[1 + (g % 7)],
    (25.00 + ((g * 17) % 475)) * (2 + (g % 15))
FROM generate_series(1, 23) AS g;

INSERT INTO order_items (order_id, sku, product_name, quantity, unit_price)
SELECT
    so.order_id,
    (ARRAY['SKU-1001','SKU-1002','SKU-1003','SKU-1004','SKU-1005',
           'SKU-1006','SKU-1007','SKU-1008','SKU-1009','SKU-1010'])[1 + (g % 10)],
    (ARRAY['Widget Type A','Widget Type B','Steel Bracket Assembly','Industrial Sensor Kit','Hydraulic Valve Unit',
           'Precision Bearing Set','Control Panel Module','Conveyor Belt Segment','Packaging Carton Bulk','Circuit Board Rev C'])[1 + (g % 10)],
    2 + (g % 15),
    25.00 + ((g * 17) % 475)
FROM generate_series(1, 23) AS g
JOIN sales_orders so ON so.order_no = 'SO-2' || lpad(g::text, 4, '0');

INSERT INTO shipment (order_id, tracking_no, carrier_name, dispatch_date, current_location, shipment_status, delay_reason)
SELECT
    so.order_id,
    'TRK-2' || lpad(g::text, 4, '0') || '-1',
    (ARRAY['BlueDart Global', 'Delhivery Freight', 'FedEx Cargo'])[1 + (g % 3)],
    CASE WHEN so.current_status IN ('Dispatched', 'In Transit', 'Delivered', 'Delayed')
         THEN so.order_date + 5 END,
    CASE so.current_status
        WHEN 'Delivered' THEN 'Delivered to customer'
        ELSE (ARRAY['Chennai Port', 'Bangalore Hub', 'Mumbai Port Warehouse', 'Regional Transit Hub - Hyderabad'])[1 + (g % 4)]
    END,
    so.current_status,
    CASE WHEN so.current_status = 'Delayed' THEN 'Delay reason under review.' END
FROM generate_series(1, 23) AS g
JOIN sales_orders so ON so.order_no = 'SO-2' || lpad(g::text, 4, '0')
WHERE so.current_status IN ('Dispatched', 'In Transit', 'Delivered', 'Delayed');

INSERT INTO invoice (order_id, invoice_no, invoice_date, amount, invoice_status)
SELECT
    so.order_id,
    'INV-2' || lpad(g::text, 4, '0'),
    so.order_date + 1,
    so.total_amount,
    CASE so.current_status WHEN 'Delivered' THEN 'Paid' ELSE 'Sent' END
FROM generate_series(1, 23) AS g
JOIN sales_orders so ON so.order_no = 'SO-2' || lpad(g::text, 4, '0')
WHERE so.current_status <> 'Cancelled';

INSERT INTO payment (invoice_id, payment_date, amount_paid, payment_method, payment_status)
SELECT inv.invoice_id, so.promised_delivery_date, inv.amount, 'Bank Transfer', 'Completed'
FROM invoice inv
JOIN sales_orders so ON so.order_id = inv.order_id
WHERE inv.invoice_status = 'Paid' AND so.order_no LIKE 'SO-2%';

COMMIT;
