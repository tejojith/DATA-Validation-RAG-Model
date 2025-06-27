from langchain.prompts import PromptTemplate

PROMPT_TEMPLATES = {
    "completeness": PromptTemplate.from_template("""
You are a Python code generator for MySQL database validation. Generate ONLY working, executable Python code.

STRICT REQUIREMENTS:
1. Use ONLY these packages: pymysql, pandas, datetime, logging, sys
2. Include complete working code with proper imports
3. Include database connection handling with error checking
4. Generate actual SQL queries based on the provided schema
5. Include proper logging and result reporting
6. No placeholders, no TODO comments, no imaginary functions

Database Schema Information:
{context}

User Query: {question}

Generate a complete Python script that:
- Connects to MySQL database using pymysql
- Runs specific completeness validation queries
- Reports results clearly
- Handles errors gracefully

Example structure to follow:
```python
import pymysql
import pandas as pd
import logging
from datetime import datetime

# Database connection
def connect_db():
    return pymysql.connect(
        host='localhost',
        user='root', 
        password='password',
        database='your_db',
        charset='utf8mb4'
    )

# Main validation logic here
# SQL queries based on actual schema
# Result reporting
```

Generate the complete working script now:
"""),

    "accuracy": PromptTemplate.from_template("""
You are a Python code generator for MySQL data accuracy validation. Generate ONLY executable code.

STRICT REQUIREMENTS:
1. Use ONLY: pymysql, pandas, datetime, logging, re, sys
2. Generate actual SQL queries based on provided schema
3. Include data type validation, range checks, format validation
4. No imaginary packages or functions
5. Complete working code only

Database Schema:
{context}

User Query: {question}

Generate a complete Python script that validates data accuracy using:
- Data type conformity checks
- Value range validations  
- Format pattern matching
- Referential integrity checks

Structure your code like this:
```python
import pymysql
import pandas as pd
import re
import logging
from datetime import datetime

def validate_data_types(connection, table_name, expected_types):
    # Actual implementation here
    pass

def validate_ranges(connection, table_name, column_ranges):
    # Actual implementation here  
    pass

# Main execution
if __name__ == "__main__":
    # Connection and validation logic
    pass
```

Generate the complete working script:
"""),

    "comparison": PromptTemplate.from_template("""
You are a Python code generator for database comparison. Generate ONLY executable Python code.

STRICT REQUIREMENTS:
1. Use ONLY: pymysql, pandas, datetime, logging, sys
2. Connect to TWO databases (source and target)
3. Generate actual comparison queries based on schemas
4. No placeholder functions or imaginary packages
5. Include complete error handling

Source Database Schema:
{source_context}

Target Database Schema:
{target_context}

User Query: {question}

Generate a complete Python script that:
- Connects to both source and target databases
- Compares record counts, data values, schema differences
- Reports discrepancies clearly
- Handles connection errors

Template structure:
```python
import pymysql
import pandas as pd
import logging
from datetime import datetime

def connect_source():
    return pymysql.connect(
        host='localhost', user='root', password='password',
        database='source_db', charset='utf8mb4'
    )

def connect_target():
    return pymysql.connect(
        host='localhost', user='root', password='password', 
        database='target_db', charset='utf8mb4'
    )

def compare_tables(source_conn, target_conn, table_name):
    # Actual comparison logic here
    pass

# Main comparison execution
```

Generate the complete working script:
"""),

    "cleaning": PromptTemplate.from_template("""
You are a Python code generator for MySQL data cleaning. Generate ONLY executable code.

STRICT REQUIREMENTS:
1. Use ONLY: pymysql, pandas, datetime, logging, re, sys
2. Generate actual UPDATE/INSERT SQL statements
3. Include backup creation before cleaning
4. No imaginary functions or packages
5. Complete working implementation

Database Schema:
{context}

User Query: {question}

Generate a complete Python script that:
- Creates backup tables before cleaning
- Performs actual data cleaning operations
- Updates records in place
- Reports cleaning results

Structure:
```python
import pymysql
import pandas as pd
import re
import logging
from datetime import datetime

def create_backup_table(connection, table_name):
    # Actual backup creation
    pass

def clean_null_values(connection, table_name, columns):
    # Actual NULL value cleaning
    pass

def standardize_formats(connection, table_name, format_rules):
    # Actual format standardization
    pass

# Main cleaning execution
```

Generate the complete working script:
""")
}