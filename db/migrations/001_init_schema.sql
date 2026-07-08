CREATE TABLE customers (
    customer_id     SERIAL PRIMARY KEY,
    customer_code   VARCHAR(20) UNIQUE NOT NULL,
    customer_name   VARCHAR(150) NOT NULL,
    contact_email   VARCHAR(150),
    contact_phone   VARCHAR(30),
    region          VARCHAR(50),
    sla_tier        VARCHAR(20) DEFAULT 'STANDARD', -- STANDARD, GOLD, PLATINUM
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE warehouse (
    warehouse_id    SERIAL PRIMARY KEY,
    warehouse_code  VARCHAR(20) UNIQUE NOT NULL,
    warehouse_name  VARCHAR(150) NOT NULL,
    location        VARCHAR(100) NOT NULL,  -- e.g. 'Chennai'
    address         TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE sales_orders (
    order_id                SERIAL PRIMARY KEY,
    order_no                VARCHAR(20) UNIQUE NOT NULL,   -- e.g. 'SO-45892'
    customer_id             INT NOT NULL REFERENCES customers(customer_id),
    warehouse_id            INT NOT NULL REFERENCES warehouse(warehouse_id),
    order_date              DATE NOT NULL,
    promised_delivery_date  DATE NOT NULL,
    revised_delivery_date   DATE,
    current_status          VARCHAR(30) NOT NULL,  -- Pending, Dispatched, In Transit, Delayed, Delivered, Cancelled
    total_amount            NUMERIC(12,2) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_sales_orders_status ON sales_orders(current_status);
CREATE INDEX idx_sales_orders_warehouse ON sales_orders(warehouse_id);

CREATE TABLE order_items (
    order_item_id   SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES sales_orders(order_id),
    sku             VARCHAR(30) NOT NULL,
    product_name    VARCHAR(150) NOT NULL,
    quantity        INT NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_sku ON order_items(sku);

CREATE TABLE inventory (
    inventory_id     SERIAL PRIMARY KEY,
    sku              VARCHAR(30) UNIQUE NOT NULL,
    product_name     VARCHAR(150) NOT NULL,
    warehouse_id     INT NOT NULL REFERENCES warehouse(warehouse_id),
    quantity_on_hand INT NOT NULL DEFAULT 0,
    quantity_reserved INT NOT NULL DEFAULT 0,
    reorder_level    INT NOT NULL DEFAULT 0,
    updated_at       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);

CREATE TABLE shipment (
    shipment_id       SERIAL PRIMARY KEY,
    order_id          INT NOT NULL REFERENCES sales_orders(order_id),
    tracking_no       VARCHAR(30) UNIQUE NOT NULL,
    carrier_name      VARCHAR(100),
    dispatch_date     DATE,
    current_location  VARCHAR(150),   -- e.g. 'Chennai Port'
    shipment_status   VARCHAR(30),    -- Dispatched, In Transit, Customs Hold, Delivered
    delay_reason      TEXT,           -- e.g. 'HS code mismatch during customs validation'
    created_at        TIMESTAMP NOT NULL DEFAULT now(),
    updated_at        TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_shipment_order ON shipment(order_id);
CREATE INDEX idx_shipment_status ON shipment(shipment_status);

CREATE TABLE carrier_tracking (
    tracking_event_id  SERIAL PRIMARY KEY,
    shipment_id        INT NOT NULL REFERENCES shipment(shipment_id),
    event_timestamp    TIMESTAMP NOT NULL,
    event_location     VARCHAR(150),
    event_status       VARCHAR(100),   -- e.g. 'Arrived at port', 'Customs hold'
    raw_payload        JSONB           -- raw carrier API response snapshot
);

CREATE INDEX idx_carrier_tracking_shipment ON carrier_tracking(shipment_id);

CREATE TABLE invoice (
    invoice_id      SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES sales_orders(order_id),
    invoice_no      VARCHAR(20) UNIQUE NOT NULL,
    invoice_date    DATE NOT NULL,
    amount          NUMERIC(12,2) NOT NULL,
    invoice_status  VARCHAR(20) NOT NULL   -- Draft, Sent, Paid, Overdue
);

CREATE INDEX idx_invoice_order ON invoice(order_id);

CREATE TABLE payment (
    payment_id      SERIAL PRIMARY KEY,
    invoice_id      INT NOT NULL REFERENCES invoice(invoice_id),
    payment_date    DATE,
    amount_paid     NUMERIC(12,2) NOT NULL,
    payment_method  VARCHAR(30),   -- Bank Transfer, Card, Cheque
    payment_status  VARCHAR(20)    -- Pending, Completed, Failed
);

CREATE INDEX idx_payment_invoice ON payment(invoice_id);

CREATE TABLE sla_rules (
    sla_rule_id      SERIAL PRIMARY KEY,
    sla_tier         VARCHAR(20) NOT NULL,   -- STANDARD, GOLD, PLATINUM
    max_delay_days   INT NOT NULL,           -- delay threshold before breach
    escalation_role  VARCHAR(50) NOT NULL,   -- e.g. 'Logistics Manager'
    description      TEXT
);

CREATE TABLE knowledge_documents (
    doc_id          SERIAL PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    doc_type        VARCHAR(30) NOT NULL,   -- SOP, SLA, POLICY
    source_path     TEXT NOT NULL,          -- file path or object storage key
    version         VARCHAR(20) DEFAULT 'v1',
    uploaded_at     TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_chunks (
    chunk_id        SERIAL PRIMARY KEY,
    doc_id          INT NOT NULL REFERENCES knowledge_documents(doc_id),
    chunk_index     INT NOT NULL,
    content         TEXT NOT NULL,
    vector_ref_id   VARCHAR(100),  -- id of the corresponding vector in Chroma/pgvector
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_knowledge_chunks_doc ON knowledge_chunks(doc_id);

CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    username        VARCHAR(100) UNIQUE NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'USER',  -- USER, ADMIN
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
    audit_id         BIGSERIAL PRIMARY KEY,
    trace_id         VARCHAR(64) NOT NULL,
    user_id          INT NOT NULL REFERENCES users(user_id),
    session_id       VARCHAR(64) NOT NULL,
    raw_query        TEXT NOT NULL,
    detected_intent  JSONB,           -- e.g. ["order_status", "delay_analysis"]
    agents_invoked   JSONB,           -- e.g. ["text_to_sql_agent", "api_status_agent", "business_rule_agent"]
    generated_sql    TEXT,
    api_calls        JSONB,           -- e.g. [{"endpoint": "...", "status": 200, "latency_ms": 320}]
    kb_sources       JSONB,           -- e.g. [{"doc_id": 3, "title": "Delay Handling SOP"}]
    final_response   TEXT NOT NULL,
    sla_result       VARCHAR(20),     -- On Time, At Risk, Breached, N/A
    created_at       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);
CREATE INDEX idx_audit_log_trace ON audit_log(trace_id);

-- Read-only role used exclusively by the Text-to-SQL Agent / db_query MCP tool
-- NOTE: Passwords and database name should be set securely via environment variables
-- or an initialization script wrapper, but provided here as the reference schema commands.

-- CREATE ROLE copilot_readonly LOGIN PASSWORD 'copilot_readonly_password';
-- GRANT CONNECT ON DATABASE nexchain TO copilot_readonly;
-- GRANT USAGE ON SCHEMA public TO copilot_readonly;
-- GRANT SELECT ON
--     customers, sales_orders, order_items, inventory, warehouse,
--     shipment, invoice, payment, carrier_tracking, sla_rules,
--     knowledge_documents, knowledge_chunks
-- TO copilot_readonly;

-- Read/write role used by Spring Boot for auth + audit persistence
-- CREATE ROLE copilot_app LOGIN PASSWORD 'copilot_app_password';
-- GRANT CONNECT ON DATABASE nexchain TO copilot_app;
-- GRANT USAGE ON SCHEMA public TO copilot_app;
-- GRANT SELECT, INSERT ON audit_log TO copilot_app;
-- GRANT SELECT, INSERT, UPDATE ON users TO copilot_app;
