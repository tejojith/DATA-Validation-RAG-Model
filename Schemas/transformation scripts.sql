-- =====================
-- ETL Transform Scripts
-- =====================


-- Load Customers
INSERT INTO customers (name, email, phone)
SELECT DISTINCT customer_name, customer_email, customer_phone
FROM raw_orders;

-- Load Sales Channels
INSERT INTO sales_channels (name)
SELECT DISTINCT channel_name FROM raw_orders;

-- Load Payment Methods
INSERT INTO payment_methods (method_name)
SELECT DISTINCT payment_method FROM raw_orders;

-- Load Shipping Methods
INSERT INTO shipping_methods (method_name)
SELECT DISTINCT shipping_method FROM raw_orders;

-- Load Product Categories
INSERT INTO product_categories (name, description)
SELECT DISTINCT category_name, category_description FROM raw_products;

-- Load Products
INSERT INTO products (name, category_id, price, stock_quantity)
SELECT 
    rp.name,
    pc.category_id,
    rp.price,
    0
FROM raw_products rp
JOIN product_categories pc ON rp.category_name = pc.name;

-- Load Warehouses
INSERT INTO warehouses (name, location)
SELECT DISTINCT warehouse_name, location FROM raw_inventory;

-- Load Inventory
INSERT INTO inventory (product_id, warehouse_id, quantity)
SELECT 
    p.product_id,
    w.warehouse_id,
    ri.quantity
FROM raw_inventory ri
JOIN products p ON ri.sku = p.name
JOIN warehouses w ON ri.warehouse_name = w.name;

-- Load Sales Orders
INSERT INTO sales_orders (customer_id, order_date, status, total_amount, shipping_method_id, payment_method_id, channel_id)
SELECT 
    c.customer_id,
    ro.order_date,
    ro.status,
    ro.total_amount,
    sm.shipping_method_id,
    pm.payment_method_id,
    sc.channel_id
FROM raw_orders ro
JOIN customers c ON ro.customer_email = c.email
JOIN shipping_methods sm ON ro.shipping_method = sm.method_name
JOIN payment_methods pm ON ro.payment_method = pm.method_name
JOIN sales_channels sc ON ro.channel_name = sc.name;

-- Load Sales Order Items
INSERT INTO sales_order_items (order_id, product_id, quantity, price)
SELECT 
    so.order_id,
    p.product_id,
    roi.quantity,
    roi.unit_price
FROM raw_order_items roi
JOIN products p ON roi.product_sku = p.name
JOIN sales_orders so ON roi.order_id = so.order_id;

-- Load Invoices
INSERT INTO invoices (order_id, invoice_date, total_amount)
SELECT 
    so.order_id,
    ri.invoice_date,
    ri.total_amount
FROM raw_invoices ri
JOIN sales_orders so ON ri.order_id = so.order_id;

-- Load Payments
INSERT INTO payments (invoice_id, amount_paid, payment_date)
SELECT 
    i.invoice_id,
    rp.amount_paid,
    rp.payment_date
FROM raw_payments rp
JOIN invoices i ON rp.order_id = i.order_id;

-- Load Product Performance Metrics
INSERT INTO product_performance_metrics (product_id, month, revenue, units_sold)
SELECT 
    p.product_id,
    rpm.month,
    rpm.revenue,
    rpm.units_sold
FROM raw_product_metrics rpm
JOIN products p ON rpm.sku = p.name;
