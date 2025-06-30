-- Check for NULL values in name, price, and stock columns of products table
SELECT id, name, price, stock
FROM products
WHERE name IS NULL OR price IS NULL OR stock IS NULL;

-- Check for default values that might indicate missing data in the same columns
SELECT id, name, price, stock
FROM products
WHERE name = '' OR price = '' OR stock = '';