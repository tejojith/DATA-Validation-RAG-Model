-- Verify that all tables have the expected number of rows
SELECT COUNT(*) AS row_count FROM source_database.table1;
SELECT COUNT(*) AS row_count FROM target_database.table1;

-- Verify that foreign key references are intact
SELECT COUNT(*) AS fk_count FROM information_schema.referential_constraints WHERE constraint_schema = 'target_database' AND referenced_table_name IS NOT NULL;

-- Verify that data types match between source and target tables
SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_schema = 'source_database' AND table_name = 'table1';
SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_schema = 'target_database' AND table_name = 'table1';

-- Verify that nullability matches between source and target tables
SELECT column_name, is_nullable FROM information_schema.columns WHERE table_schema = 'source_database' AND table_name = 'table1';
SELECT column_name, is_nullable FROM information_schema.columns WHERE table_schema = 'target_database' AND table_name = 'table1';

-- Verify that JOINs used in the transformation are valid and maintain referential integrity
SELECT COUNT(*) AS join_count FROM source_database.table1 INNER JOIN target_database.table2 ON source_database.table1.column1 = target_database.table2.column2;

-- Verify that filters or WHERE clauses are correctly applied
SELECT COUNT(*) AS filter_count FROM source_database.table1 WHERE column1 > 0;

-- Verify that aggregations or GROUP BYs match target values
SELECT COUNT(*) AS agg_count, SUM(column1) AS sum_column1 FROM source_database.table1 GROUP BY column2;
SELECT COUNT(*) AS agg_count, SUM(column1) AS sum_column1 FROM target_database.table1 WHERE column2 = 'value';

-- Verify that no extra or missing rows exist in the target table
SELECT COUNT(*) AS row_count FROM source_database.table1;
SELECT COUNT(*) AS row_count FROM target_database.table1;