import pandas as pd
from sqlalchemy import create_engine

# Define the source and target databases
source_db = {'host': 'localhost', 'user': 'root', 'password': 'password', 'database': 'source_db'}
target_db = {'host': 'localhost', 'user': 'root', 'password': 'password', 'database': 'target_db'}

# Create a connection to the source and target databases using SQLAlchemy
source_engine = create_engine('mysql+pymysql://{}:{}@{}/{}'.format(source_db['user'], source_db['password'], source_db['host'], source_db['database']))
target_engine = create_engine('mysql+pymysql://{}:{}@{}/{}'.format(target_db['user'], target_db['password'], target_db['host'], target_db['database']))

# Define the tables to be validated
source_table = 'employees'
target_table = 'employees'

# Get the schema of the source table
source_schema = pd.read_sql('SELECT * FROM {} LIMIT 0'.format(source_table), con=source_engine)

# Define the columns to be validated
columns_to_validate = ['id', 'name', 'department', 'salary', 'hired_date']

# Get the schema of the target table
target_schema = pd.read_sql('SELECT * FROM {} LIMIT 0'.format(target_table), con=target_engine)

# Validate the data type conformity for each column
for col in columns_to_validate:
    source_col_type = str(source_schema[col].dtypes)
    target_col_type = str(target_schema[col].dtypes)
    if source_col_type != target_col_type:
        print('Data type mismatch for column {} in table {}. Source data type is {}, but target data type is {}'.format(col, source_table, source_col_type, target_col_type))

# Validate the value ranges for each column
for col in columns_to_validate:
    source_min = source_schema[col].min()
    source_max = source_schema[col].max()
    target_min = target_schema[col].min()
    target_max = target_schema[col].max()
    if not (source_min == target_min and source_max == target_max):
        print('Value range mismatch for column {} in table {}. Source value range is {}, but target value range is {}'.format(col, source_table, (source_min, source_max), (target_min, target_max)))

# Validate the referential integrity of each column
for col in columns_to_validate:
    source_fk = source_schema[col].isnull().sum()
    target_fk = target_schema[col].isnull().sum()
    if not (source_fk == target_fk):
        print('Referential integrity mismatch for column {} in table {}. Source has {} NULL values, but target has {} NULL values'.format(col, source_table, source_fk, target_fk))

# Validate the number of rows in each table
source_row_count = source_schema.shape[0]
target_row_count = target_schema.shape[0]
if not (source_row_count == target_row_count):
    print('Row count mismatch between tables {}. Source has {} rows, but target has {} rows'.format(source_table, source_row_count, target_row_count))

# Validate the number of distinct values in each column
for col in columns_to_validate:
    source_distinct = len(set(source_schema[col]))
    target_distinct = len(set(target_schema[col]))
    if not (source_distinct == target_distinct):
        print('Distinct value count mismatch for column {} in table {}. Source has {} distinct values, but target has {} distinct values'.format(col, source_table, source_distinct, target_distinct))

# Validate the number of samples in each column
for col in columns_to_validate:
    source_samples = len(set(source_schema[col].sample(10)))
    target_samples = len(set(target_schema[col].sample(10)))
    if not (source_samples == target_samples):
        print('Sample count mismatch for column {} in table {}. Source has {} samples, but target has {} samples'.format(col, source_table, source_samples, target_samples))