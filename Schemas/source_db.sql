-- =====================
-- Source Tables Setup
-- =====================


CREATE TABLE raw_orders (
    order_id INT,
    customer_name VARCHAR(100),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(20),
    order_date DATE,
    status VARCHAR(50),
    total_amount DECIMAL(10, 2),
    channel_name VARCHAR(100),
    shipping_method VARCHAR(50),
    payment_method VARCHAR(50)
);

CREATE TABLE raw_order_items (
    order_id INT,
    product_sku VARCHAR(50),
    quantity INT,
    unit_price DECIMAL(10, 2)
);

CREATE TABLE raw_products (
    sku VARCHAR(50),
    name VARCHAR(100),
    category_name VARCHAR(100),
    category_description TEXT,
    price DECIMAL(10, 2)
);

CREATE TABLE raw_inventory (
    sku VARCHAR(50),
    warehouse_name VARCHAR(100),
    location VARCHAR(100),
    quantity INT
);

CREATE TABLE raw_invoices (
    order_id INT,
    invoice_date DATE,
    total_amount DECIMAL(10, 2)
);

CREATE TABLE raw_payments (
    order_id INT,
    amount_paid DECIMAL(10, 2),
    payment_date DATE
);

CREATE TABLE raw_product_metrics (
    sku VARCHAR(50),
    month DATE,
    revenue DECIMAL(10,2),
    units_sold INT
);
