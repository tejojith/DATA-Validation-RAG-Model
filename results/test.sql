SELECT 
    COUNT(*) AS total_rows,
    SUM(CASE WHEN target_database.customers.id IS NULL THEN 1 ELSE 0 END) AS missing_customer_ids,
    SUM(CASE WHEN target_database.products.id IS NULL THEN 1 ELSE 0 END) AS missing_product_ids,
    SUM(CASE WHEN target_database.sales_orders.id IS NULL THEN 1 ELSE 0 END) AS missing_sales_order_ids,
    SUM(CASE WHEN target_database.sales_order_items.id IS NULL THEN 1 ELSE 0 END) AS missing_sales_order_item_ids
FROM source_database.raw_orders
LEFT JOIN target_database.customers ON source_database.raw_orders.customer_email = target_database.customers.email
LEFT JOIN target_database.products ON source_database.raw_orders.product_sku = target_database.products.name
LEFT JOIN target_database.sales_orders ON source_database.raw_orders.order_id = target_database.sales_orders.order_id
LEFT JOIN target_database.sales_order_items ON source_database.raw_orders.order_id = target_database.sales_order_items.order_id;

SELECT 
    COUNT(*) AS total_rows,
    SUM(CASE WHEN target_database.customers.id IS NULL THEN 1 ELSE 0 END) AS missing_customer_ids,
    SUM(CASE WHEN target_database.products.id IS NULL THEN 1 ELSE 0 END) AS missing_product_ids,
    SUM(CASE WHEN target_database.sales_orders.id IS NULL THEN 1 ELSE 0 END) AS missing_sales_order_ids,
    SUM(CASE WHEN target_database.sales_order_items.id IS NULL THEN 1 ELSE 0 END) AS missing_sales_order_item_ids
FROM source_database.raw_orders
LEFT JOIN target_database.customers ON source_database.raw_orders.customer_email = target_database.customers.email
LEFT JOIN target_database.products ON source_database.raw_orders.product_sku = target_database.products.name
LEFT JOIN target_database.sales_orders ON source_database.raw_orders.order_id = target_database.sales_orders.order_id
LEFT JOIN target_database.sales_order_items ON source_database.raw_orders.order_id = target_database.sales_order_items.order_id;