-- Validate row counts match expectations after transformations
SELECT COUNT(*) AS "Total Rows in Source Database" FROM source_database.raw_orders;
SELECT COUNT(*) AS "Total Rows in Target Database" FROM target_database.sales_orders;

-- Check referential integrity between source and target tables
SELECT COUNT(*) AS "Referential Integrity Issues" 
FROM source_database.raw_orders so 
LEFT JOIN target_database.customers c ON so.customer_email = c.email 
WHERE c.customer_id IS NULL;

-- Verify data quality and completeness
SELECT COUNT(*) AS "Missing Values in Source Database" FROM source_database.raw_orders WHERE customer_email IS NULL OR shipping_address IS NULL;
SELECT COUNT(*) AS "Missing Values in Target Database" FROM target_database.sales_orders WHERE customer_id IS NULL OR shipping_address IS NULL;

-- Validate specific transformation rules from the ETL script
SELECT COUNT(*) AS "Total Orders with Missing Payment Information" 
FROM source_database.raw_orders so 
WHERE payment_method IS NULL AND total_amount IS NULL;

SELECT COUNT(*) AS "Total Orders with Missing Shipping Address" 
FROM source_database.raw_orders so 
WHERE shipping_address IS NULL;

-- Check for data loss or duplication during transformation
SELECT COUNT(*) AS "Duplicate Rows in Target Database" FROM target_database.sales_orders GROUP BY order_id HAVING COUNT(*) > 1;