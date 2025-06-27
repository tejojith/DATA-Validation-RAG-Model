import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData, Table
from sqlalchemy.sql import select
from pymysql import connect

# Connect to source and target databases
source_engine = create_engine('mysql+pymysql://root:password@localhost/source_db')
target_engine = create_engine('mysql+pymysql://root:password@localhost/target_db')

# Retrieve schema information for both databases
source_metadata = MetaData()
source_metadata.reflect(bind=source_engine)
target_metadata = MetaData()
target_metadata.reflect(bind=target_engine)

# Compare schema information between the two databases
schema_diff = source_metadata.compare(target_metadata)
if len(schema_diff) > 0:
    print("Schema differences found!")
    for diff in schema_diff:
        print(diff)
else:
    print("No schema differences found.")

# Compare record counts for each table in both databases
for source_table, target_table in zip(source_metadata.tables.values(), target_metadata.tables.values()):
    source_count = sa.select([sa.func.count('*')]).select_from(source_table).scalar()
    target_count = sa.select([sa.func.count('*')]).select_from(target_table).scalar()
    if source_count != target_count:
        print("Record count mismatch for table", source_table.name)
        print("Source count:", source_count)
        print("Target count:", target_count)

# Validate data transformations by comparing the source and target data
for source_table, target_table in zip(source_metadata.tables.values(), target_metadata.tables.values()):
    source_data = sa.select([sa.column('*')]).select_from(source_table).execute().fetchall()
    target_data = sa.select([sa.column('*')]).select_from(target_table).execute().fetchall()
    if len(source_data) != len(target_data):
        print("Data transformation failed for table", source_table.name)
        print("Source data:", source_data)
        print("Target data:", target_data)
    else:
        for i in range(len(source_data)):
            if source_data[i] != target_data[i]:
                print("Data transformation failed for table", source_table.name)
                print("Source data:", source_data[i])
                print("Target data:", target_data[i])
                break

# Verify ETL completeness by checking if all records from the source database have been transferred to the target database
source_count = sa.select([sa.func.count('*')]).select_from(source_table).scalar()
target_count = sa.select([sa.func.count('*')]).select_from(target_table).scalar()
if source_count != target_count:
    print("ETL completeness check failed")
    print("Source count:", source_count)
    print("Target count:", target_count)
else:
    print("ETL completeness check passed")

# Identify data drift by comparing the distribution of values in each column between the two databases
for source_table, target_table in zip(source_metadata.tables.values(), target_metadata.tables.values()):
    for source_column, target_column in zip(source_table.columns, target_table.columns):
        source_data = sa.select([sa.column('*')]).select_from(source_table).execute().fetchall()
        target_data = sa.select([sa.column('*')]).select_from(target_table).execute().fetchall()
        if len(source_data) != len(target_data):
            print("Data drift found for column", source_column.name, "in table", source_table.name)
            print("Source data:", source_data)
            print("Target data:", target_data)
        else:
            for i in range(len(source_data)):
                if source_data[i] != target_data[i]:
                    print("Data drift found for column", source_column.name, "in table", source_table.name)
                    print("Source data:", source_data[i])
                    print("Target data:", target_data[i])
                    break

