DELIMITER //
CREATE PROCEDURE ValidateProducts()
BEGIN
    -- Data Type Conformity Test
    SELECT COUNT(*) FROM products WHERE data_type(id) != 'varchar' OR LENGTH(id) > 50;
    SELECT COUNT(*) FROM products WHERE data_type(name) != 'varchar' OR LENGTH(name) > 255;
    SELECT COUNT(*) FROM products WHERE data_type(price) != 'decimal' OR LENGTH(price) > 60;
    SELECT COUNT(*) FROM products WHERE data_type(stock) != 'int' OR LENGTH(stock) > 50;

    -- Value Ranges Test (Assuming price is a decimal and stock is an integer)
    SET @minPrice = -1000.00;
    SET @maxPrice = 100000.00;
    SELECT COUNT(*) FROM products WHERE price < @minPrice OR price > @maxPrice;

    -- Referential Integrity Test (Assuming product_id in orders table is a foreign key referencing the id column in products)
    SELECT COUNT(DISTINCT p.id) FROM products AS p
    LEFT JOIN orders AS o ON p.id = o.product_id
    WHERE p.id IS NULL;
END//
DELIMITER ;