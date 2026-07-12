-- P2.2 completion gate, part 1: every table can be queried, relationships hold,
-- and CRUD works end to end.
--
--   psql -v ON_ERROR_STOP=1 -d nexchain -f db/verify_crud.sql
--
-- Leaves no data behind. Uses CUST-VERIFY/WH-VERIFY/SO-VERIFY-* codes so it
-- can run independently of db/seed_data.sql in either order without
-- colliding on unique codes. Roles are verified separately in db/verify_roles.sql.

-- 0. Every table in the frozen schema (docs/06_backend_schema.md §2) exists and
--    is queryable. Asserts rather than prints — a missing table fails the script.
DO $$
DECLARE
    expected TEXT[] := ARRAY['customers','warehouse','sales_orders','order_items','inventory',
                             'shipment','carrier_tracking','invoice','payment','sla_rules',
                             'knowledge_documents','knowledge_chunks','users','audit_log'];
    t TEXT;
    n BIGINT;
BEGIN
    FOREACH t IN ARRAY expected LOOP
        EXECUTE format('SELECT count(*) FROM %I', t) INTO n;
        RAISE NOTICE 'queryable: % (% rows)', t, n;
    END LOOP;
    RAISE NOTICE 'PASS: all % tables queryable', array_length(expected, 1);
END $$;

-- 1. Insert (Create)
INSERT INTO customers (customer_code, customer_name, contact_email, region, sla_tier)
VALUES ('CUST-VERIFY', 'Acme Corp', 'contact@acme.com', 'APAC', 'GOLD');

INSERT INTO warehouse (warehouse_code, warehouse_name, location)
VALUES ('WH-VERIFY', 'Chennai Main', 'Chennai');

INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date, current_status, total_amount)
VALUES ('SO-VERIFY-0001',
        (SELECT customer_id FROM customers WHERE customer_code = 'CUST-VERIFY'),
        (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-VERIFY'),
        CURRENT_DATE, CURRENT_DATE + INTERVAL '5 days', 'Pending', 500.00);

-- 2. Select (Read)
SELECT
    so.order_no,
    c.customer_name,
    w.location,
    so.current_status
FROM sales_orders so
JOIN customers c ON so.customer_id = c.customer_id
JOIN warehouse w ON so.warehouse_id = w.warehouse_id
WHERE so.order_no = 'SO-VERIFY-0001';

-- 3. Update
UPDATE sales_orders
SET current_status = 'Dispatched'
WHERE order_no = 'SO-VERIFY-0001';

SELECT order_no, current_status FROM sales_orders WHERE order_no = 'SO-VERIFY-0001';

-- 4. Referential integrity is actually enforced, not just declared: an order
--    pointing at a customer that doesn't exist must be rejected.
DO $$
BEGIN
    BEGIN
        INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date,
                                  promised_delivery_date, current_status, total_amount)
        VALUES ('SO-VERIFY-BOGUS', 999999, 999999, CURRENT_DATE, CURRENT_DATE, 'Pending', 1.00);
        RAISE EXCEPTION 'FAIL: sales_orders accepted a non-existent customer_id/warehouse_id';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'PASS: foreign keys enforced on sales_orders';
    END;

    BEGIN
        DELETE FROM customers WHERE customer_code = 'CUST-VERIFY';
        RAISE EXCEPTION 'FAIL: deleted a customer that still has orders';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'PASS: child orders block customer deletion';
    END;
END $$;

-- 5. Delete (children first, per the FK direction verified above)
DELETE FROM sales_orders WHERE order_no = 'SO-VERIFY-0001';
DELETE FROM warehouse WHERE warehouse_code = 'WH-VERIFY';
DELETE FROM customers WHERE customer_code = 'CUST-VERIFY';
