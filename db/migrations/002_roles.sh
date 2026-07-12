#!/bin/sh
# Database roles — docs/06_backend_schema.md §3.
#
# A shell script, not a .sql file, because the passwords must come from the
# environment and never from git. Postgres runs both from
# /docker-entrypoint-initdb.d in filename order, so this lands right after
# 001_init_schema.sql. To run it against a local (non-Docker) Postgres:
#
#   COPILOT_READONLY_PASSWORD=... COPILOT_APP_PASSWORD=... \
#     POSTGRES_USER=$(whoami) sh db/migrations/002_roles.sh
set -eu

psql -v ON_ERROR_STOP=1 \
    --username "${POSTGRES_USER:-postgres}" \
    --dbname "${POSTGRES_DB:-nexchain}" <<SQL
-- Read-only role used exclusively by the Text-to-SQL Agent / db_query MCP tool.
-- Its SELECT grants are the enforcement layer under SQL_TABLE_ALLOWLIST in
-- ai/contracts.py: even if the validator there is bypassed, the connection
-- itself cannot write, and cannot read users or audit_log at all.
CREATE ROLE copilot_readonly LOGIN PASSWORD '${COPILOT_READONLY_PASSWORD:?set COPILOT_READONLY_PASSWORD}';
GRANT CONNECT ON DATABASE ${POSTGRES_DB:-nexchain} TO copilot_readonly;
GRANT USAGE ON SCHEMA public TO copilot_readonly;
GRANT SELECT ON
    customers, sales_orders, order_items, inventory, warehouse,
    shipment, invoice, payment, carrier_tracking, sla_rules,
    knowledge_documents, knowledge_chunks
TO copilot_readonly;

-- Read/write role used by Spring Boot for auth + audit persistence.
CREATE ROLE copilot_app LOGIN PASSWORD '${COPILOT_APP_PASSWORD:?set COPILOT_APP_PASSWORD}';
GRANT CONNECT ON DATABASE ${POSTGRES_DB:-nexchain} TO copilot_app;
GRANT USAGE ON SCHEMA public TO copilot_app;
GRANT SELECT, INSERT ON audit_log TO copilot_app;
GRANT SELECT, INSERT, UPDATE ON users TO copilot_app;
GRANT USAGE, SELECT ON SEQUENCE audit_log_audit_id_seq, users_user_id_seq TO copilot_app;
SQL
