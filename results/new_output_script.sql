-- Test data type conformity
SELECT 
    COUNT(*) AS num_rows,
    SUM(CASE WHEN id IS NULL THEN 1 ELSE 0 END) AS null_count,
    SUM(CASE WHEN name IS NULL THEN 1 ELSE 0 END) AS null_count,
    SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) AS null_count,
    SUM(CASE WHEN signup_date IS NULL THEN 1 ELSE 0 END) AS null_count
FROM customers;

-- Test value ranges
SELECT 
    COUNT(*) AS num_rows,
    MIN(id),
    MAX(id),
    AVG(id)
FROM customers;

-- Test referential integrity
SELECT 
    COUNT(*) AS num_rows,
    SUM(CASE WHEN id NOT IN (SELECT DISTINCT id FROM customers) THEN 1 ELSE 0 END) AS invalid_ids
FROM customers;