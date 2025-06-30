
import mysql.connector
from datetime import date

# Database connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'source_db'
}

def check_null_values(column):
    query = f"SELECT COUNT(*) FROM employees WHERE {column} IS NULL;"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None

def check_missing_required_fields():
    missing_count = 0
    for column in ['name', 'department', 'salary']:
        count = check_null_values(column)
        if count is not None and count > 0:
            missing_count += 1
    return missing_count

def check_empty_strings():
    query = "SELECT COUNT(*) FROM employees WHERE name = '' OR department = '';"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None

def check_default_values():
    # Assuming that the default values for salary and hired_date are 0 and '0000-00-00' respectively
    query = "SELECT COUNT(*) FROM employees WHERE salary = 0 OR hired_date IS NULL;"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None

def check_distinct_values(column):
    query = f"SELECT COUNT(DISTINCT {column}) FROM employees;"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0]

# Connect to the database
cnx = mysql.connector.connect(**db_config)
cursor = cnx.cursor()

# Run tests
null_values_id = check_null_values('id')
missing_required_fields_count = check_missing_required_fields()
empty_strings_count = check_empty_strings()
default_values_count = check_default_values()
hired_date_distinct_count = check_distinct_values('hired_date')

# Print test results
print(f"NULL values in id column: {null_values_id}")
print(f"Missing required fields count: {missing_required_fields_count}")
print(f"Empty strings count: {empty_strings_count}")
print(f"Default values count: {default_values_count}")
print(f"Distinct hired_date count: {hired_date_distinct_count}")

# Close the connection
cursor.close()
cnx.close()