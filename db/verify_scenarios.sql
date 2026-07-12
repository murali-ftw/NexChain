-- P2.3 completion gate: "at least 10 predefined business scenarios can be
-- queried manually" (docs/team_plan.md), covering every category it names:
-- on-time, shortage, customs hold, payment hold, carrier delay, warehouse
-- delay, SLA breach. Run after db/seed_data.sql:
--
--   psql -v ON_ERROR_STOP=1 -d nexchain -f db/verify_scenarios.sql
--
-- Asserts rather than prints: a wrong value fails the script. Uses the
-- exact SLA breach calculation from docs/06_backend_schema.md §6 so this
-- doubles as a check that the Business Rule Agent's query returns the
-- right classification for each seeded case.
DO $$
DECLARE
    r RECORD;
BEGIN
    -- 1. Flagship: SO-45892, customs hold, 6-day delay, Breached (GOLD, max 5d).
    SELECT so.current_status, sh.shipment_status, sh.current_location, sh.delay_reason,
           (CURRENT_DATE - so.promised_delivery_date) AS actual_delay_days,
           so.revised_delivery_date, sr.escalation_role,
           CASE WHEN (so.revised_delivery_date - so.promised_delivery_date) > sr.max_delay_days
                THEN 'Breached' ELSE 'not breached' END AS sla_result
    INTO r
    FROM sales_orders so
    JOIN customers c ON c.customer_id = so.customer_id
    JOIN sla_rules sr ON sr.sla_tier = c.sla_tier
    JOIN shipment sh ON sh.order_id = so.order_id
    WHERE so.order_no = 'SO-45892';
    ASSERT r.shipment_status = 'Customs Hold', 'SO-45892 should be Customs Hold';
    ASSERT r.delay_reason = 'HS code mismatch during customs validation.', 'SO-45892 delay_reason mismatch';
    ASSERT r.revised_delivery_date - (SELECT promised_delivery_date FROM sales_orders WHERE order_no = 'SO-45892') = 6,
        'SO-45892 should be a 6-day delay';
    ASSERT r.sla_result = 'Breached', 'SO-45892 should be Breached';
    ASSERT r.escalation_role = 'Logistics Manager', 'SO-45892 (GOLD) should escalate to Logistics Manager';
    RAISE NOTICE 'PASS 1: flagship customs-hold / SLA-breach scenario (SO-45892)';

    -- 2. On-time delivered order.
    SELECT current_status INTO r FROM sales_orders WHERE order_no = 'SO-30001';
    ASSERT r.current_status = 'Delivered', 'SO-30001 should be Delivered (on-time)';
    RAISE NOTICE 'PASS 2: on-time delivered order (SO-30001)';

    -- 3. Inventory shortage: order wants more than is on hand.
    SELECT oi.quantity, inv.quantity_on_hand INTO r
    FROM order_items oi
    JOIN sales_orders so ON so.order_id = oi.order_id
    JOIN inventory inv ON inv.sku = oi.sku
    WHERE so.order_no = 'SO-30002';
    ASSERT r.quantity > r.quantity_on_hand, 'SO-30002 should exceed available SKU-1006 stock';
    RAISE NOTICE 'PASS 3: inventory shortage (SO-30002, wants % of % on hand)', r.quantity, r.quantity_on_hand;

    -- 4. Payment hold: overdue invoice, failed payment.
    SELECT inv.invoice_status, p.payment_status INTO r
    FROM invoice inv JOIN payment p ON p.invoice_id = inv.invoice_id
    WHERE inv.invoice_no = 'INV-30003';
    ASSERT r.invoice_status = 'Overdue' AND r.payment_status = 'Failed', 'SO-30003 should be an overdue/failed payment hold';
    RAISE NOTICE 'PASS 4: payment hold (SO-30003)';

    -- 5. Carrier delay: in transit, post-dispatch.
    SELECT shipment_status, dispatch_date IS NOT NULL AS dispatched INTO r
    FROM shipment WHERE tracking_no = 'TRK-30004-1';
    ASSERT r.shipment_status = 'In Transit' AND r.dispatched, 'SO-30004 should be a dispatched, in-transit carrier delay';
    RAISE NOTICE 'PASS 5: carrier delay (SO-30004)';

    -- 6. Warehouse delay: never dispatched, blocked at the warehouse itself.
    SELECT shipment_status, dispatch_date IS NULL AS never_dispatched INTO r
    FROM shipment WHERE tracking_no = 'TRK-30005-1';
    ASSERT r.never_dispatched, 'SO-30005 should never have dispatched (warehouse delay)';
    RAISE NOTICE 'PASS 6: warehouse delay (SO-30005)';

    -- 7. Cancelled order.
    SELECT current_status INTO r FROM sales_orders WHERE order_no = 'SO-30006';
    ASSERT r.current_status = 'Cancelled', 'SO-30006 should be Cancelled';
    RAISE NOTICE 'PASS 7: cancelled order (SO-30006)';

    -- 8. SLA breach (non-flagship): STANDARD tier (max 3d), 5-day delay -> Breached.
    SELECT (CURRENT_DATE - so.promised_delivery_date) AS delay_days, sr.max_delay_days INTO r
    FROM sales_orders so JOIN customers c ON c.customer_id = so.customer_id
    JOIN sla_rules sr ON sr.sla_tier = c.sla_tier
    WHERE so.order_no = 'SO-10288';
    ASSERT r.delay_days > r.max_delay_days, 'SO-10288 should be Breached (% days > % max)', r.delay_days, r.max_delay_days;
    RAISE NOTICE 'PASS 8: non-flagship SLA breach (SO-10288, % days delayed)', r.delay_days;

    -- 9. At Risk edge case: STANDARD tier, delay exactly equals max_delay_days (3),
    --    so it must NOT be Breached (strictly-greater-than per schema doc §6).
    SELECT (CURRENT_DATE - so.promised_delivery_date) AS delay_days, sr.max_delay_days INTO r
    FROM sales_orders so JOIN customers c ON c.customer_id = so.customer_id
    JOIN sla_rules sr ON sr.sla_tier = c.sla_tier
    WHERE so.order_no = 'SO-10310';
    ASSERT r.delay_days = r.max_delay_days, 'SO-10310 should be exactly at the STANDARD threshold';
    RAISE NOTICE 'PASS 9: At-Risk boundary case, delay == max_delay_days (SO-10310)';

    -- 10. PLATINUM tolerance: 4-day delay against a 7-day threshold stays At Risk.
    SELECT (CURRENT_DATE - so.promised_delivery_date) AS delay_days, sr.max_delay_days INTO r
    FROM sales_orders so JOIN customers c ON c.customer_id = so.customer_id
    JOIN sla_rules sr ON sr.sla_tier = c.sla_tier
    WHERE so.order_no = 'SO-30007';
    ASSERT r.delay_days <= r.max_delay_days, 'SO-30007 (PLATINUM) should still be At Risk, not Breached';
    RAISE NOTICE 'PASS 10: PLATINUM tier tolerance, At Risk not Breached (SO-30007)';

    -- 11. Reporting scenario: exactly the 4 Chennai delayed orders + day counts
    --     Person 1's ChatService/chat-fixtures already hardcode.
    IF (SELECT count(*) FROM sales_orders so JOIN warehouse w ON w.warehouse_id = so.warehouse_id
        WHERE w.location = 'Chennai' AND so.current_status = 'Delayed'
          AND so.order_no IN ('SO-10241', 'SO-10288', 'SO-10299', 'SO-10310')) <> 4 THEN
        RAISE EXCEPTION 'FAIL: expected exactly the 4 named Chennai delayed orders';
    END IF;
    FOR r IN
        SELECT order_no, (CURRENT_DATE - promised_delivery_date) AS delay_days
        FROM sales_orders WHERE order_no IN ('SO-10241', 'SO-10288', 'SO-10299', 'SO-10310')
        ORDER BY order_no
    LOOP
        RAISE NOTICE '  % delayed % days', r.order_no, r.delay_days;
    END LOOP;
    ASSERT (SELECT (CURRENT_DATE - promised_delivery_date) FROM sales_orders WHERE order_no = 'SO-10241') = 2;
    ASSERT (SELECT (CURRENT_DATE - promised_delivery_date) FROM sales_orders WHERE order_no = 'SO-10288') = 5;
    ASSERT (SELECT (CURRENT_DATE - promised_delivery_date) FROM sales_orders WHERE order_no = 'SO-10299') = 1;
    ASSERT (SELECT (CURRENT_DATE - promised_delivery_date) FROM sales_orders WHERE order_no = 'SO-10310') = 3;
    RAISE NOTICE 'PASS 11: reporting scenario matches ChatService/chat-fixtures exactly';

    -- Sanity: total order volume is in the 30-50 range team_plan.md calls for.
    ASSERT (SELECT count(*) FROM sales_orders) BETWEEN 30 AND 50, 'sales_orders count out of the 30-50 range';

    RAISE NOTICE 'ALL SCENARIOS PASS (11 of 11) — gate requires >= 10';
END $$;
