-- Validate data type conformity
SELECT 
  COUNT(*) AS num_rows,
  SUM(CASE WHEN id IS NULL THEN 1 ELSE 0 END) AS null_id,
  SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
  SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) AS null_quantity,
  SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) AS null_order_date
FROM orders;

-- Validate value ranges
SELECT 
  COUNT(*) AS num_rows,
  MIN(id) AS min_id,
  MAX(id) AS max_id,
  MIN(customer_id) AS min_customer_id,
  MAX(customer_id) AS max_customer_id,
  MIN(product_id) AS min_product_id,
  MAX(product_id) AS max_product_id,
  MIN(quantity) AS min_quantity,
  MAX(quantity) AS max_quantity,
  MIN(order_date) AS min_order_date,
  MAX(order_date) AS max_order_date
FROM orders;

-- Validate referential integrity
SELECT 
  COUNT(*) AS num_rows,
  SUM(CASE WHEN customer_id NOT IN (SELECT id FROM customers) THEN 1 ELSE 0 END) AS invalid_customer_ids,
  SUM(CASE WHEN product_id NOT IN (SELECT id FROM products) THEN 1 ELSE 0 END) AS invalid_product_ids
FROM orders;