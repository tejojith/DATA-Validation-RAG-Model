
-- ===============================
-- Core Sales Transactions Module
-- ===============================

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category_id INT,
    price DECIMAL(10, 2),
    stock_quantity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT
);

CREATE TABLE sales_channels (
    channel_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT
);

CREATE TABLE sales_orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date DATE,
    status VARCHAR(50),
    total_amount DECIMAL(10, 2),
    shipping_method_id INT,
    payment_method_id INT,
    channel_id INT REFERENCES sales_channels(channel_id)
);

CREATE TABLE sales_order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES sales_orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    price DECIMAL(10, 2)
);

CREATE TABLE payment_methods (
    payment_method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(50)
);

CREATE TABLE shipping_methods (
    shipping_method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(50),
    estimated_days INT
);

CREATE TABLE discounts (
    discount_id SERIAL PRIMARY KEY,
    description TEXT,
    discount_percent DECIMAL(5,2)
);

CREATE TABLE returns (
    return_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES sales_orders(order_id),
    return_date DATE,
    reason TEXT
);

CREATE TABLE return_items (
    return_item_id SERIAL PRIMARY KEY,
    return_id INT REFERENCES returns(return_id),
    product_id INT REFERENCES products(product_id),
    quantity INT
);

-- ===========================
-- Inventory & Supply Chain
-- ===========================

CREATE TABLE warehouses (
    warehouse_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    location VARCHAR(100)
);

CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    warehouse_id INT REFERENCES warehouses(warehouse_id),
    quantity INT
);

CREATE TABLE inventory_movements (
    movement_id SERIAL PRIMARY KEY,
    inventory_id INT REFERENCES inventory(inventory_id),
    movement_type VARCHAR(50),
    quantity INT,
    movement_date DATE
);

CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    contact_email VARCHAR(100)
);

CREATE TABLE purchase_orders (
    purchase_order_id SERIAL PRIMARY KEY,
    supplier_id INT REFERENCES suppliers(supplier_id),
    order_date DATE,
    status VARCHAR(50)
);

CREATE TABLE purchase_order_items (
    po_item_id SERIAL PRIMARY KEY,
    purchase_order_id INT REFERENCES purchase_orders(purchase_order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    price DECIMAL(10,2)
);

CREATE TABLE stock_adjustments (
    adjustment_id SERIAL PRIMARY KEY,
    inventory_id INT REFERENCES inventory(inventory_id),
    adjustment_reason TEXT,
    adjusted_quantity INT
);

CREATE TABLE restock_requests (
    request_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    requested_quantity INT,
    request_date DATE
);

-- ======================
-- Finance & Billing
-- ======================

CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES sales_orders(order_id),
    invoice_date DATE,
    total_amount DECIMAL(10, 2)
);

CREATE TABLE invoice_items (
    invoice_item_id SERIAL PRIMARY KEY,
    invoice_id INT REFERENCES invoices(invoice_id),
    description TEXT,
    amount DECIMAL(10, 2)
);

CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    invoice_id INT REFERENCES invoices(invoice_id),
    amount_paid DECIMAL(10, 2),
    payment_date DATE
);

CREATE TABLE payment_transactions (
    transaction_id SERIAL PRIMARY KEY,
    payment_id INT REFERENCES payments(payment_id),
    transaction_reference VARCHAR(100)
);

CREATE TABLE tax_rates (
    tax_id SERIAL PRIMARY KEY,
    region VARCHAR(100),
    rate DECIMAL(5,2)
);

CREATE TABLE exchange_rates (
    exchange_id SERIAL PRIMARY KEY,
    from_currency VARCHAR(10),
    to_currency VARCHAR(10),
    rate DECIMAL(10,4),
    effective_date DATE
);

-- ===========================
-- Analytics & Reporting
-- ===========================

CREATE TABLE sales_forecasts (
    forecast_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    forecast_month DATE,
    expected_sales INT
);

CREATE TABLE sales_targets (
    target_id SERIAL PRIMARY KEY,
    region VARCHAR(100),
    target_month DATE,
    target_amount DECIMAL(10,2)
);

CREATE TABLE product_performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    month DATE,
    revenue DECIMAL(10,2),
    units_sold INT
);

CREATE TABLE region_performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    region VARCHAR(100),
    month DATE,
    revenue DECIMAL(10,2)
);

CREATE TABLE customer_segmentation (
    segment_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    segment_name VARCHAR(100)
);

CREATE TABLE profit_margins (
    margin_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    margin_percent DECIMAL(5,2)
);

-- ==========================
-- CRM & Customer Engagement
-- ==========================

CREATE TABLE customer_contacts (
    contact_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    contact_date DATE,
    contact_method VARCHAR(50),
    notes TEXT
);

CREATE TABLE customer_feedback (
    feedback_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    feedback_date DATE,
    rating INT,
    comments TEXT
);

CREATE TABLE support_tickets (
    ticket_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    issue_description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loyalty_programs (
    program_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT
);

CREATE TABLE customer_rewards (
    reward_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    points INT,
    reward_date DATE
);

CREATE TABLE customer_behavior_logs (
    log_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    activity VARCHAR(255),
    log_date TIMESTAMP
);

-- ==========================
-- System & Configuration
-- ==========================

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50)
);

CREATE TABLE permissions (
    permission_id SERIAL PRIMARY KEY,
    permission_name VARCHAR(100)
);

CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    action VARCHAR(100),
    log_time TIMESTAMP
);

CREATE TABLE system_settings (
    setting_id SERIAL PRIMARY KEY,
    setting_name VARCHAR(100),
    setting_value TEXT
);

CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    message TEXT,
    read_status BOOLEAN DEFAULT FALSE
);

CREATE TABLE email_templates (
    template_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    subject TEXT,
    body TEXT
);

CREATE TABLE api_logs (
    api_log_id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255),
    request_time TIMESTAMP,
    response_code INT
);

CREATE TABLE data_imports (
    import_id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    import_date DATE,
    status VARCHAR(50)
);

CREATE TABLE data_exports (
    export_id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    export_date DATE,
    status VARCHAR(50)
);
