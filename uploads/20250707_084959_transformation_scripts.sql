-- =====================
-- ETL Transform Scripts
-- =====================

-- Load Customers
INSERT INTO target_database.customers (name, email, phone)
SELECT DISTINCT customer_name, customer_email, customer_phone
FROM source_database.raw_orders;

-- Load Sales Channels
INSERT INTO target_database.sales_channels (name)
SELECT DISTINCT channel_name FROM source_database.raw_orders;

-- Load Payment Methods
INSERT INTO target_database.payment_methods (method_name)
SELECT DISTINCT payment_method FROM source_database.raw_orders;

-- Load Shipping Methods
INSERT INTO target_database.shipping_methods (method_name)
SELECT DISTINCT shipping_method FROM source_database.raw_orders;

-- Load Product Categories
INSERT INTO target_database.product_categories (name, description)
SELECT DISTINCT category_name, category_description 
FROM source_database.raw_products;

-- Load Products
INSERT INTO target_database.products (name, category_id, price, stock_quantity)
SELECT 
    rp.name,
    pc.category_id,
    rp.price,
    0
FROM source_database.raw_products rp
JOIN target_database.product_categories pc ON rp.category_name = pc.name;

-- Load Warehouses
INSERT INTO target_database.warehouses (name, location)
SELECT DISTINCT warehouse_name, location 
FROM source_database.raw_inventory;

-- Load Inventory
INSERT INTO target_database.inventory (product_id, warehouse_id, quantity)
SELECT 
    p.product_id,
    w.warehouse_id,
    ri.quantity
FROM source_database.raw_inventory ri
JOIN target_database.products p ON ri.sku = p.name
JOIN target_database.warehouses w ON ri.warehouse_name = w.name;

-- Load Sales Orders
INSERT INTO target_database.sales_orders (customer_id, order_date, status, total_amount, shipping_method_id, payment_method_id, channel_id)
SELECT 
    c.customer_id,
    ro.order_date,
    ro.status,
    ro.total_amount,
    sm.shipping_method_id,
    pm.payment_method_id,
    sc.channel_id
FROM source_database.raw_orders ro
JOIN target_database.customers c ON ro.customer_email = c.email
JOIN target_database.shipping_methods sm ON ro.shipping_method = sm.method_name
JOIN target_database.payment_methods pm ON ro.payment_method = pm.method_name
JOIN target_database.sales_channels sc ON ro.channel_name = sc.name;

-- Load Sales Order Items
INSERT INTO target_database.sales_order_items (order_id, product_id, quantity, price)
SELECT 
    so.order_id,
    p.product_id,
    roi.quantity,
    roi.unit_price
FROM source_database.raw_order_items roi
JOIN target_database.products p ON roi.product_sku = p.name
JOIN target_database.sales_orders so ON roi.order_id = so.order_id;

-- Load Invoices
INSERT INTO target_database.invoices (order_id, invoice_date, total_amount)
SELECT 
    so.order_id,
    ri.invoice_date,
    ri.total_amount
FROM source_database.raw_invoices ri
JOIN target_database.sales_orders so ON ri.order_id = so.order_id;

-- Load Payments
INSERT INTO target_database.payments (invoice_id, amount_paid, payment_date)
SELECT 
    i.invoice_id,
    rp.amount_paid,
    rp.payment_date
FROM source_database.raw_payments rp
JOIN target_database.invoices i ON rp.order_id = i.order_id;

-- Load Product Performance Metrics
INSERT INTO target_database.product_performance_metrics (product_id, month, revenue, units_sold)
SELECT 
    p.product_id,
    rpm.month,
    rpm.revenue,
    rpm.units_sold
FROM source_database.raw_product_metrics rpm
JOIN target_database.products p ON rpm.sku = p.name;
