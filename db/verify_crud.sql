-- Test CRUD operations and verify relationships

-- 1. Insert (Create)
INSERT INTO customers (customer_code, customer_name, contact_email, region, sla_tier) 
VALUES ('CUST-001', 'Acme Corp', 'contact@acme.com', 'APAC', 'GOLD');

INSERT INTO warehouse (warehouse_code, warehouse_name, location) 
VALUES ('WH-CHN', 'Chennai Main', 'Chennai');

INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, promised_delivery_date, current_status, total_amount) 
VALUES ('SO-10001', 
        (SELECT customer_id FROM customers WHERE customer_code = 'CUST-001'), 
        (SELECT warehouse_id FROM warehouse WHERE warehouse_code = 'WH-CHN'), 
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
WHERE so.order_no = 'SO-10001';

-- 3. Update
UPDATE sales_orders 
SET current_status = 'Dispatched' 
WHERE order_no = 'SO-10001';

SELECT order_no, current_status FROM sales_orders WHERE order_no = 'SO-10001';

-- 4. Delete (Verify constraint cleanup if needed, but here we just delete in order)
DELETE FROM sales_orders WHERE order_no = 'SO-10001';
DELETE FROM warehouse WHERE warehouse_code = 'WH-CHN';
DELETE FROM customers WHERE customer_code = 'CUST-001';
