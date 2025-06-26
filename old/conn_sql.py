    
import mysql.connector
import pandas as pd
from langchain.schema import Document

class MySQLConnection:
    def __init__(self, host, user, password, database):
        """Initialize MySQL connection parameters"""
        self.mysql_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'password',
            'database': 'sys'
        }

    def connect_to_mysql(self):
        """Create MySQL connection"""
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            print("Successfully connected to MySQL database")
            return connection
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            return None
        
    def extract_data_from_mysql(self, query):
        """
        Extract data from MySQL using a custom query
        
        Args:
            query (str): SQL query to extract data
            
        Returns:
            pandas.DataFrame: Extracted data
        """
        connection = self.connect_to_mysql()
        if not connection:
            return None
        
        try:
            df = pd.read_sql(query, connection)
            print(f"✅ Extracted {len(df)} records from MySQL")
            return df
        except Exception as e:
            print(f"❌ Error extracting data: {e}")
            return None
        finally:
            connection.close()

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
        
        print(f"✅ Prepared {len(documents)} documents")
        return documents