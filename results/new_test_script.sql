-- Test data type conformity
SELECT * FROM customers WHERE NOT (id IS NULL OR id = '') AND NOT (name IS NULL OR name = '') AND NOT (email IS NULL OR email = '') AND NOT (signup_date IS NULL OR signup_date = '');

-- Test value ranges
SELECT * FROM customers WHERE id < 0 OR id > 100 OR name < 0 OR name > 255 OR email < 0 OR email > 255 OR signup_date < '2020-01-01' OR signup_date > '2020-12-31';

-- Test referential integrity
SELECT * FROM customers WHERE NOT EXISTS (SELECT 1 FROM orders WHERE customer_id = id);