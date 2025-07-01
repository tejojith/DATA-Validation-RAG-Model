DELIMITER //
CREATE PROCEDURE validate_products()
BEGIN
    -- Data Type Conformity Test
    SELECT COUNT(*) as total
    FROM products
    WHERE id NOT REGEXP '^[a-zA-Z0-9]{1,50}$'
    OR name NOT REGEXP '^.{1,255}$'
    OR price NOT REGEXP '^[0-9]+(\.[0-9]{1,2})?$'
    OR stock NOT REGEXP '^[0-9]+(\s*(?:,\s*[0-9]+)*)?$';

    -- Value Ranges Test (Assuming price is numeric and stock is positive integer)
    SELECT COUNT(*) as total
    FROM products
    WHERE CAST(price AS UNSIGNED) < 0;

    SELECT COUNT(*) as total
    FROM products
    WHERE stock < 0;

    -- Referential Integrity Test (Assuming product_id in orders table is foreign key referencing id in products table)
    SELECT COUNT(*) as total
    FROM orders o
    JOIN products p ON o.product_id = p.id
    WHERE p.id IS NULL;
END//
DELIMITER ;