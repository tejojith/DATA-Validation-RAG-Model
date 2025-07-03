SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'sales_orders' AND COLUMN_NAME = 'order_id';

SELECT * FROM sales_orders WHERE order_id = 1;

SELECT * FROM products WHERE product_id = 1;

SELECT COUNT(*) FROM sales_orders;

SELECT * FROM sales_order_items WHERE order_id = 1;

SELECT * FROM sales_orders WHERE order_total < 100;

SELECT * FROM products WHERE product_name LIKE '%apple%';

EXPLAIN SELECT * FROM sales_orders WHERE order_total < 100;

SELECT * FROM sales_orders WHERE order_total < 100;

SELECT * FROM sales_orders WHERE order_total < 100;

SELECT COUNT(*) FROM sales_orders;