import pandas as pd
from datetime import datetime

# Load the table into a DataFrame
df = pd.read_sql_query("SELECT * FROM employees", connection)

def check_data_type(column):
    """Check if all values in a column have the correct data type"""
    for value in column:
        if not isinstance(value, type(column[0])):
            print(f"Error: {column} contains an incorrect data type ({type(value)}).")

def check_value_range(column, min_val=None, max_val=None):
    """Check if all values in a column are within the specified range"""
    for value in column:
        if (min_val is not None and value < min_val) or (max_val is not None and value > max_val):
            print(f"Error: {column} contains an out-of-range value ({value}).")

def check_referential_integrity(table, foreign_key, referenced_table, referenced_column):
    """Check if all values in a foreign key column exist in the referenced table"""
    df_foreign = pd.read_sql_query(f"SELECT {foreign_key} FROM {table}", connection)
    df_referenced = pd.read_sql_query(f"SELECT {referenced_column} FROM {referenced_table}", connection)

    missing_values = set(df_foreign[foreign_key]) - set(df_referenced[referenced_column])
    if len(missing_values) > 0:
        print("Error: Missing referential integrity in the foreign key column.")
        for value in missing_values:
            print(f"- {value}")

# Check data type conformity
check_data_type(df['id'])
check_data_type(df['name'])
check_data_type(df['department'])
check_data_type(df['salary'])
check_data_type(df['hired_date'])

# Check value ranges (assuming no specific range for these columns)
# check_value_range(df['id'], min_val=1, max_val=None)
# check_value_range(df['salary'], min_val=0.0, max_val=None)

# Check referential integrity (assuming no foreign key relationships in this example)
# check_referential_integrity('employees', 'foreign_key', 'another_table', 'referenced_column')