SELECT COUNT(*) AS num_rows
FROM source_database.raw_orders
EXCEPT
SELECT COUNT(*) AS num_rows
FROM target_database.sales_orders;

SELECT COUNT(*) AS num_rows
FROM source_database.raw_orders
WHERE NOT EXISTS (
  SELECT 1
  FROM target_database.sales_orders
  WHERE source_database.raw_orders.order_id = target_database.sales_orders.order_id
);

SELECT COUNT(*) AS num_rows
FROM source_database.raw_orders
LEFT JOIN target_database.sales_orders ON source_database.raw_orders.order_id = target_database.sales_orders.order_id;

SELECT COUNT(*) AS num_rows
FROM source_database.raw_orders
WHERE COALESCE(source_database.raw_orders.order_date, '1970-01-01') <> COALESCE(target_database.sales_orders.order_date, '1970-01-01');

SELECT COUNT(*) AS num_rows
FROM source_database.raw_orders
JOIN target_database.sales_orders ON source_database.raw_orders.order_id = target_database.sales_orders.order_id;

SELECT COUNT(*) AS num_rows
FROM source_database.raw_orders
WHERE NOT EXISTS (
  SELECT 1
  FROM target_database.sales_orders
  WHERE source_database.raw_orders.order_id = target_database.sales_orders.order_id AND source_database.raw_orders.order_date <> target_database.sales_orders.order_date
);