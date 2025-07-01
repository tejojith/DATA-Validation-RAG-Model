import os

import mysql.connector
from connect_alchemy import MySQLConnection
from typing import Dict, List
import sqlparse

# Configuration
RESULTS_FOLDER = 'results' # Name of your Python script

# MySQL connection configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'source_db'
}

class ExecuteOutput:
    def __init__(self, script_filename):
        self.path = script_filename
        
            
    def extract_output(self,path: str):
        with open(path, 'r') as file:
            results = file.read()

        statements = sqlparse.split(results)
        return statements 


    def execute_final(self, connection_config: Dict) -> List[Dict]:
        conn = MySQLConnection(**connection_config)     
        try:
            #get the script
            statements = self.extract_output(self.path)
            # execute the script
            for stmt in statements:
                cleaned = stmt.strip()
                if cleaned:
                    try:
                        result = conn.execute_query(cleaned)
                        print(result)
                    except Exception as e:
                        print(f"Error executing: {cleaned}\n{e}")
        finally:
            conn.close()
                


if __name__ == "__main__":

    executor = ExecuteOutput(script_filename='results/test2_script.sql')
    # Execute the final script
    executor.execute_final(MYSQL_CONFIG)

