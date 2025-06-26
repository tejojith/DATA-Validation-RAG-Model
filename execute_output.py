import os

import mysql.connector

# Configuration
RESULTS_FOLDER = 'results'
SCRIPT_FILENAME = 'testing_script.py'  # Name of your Python script

# MySQL connection configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database'
}

def main():
    # Connect to MySQL
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("Connected to MySQL database.")
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return

    script_path = os.path.join(RESULTS_FOLDER, SCRIPT_FILENAME)
    if not os.path.isfile(script_path):
        print(f"Python script not found: {script_path}")
        conn.close()
        return

    with open(script_path, 'r', encoding='utf-8') as file:
        script_code = file.read()
    try:
        # Pass the MySQL connection to the script's global namespace
        exec(script_code, {'__name__': '__main__', 'mysql_conn': conn})
        print("Python script executed successfully.")
    except Exception as e:
        print(f"Error executing script: {e}")
    finally:
        conn.close()
        print("MySQL connection closed.")

if __name__ == "__main__":
    main()
