import mysql.connector
import pandas as pd
from langchain.schema import Document
from typing import Optional, List, Dict, Union

class MySQLConnection:
    def __init__(self, host: str, user: str, password: str, database: str):
        self.mysql_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connection = None

    def connect(self) -> bool:
        if self.connection:
            return True
            
        try:
            self.connection = mysql.connector.connect(**self.mysql_config)
            print("Successfully connected to MySQL database")
            return True
        except mysql.connector.Error as err:
            print(f"--Error connecting to MySQL: {err}")
            return False

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
            print("MySQL connection closed")

    def execute_query(self, query):
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            df = pd.read_sql(query, self.connection)
            print(f"Extracted {len(df)} records from MySQL")
            return df
        except Exception as e:
            print(f"--Error extracting data: {e}")
            return pd.DataFrame()

    def prepare_documents(self, df, content_column, metadata_columns=None):
        """
        Prepare documents from DataFrame
        
        Args:
            df (pandas.DataFrame): Source DataFrame
            content_column (str): Column containing main content
            metadata_columns (list): Columns to include as metadata
            
        Returns:
            list: List of Document objects
        """
        documents = []
        
        for idx, row in df.iterrows():
            # Main content
            content = str(row[content_column]) if pd.notna(row[content_column]) else ""
            
            # Prepare metadata
            metadata = {"source": "mysql_database", "row_id": idx}
            if metadata_columns:
                for col in metadata_columns:
                    if col in df.columns:
                        metadata[col] = str(row[col]) if pd.notna(row[col]) else ""
            
            # Create document
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        print(f"Prepared {len(documents)} documents")
        return documents








    
if __name__ == "__main__":
            # Configure databases
    source_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'source_db'
    }

    target_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'target_db'
    }
    with MySQLConnection(**source_config) as conn:
        tables_df = conn.execute_query("Select * from employees;")
    
    
    print(tables_df)