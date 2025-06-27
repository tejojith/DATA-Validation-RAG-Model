
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Decimal, Date, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import datetime

# Database connection details
host = 'localhost'
user = 'root'
password =  'password'
port = 3306
database = 'source_db'
DB_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(DB_URL)
metadata = MetaData()
employees = Table('employees', metadata, autoload_with=engine)

def check_data_type_conformity():
    # Check if the data types of each column match their declared types in the table schema
    for column in employees.c:
        distinct_values = session.query(column).distinct().all()

        if column.type is not Integer:
            if any(isinstance(value, int) for value in [x[0] for x in distinct_values]):
                print(f"Error: {column.key} contains integer values but its data type is not int.")

        if column.type is not String:
            if all(isinstance(value, str) for value in [x[0] for x in distinct_values]):
                print(f"Error: {column.key} contains string values but its data type is not varchar.")

        if column.type is not Decimal:
            if all(isinstance(value, (float, decimal.Decimal)) for value in [x[0] for x in distinct_values]):
                print(f"Error: {column.key} contains decimal values but its data type is not decimal.")

        if column.type is not Date:
            if all(isinstance(value, datetime.date) for value in [x[0] for x in distinct_values]):
                print(f"Error: {column.key} contains date values but its data type is not date.")

def check_value_ranges():
    # Check if the values of each column are within their expected ranges
    min_hired_date = datetime.date(2019, 1, 1)

    for row in session.query(employees).all():
        if row.hired_date < min_hired_date:
            print(f"Error: Employee {row.id} has hired_date ({row.hired_date}) that is before 2019-01-01.")

def check_referential_integrity():
    # Check if foreign keys reference valid primary key values in the related table
    departments = Table('departments', metadata, autoload_with=engine)

    for row in session.query(employees).all():
        if row.department and not session.query(departments.id).filter_by(name=row.department).first():
            print(f"Error: Department '{row.department}' does not exist.")

if __name__ == "__main__":
    Session = sessionmaker(bind=engine)
    session = Session()

    check_data_type_conformity()
    check_value_ranges()
    check_referential_integrity()