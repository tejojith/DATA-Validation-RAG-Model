-- Data type conformity tests
SELECT * FROM orders WHERE NOT (order_id IS INTEGER OR order_date IS DATE);

-- Value ranges tests
SELECT * FROM orders WHERE order_id < 0 OR order_id > 100;
SELECT * FROM orders WHERE order_date < '2020-01-01' OR order_date > '2020-12-31';

-- Referential integrity tests
SELECT * FROM orders WHERE customer_id NOT IN (SELECT id FROM customers);
SELECT * FROM orders WHERE product_id NOT IN (SELECT id FROM products);