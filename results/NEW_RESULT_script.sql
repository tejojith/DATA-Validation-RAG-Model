SELECT COUNT(*) FROM source_database.raw_orders WHERE NOT EXISTS (SELECT 1 FROM target_database.sales_orders WHERE source_database.raw_orders.order_id = target_database.sales_orders.order_id);

SELECT COUNT(*) FROM source_database.raw_orders WHERE NOT EXISTS (SELECT 1 FROM target_database.sales_orders WHERE source_database.raw_orders.order_id = target_database.sales_orders.order_id AND source_database.raw_orders.customer_id = target_database.sales_orders.customer_id);

SELECT COUNT(*) FROM source_database.raw_orders AS so
LEFT JOIN target_database.sales_orders AS so2 ON so.order_id = so2.order_id AND so.customer_id = so2.customer_id
WHERE so2.order_id IS NULL;

SELECT COUNT(*) FROM source_database.raw_orders AS so
LEFT JOIN target_database.sales_orders AS so2 ON so.order_id = so2.order_id AND so.customer_id = so2.customer_id
WHERE COALESCE(so.total_amount, 0) <> COALESCE(so2.total_amount, 0);

SELECT COUNT(*) FROM source_database.raw_orders AS so
JOIN target_database.sales_orders AS so2 ON so.order_id = so2.order_id AND so.customer_id = so2.customer_id
WHERE so.status <> so2.status;

SELECT COUNT(*) FROM source_database.raw_orders AS so
JOIN target_database.sales_orders AS so2 ON so.order_id = so2.order_id AND so.customer_id = so2.customer_id
WHERE so.price <> so2.price;