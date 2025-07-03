-- Row Count Check
SELECT COUNT(*) FROM source_database.table1;
SELECT COUNT(*) FROM target_database.table1;

-- Foreign Key Validation
SELECT COUNT(*) FROM target_database.table2 WHERE table2.id NOT IN (SELECT id FROM source_database.table1);

-- Join Validation
SELECT COUNT(*) FROM target_database.table3 LEFT JOIN source_database.table4 ON target_database.table3.id = source_database.table4.id;

-- Aggregation Validation
SELECT COUNT(DISTINCT table5.column1) FROM target_database.table5 GROUP BY table5.column2 HAVING COUNT(*) > 1;

-- Filter Validation
SELECT COUNT(*) FROM target_database.table6 WHERE table6.column3 = 'value';