# Generate a report summarizing the results of the comparison and validation
report = []
for source_table, target_table in zip(source_metadata.tables.values(), target_metadata.tables.values()):
    if len(source_table.columns) != len(target_table.columns):
        report.append("Table", source_table.name, "has a different number of columns than table", target_table.name)
    for source_column, target_column in zip(source_table.columns, target_table.columns):
        if source_column.type != target_column.type:
            report.append("Column", source_column.name, "has a different data type than column", target_column.name)
        if source_column.nullable != target_column.nullable:
            report.append("Column", source_column.name, "has a different nullability than column", target_column.name)
    if len(source_table.indexes) != len(target_table.indexes):
        report.append("Table", source_table.name, "has a different number of indexes than table", target_table.name)
    for source_index, target_index in zip(source_table.indexes, target_table.indexes):
        if source_index.type != target_index.type:
            report.append("Index", source_index.name, "has a different type than index", target_index.name)
    if len(source_table.foreign_keys) != len(target_table.foreign_keys):
        report.append("Table", source_table.name, "has a different number of foreign keys than table", target_table.name)
    for source_fk, target_fk in zip(source_table.foreign_keys, target_table.foreign_keys):
        if source_fk.column != target_fk.column:
            report.append("Foreign key", source_fk.name, "has a different column than foreign key", target_fk.name)
        if source_fk.ref_table != target_fk.ref_table:
            report.append("Foreign key", source_fk.name, "has a different referenced table than foreign key", target_fk.name)
    if len(source_table.primary_key) != len(target_table.primary_key):
        report.append("Table", source_table.name, "has a different number of primary keys than table", target_table.name)
    for source_pk, target_pk in zip(source_table.primary_key, target_table.primary_key):
        if source_pk != target_pk:
            report.append("Primary key", source_pk.name, "has a different column than primary key", target_pk.name)
    if len(source_table.unique_constraints) != len(target_table.unique_constraints):
        report.append("Table", source_table.name, "has a different number of unique constraints than table", target_table.name)
    for source_uc, target_uc in zip(source_table.unique_constraints, target_table.unique_constraints):
        if len(source_uc.columns) != len(target_uc.columns):
            report.append("Unique constraint", source_uc.name, "has a different number of columns than unique constraint", target_uc.name)
        for source_column, target_column in zip(source_uc.columns, target_uc.columns):
            if source_column != target_column:
                report.append("Unique constraint", source_uc.name, "has a different column than unique constraint", target_uc.name)
    if len(source_table.check_constraints) != len(target_table.check_constraints):
        report.append("Table", source_table.name, "has a different number of check constraints than table", target_table.name)
    for source_cc, target_cc in zip(source_table.check_constraints, target_table.check_constraints):
        if len(source_cc.columns) != len(target_cc.columns):
            report.append("Check constraint", source_cc.name, "has a different number of columns than check constraint", target_cc.name)
        for source_column, target_column in zip(source_cc.columns, target_cc.columns):
            if source_column != target_column:
                report.append("Check constraint", source_cc.name, "has a different column than check constraint", target_cc.name)
    if len(source_table.indexes) != len(target_table.indexes):
        report.append("Table", source_table.name, "has a different number of indexes than table", target_table.name)
    for source_index, target_index in zip(source_table.indexes, target_table.indexes):
        if len(source_index.columns) != len(target_index.columns):
            report.append("Index", source_index.name, "has a different number of columns than index", target_index.name)
        for source_column, target_column in zip(source_index.columns, target_index.columns):
            if source_column != target_column:
                report.append("Index", source_index.name, "has a different column than index", target_index.name)
    if len(source_table.foreign_keys) != len(target_table.foreign_keys):
        report.append("Table", source_table.name, "has a different number of foreign keys than table", target_table.name)
    for source_fk, target_fk in zip(source_table.foreign_keys, target_table.foreign_keys):
        if len(source_fk.columns) != len(target_fk.columns):
            report.append("Foreign key", source_fk.name, "has a different number of columns than foreign key", target_fk.name)
        for source_column, target_column in zip(source_fk.columns, target_fk.columns):
            if source_column != target_column:
                report.append("Foreign key", source_fk.name, "has a different column than foreign key", target_fk.name)
    if len(source_table.primary_key) != len(target_table.primary_key):
        report.append("Table", source_table.name, "has a different number of primary keys than table", target_table.name)
    for source_pk, target_pk in zip(source_table.primary_key, target_table.primary_key):
        if len(source_pk.columns) != len(target_pk.columns):
            report.append("Primary key", source_pk.name, "has a different number of columns than primary key", target_pk.name)
        for source_column, target_column in zip(source_pk.columns, target_pk.columns):
            if source_column != target_column:
                report.append("Primary key", source_pk.name, "has a different column than primary key", target_pk.name)
    if len(source_table.unique_constraints) != len(target_table.unique_constraints):
        report.append("Table", source_table.name, "has a different number of unique constraints than table", target_table.name)
    for source_uc, target_uc in zip(source_table.unique_constraints, target_table.unique_constraints):
        if len(source_uc.columns) != len(target_uc.columns):
            report.append("Unique constraint", source_uc.name, "has a different number of columns than unique constraint", target_uc.name)
        for source_column, target_column in zip(source_uc.columns, target_uc.columns):
            if source_column != target_column:
                report.append("Unique constraint", source_uc.name, "has a different column than unique constraint", target_uc.name)
    if len(source_table.check_constraints) != len(target_table.check_constraints):
        report.append("Table", source_table.name, "has a different number of check constraints than table", target_table.name)
    for source_cc, target_cc in zip(source_table.check_constraints, target_table.check_constraints):
        if len(source_cc.columns) != len(target_cc.columns):
            report.append("Check constraint", source_cc.name, "has a different number of columns than check constraint", target_cc.name)
        for source_column, target_column in zip(source_cc.columns, target_cc.columns):
            if source_column != target_column:
                report.append("Check constraint", source_cc.name, "has a different column than check constraint", target_cc.name)
    if len(source_table.indexes) != len(target_table.indexes):
        report.append("Table", source_table.name, "has a different number of indexes than table", target_table.name)
    for source_index, target_index in zip(source_table.indexes, target_table.indexes):
        if len(source_index.columns) != len(target_index.columns):
            report.append("Index", source_index.name, "has a different number of columns than index", target_index.name)
        for source_column, target_column in zip(source_index.columns, target_index.columns):
            if source_column != target_column:
                report.append("Index", source_index.name, "has a different column than index", target_index.name)
    if len(source_table.foreign_keys) != len(target_table.foreign_keys):
        report.append("Table", source_table.name, "has a different number of foreign keys than table", target_table.name)
    for source_fk, target_fk in zip(source_table.foreign_keys, target_table.foreign_keys):
        if len(source_fk.columns) != len(target_fk.columns):
            report.append("Foreign key", source_fk.name, "has a different number of columns than foreign key", target_fk.name)
        for source_column, target_column in zip(source_fk.columns, target_fk.columns):
            if source_column != target_column:
                report.append("Foreign key", source_fk.name, "has a different column than foreign key", target_fk.name)
    if len(source_table.primary_key) != len(target_table.primary_key):
        report.append("Table", source_table.name, "has a different number of primary keys than table", target_table.name)
    for source_pk, target_pk in zip(source_table.primary_key, target_table.primary_key):
        if len(source_pk.columns) != len(target_pk.columns):
            report.append("Primary key", source_pk.name, "has a different number of columns than primary key", target_pk.name)
        for source_column, target_column in zip(source_pk.columns, target_pk.columns):
            if source_column != target_column:
                report.append("Primary key", source_pk.name, "has a different column than primary key", target_pk.name)
    if len(source_table.unique_constraints) != len(target_table.unique_constraints):
        report.append("Table", source_table.name, "has a different number of unique constraints than table", target_table.name)
    for source_uc, target_uc in zip(source_table.unique_constraints, target_table.unique_constraints):
        if len(source_uc.columns) != len(target_uc.columns):
            report.append("Unique constraint", source_uc.name, "has a different number of columns than unique constraint", target_uc.name)
        for source_column, target_column in zip(source_uc.columns, target_uc.columns):
            if source_column != target_column:
                report.append("Unique constraint", source_uc.name, "has a different column than unique constraint", target_uc.name)
    if len(source_table.check_constraints) != len(target_table.check_constraints):
        report.append("Table", source_table.name, "has a different number of check constraints than table", target_table.name)
    for source_cc, target_cc in zip(source_table.check_constraints, target_table.check_constraints):
        if len(source_cc.columns) != len(target_cc.columns):
            report.append("Check constraint", source_cc.name, "has a different number of columns than check constraint", target_cc.name)
        for source_column, target_column in zip(source_cc.columns, target_cc.columns):
            if source_column != target_column:
                report.append("Check constraint", source_cc.name, "has a different column than check constraint", target_cc.name)
    if len(source_table.indexes) != len(target_table.indexes):
        report.append("Table", source_table.name, "has a different number of indexes than table", target_table.name)
    for source_index, target_index in zip(source_table.indexes, target_table.indexes):
        if len(source_index.columns) != len(target_index.columns):
            report.append("Index", source_index.name, "has a different number of columns than index", target_index.name)
        for source_column, target_column in zip(source_index.columns, target_index.columns):
            if source_column != target_column:
                report.append("Index", source_index.name, "has a different column than index", target_index.name)
    if len(source_table.foreign_keys) != len(target_table.foreign_keys):
        report.append("Table", source_table.name, "has a different number of foreign keys than table", target_table.name)
    for source_fk, target_fk in zip(source_table.foreign_keys, target_table.foreign_keys):
        if len(source_fk.columns) != len(target_fk.columns):
            report.append("Foreign key", source_fk.name, "has a different number of columns than foreign key", target_fk.name)
        for source_column, target_column in zip(source_fk.columns, target_fk.columns):
            if source_column != target_column:
                report.append("Foreign key", source_fk.name, "has a different column than foreign key", target_fk.name)
    if len(source_table.primary_key) != len(target_table.primary_key):
        report.append("Table", source_table.name, "has a different number of primary keys than table", target_table.name)
    for source_pk, target_pk in zip(source_table.primary_key, target_table.primary_key):
        if len(source_pk.columns) != len(target_pk.columns):
            report.append("Primary key", source_pk.name, "has a different number of columns than primary key", target_pk.name)
        for source_column, target_column in zip(source_pk.columns, target_pk.columns):
            if source_column != target_column:
                report.append("Primary key", source_pk.name, "has a different column than primary key", target_pk.name)
    if len(source_table.unique_constraints) != len(target_table.unique_constraints):
        report.append("Table", source_table.name, "has a different number of unique constraints than table", target_table.name)
    for source_uc, target_uc in zip(source_table.unique_constraints, target_table.unique_constraints):
        if len(source_uc.columns) != len(target_uc.columns):
            report.append("Unique constraint", source_uc.name, "has a different number of columns than unique constraint", target_uc.name)
        for source_column, target_column in zip(source_uc.columns, target_uc.columns):
            if source_column != target_column:
                report.append("Unique constraint", source_uc.name, "has a different column than unique constraint", target_uc.name)
    if len(source_table.check_constraints) != len(target_table.check_constraints):
        report.append("Table", source_table.name, "has a different number of check constraints than table", target_table.name)
    for source_cc, target_cc in zip(source_table.check_constraints, target_table.check_constraints):
        if len(source_cc.columns) != len(target_cc.columns):
            report.append("Check constraint", source_cc.name, "has a different number of columns than check constraint", target_cc.name)
        for source_column, target_column in zip(source_cc.columns, target_cc.columns):
            if source_column != target_column:
                report.append("Check constraint", source_cc.name, "has a different column than check constraint", target_cc.name)
    if len(source_table.indexes) != len(target_table.indexes):
        report.append("Table", source_table.name, "has a different number of indexes than table", target_table.name)
    for source_index, target_index in zip(source_table.indexes, target_table.indexes):
        if len(source_index.columns) != len(target_index.columns):
            report.append("Index", source_index.name, "has a different number of columns than index", target_index.name)
        for source_column, target_column in zip(source_index.columns, target_index.columns):
            if source_column != target_column:
                report.append("Index", source_index.name, "has a different column than index", target_index.name)
    if len(source_table.foreign_keys) != len(target_table.foreign_keys):
        report.append("Table", source_table.name, "has a different number of foreign keys than table", target_table.name)
    for source_fk, target_fk in zip(source_table.foreign_keys, target_table.foreign_keys):
        if len(source_fk.columns) != len(target_fk.columns):
            report.append("Foreign key", source_fk.name, "has a different number of columns than foreign key", target_fk.name)
        for source_column, target_column in zip(source_fk.columns, target_fk.columns):
            if source_column != target_column:
                report.append("Foreign key", source_fk.name, "has a different column than foreign key", target_fk.name)
    if len(source_table.primary_key) != len(target_table.primary_key):
        report.append("Table", source_table.name, "has a different number of primary keys than table", target_table.name)
    for source_pk, target_pk in zip(source_table.primary_key, target_table.primary_key):
        if len(source_pk.columns) != len(target_pk.columns):
            report.append("Primary key", source_pk.name, "has a different number of columns than primary key", target_pk.name)
        for source_column, target_column in zip(source_pk.columns, target_pk.columns):
            if source_column != target_column:
                report.append("Primary key", source_pk.name, "has a different column than primary key", target_pk.name)
    if len(source_table.unique_constraints) != len(target_table.unique_constraints):
        report.append("Table", source_table.name, "has a different number of unique constraints than table", target_table.name)
    for source_uc, target_uc in zip(source_table.unique_constraints, target_table.unique_constraints):
        if len(source_uc.columns) != len(target_uc.columns):
            report.append("Unique constraint", source_uc.name, "has a different number of columns than unique constraint", target_uc.name)
        for source_column, target_column in zip(source_uc.columns, target_uc.columns):
            if source_column != target_column:
                report.append("Unique constraint", source_uc.name, "has a different column than unique constraint", target_uc.name)
    if len(source_table.check_constraints) != len(target_table.check_constraints):
        report.append("Table", source_table.name, "has a different number of check constraints than table", target_table.name)
    for source_cc, target_cc in zip(source_table.check_constraints, target_table.check_constraints):
        if len(source_cc.columns) != len(target_cc.columns):
            report.append("Check constraint", source_cc.name, "has a different number of columns than check constraint", target_cc.name)
        for source_column, target_column in zip(source_cc.columns, target_cc.columns):
            if source_column != target_column:
                report.append("Check constraint", source_cc.name, "has a different column than check constraint", target_cc.name)
print(report)