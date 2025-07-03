-- Verify that the number of rows in each table is as expected
SELECT COUNT(*) AS source_count FROM source_database.table1;
SELECT COUNT(*) AS target_count FROM target_database.table1;

-- Verify that foreign key references are intact
SELECT * FROM target_database.table1 WHERE NOT EXISTS (SELECT 1 FROM source_database.table2 WHERE source_database.table1.fk = source_database.table2.pk);

-- Verify that JOINs used in the transformation are valid and maintain referential integrity
SELECT * FROM target_database.table1 LEFT JOIN source_database.table2 ON target_database.table1.fk = source_database.table2.pk;

-- Verify that filters or WHERE clauses are correctly applied
SELECT * FROM target_database.table1 WHERE column1 > 0 AND column2 < 10;

-- Verify that aggregations or GROUP BYs match target values
SELECT COUNT(*) AS count, SUM(column1) AS sum, AVG(column2) AS avg FROM target_database.table1 GROUP BY column3;

-- Verify that no extra or missing rows exist in `target_database`
SELECT COUNT(*) AS count FROM target_database.table1 WHERE NOT EXISTS (SELECT 1 FROM source_database.table2 WHERE source_database.table1.fk = source_database.table2.pk);

-- Verify that data in `target_database` tables was derived as expected from `source_database` tables
SELECT * FROM target_database.table1 WHERE NOT EXISTS (SELECT 1 FROM source_database.table2 WHERE source_database.table1.fk = source_database.table2.pk);

-- Verify that column-level expressions (calculations, mappings, case logic) are correctly computed
SELECT * FROM target_database.table1 WHERE NOT EXISTS (SELECT 1 FROM source_database.table2 WHERE source_database.table1.fk = source_database.table2.pk);