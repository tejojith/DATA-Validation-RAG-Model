-- Check data type conformity
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    COUNT(*) AS num_rows
FROM 
    information_schema.tables t
INNER JOIN 
    information_schema.columns c ON t.table_name = c.table_name
WHERE 
    c.data_type NOT IN ('integer', 'float', 'double', 'decimal')
GROUP BY 
    t.table_name,
    c.column_name,
    c.data_type
HAVING 
    COUNT(*) > 0;

-- Check value ranges
SELECT 
    t.table_name,
    c.column_name,
    MIN(c.min_value),
    MAX(c.max_value)
FROM 
    information_schema.tables t
INNER JOIN 
    information_schema.columns c ON t.table_name = c.table_name
WHERE 
    c.data_type IN ('integer