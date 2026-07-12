-- P2.2 completion gate, part 2: the roles from docs/06_backend_schema.md §3
-- grant exactly what they should and nothing more.
--
--   psql -v ON_ERROR_STOP=1 -d nexchain -f db/verify_roles.sql
--
-- Asserts rather than prints: a wrong grant fails the script.
DO $$
DECLARE
    readable  TEXT[] := ARRAY['customers','sales_orders','order_items','inventory','warehouse',
                              'shipment','invoice','payment','carrier_tracking','sla_rules',
                              'knowledge_documents','knowledge_chunks'];
    t TEXT;
BEGIN
    FOREACH t IN ARRAY readable LOOP
        ASSERT has_table_privilege('copilot_readonly', t, 'SELECT'),
            format('copilot_readonly cannot SELECT %s', t);
        ASSERT NOT has_table_privilege('copilot_readonly', t, 'INSERT')
           AND NOT has_table_privilege('copilot_readonly', t, 'UPDATE')
           AND NOT has_table_privilege('copilot_readonly', t, 'DELETE'),
            format('copilot_readonly can write to %s — must be read-only', t);
    END LOOP;

    -- The Text-to-SQL agent must never see auth or audit data (§4).
    ASSERT NOT has_table_privilege('copilot_readonly', 'users', 'SELECT'),
        'copilot_readonly can read users';
    ASSERT NOT has_table_privilege('copilot_readonly', 'audit_log', 'SELECT'),
        'copilot_readonly can read audit_log';

    -- Spring Boot's role: audit + auth only, no supply-chain tables.
    ASSERT has_table_privilege('copilot_app', 'audit_log', 'INSERT'),
        'copilot_app cannot INSERT audit_log';
    ASSERT has_table_privilege('copilot_app', 'users', 'UPDATE'),
        'copilot_app cannot UPDATE users';
    ASSERT NOT has_table_privilege('copilot_app', 'sales_orders', 'SELECT'),
        'copilot_app can read sales_orders — not its job';

    RAISE NOTICE 'PASS: copilot_readonly and copilot_app grants match schema doc §3';
END $$;
