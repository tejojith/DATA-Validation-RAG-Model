from connector_sql import MySQLConnection
import time
from langchain.prompts import PromptTemplate
from chunking import EnhancedChunker
from typing import Dict, List, Optional
import pandas as pd

class SQLExtraction:
    def __init__(self):
        self.source_db_config = None
        self.target_db_config = None

    def configure_databases(self, source_config: Dict, target_config: Optional[Dict] = None):
        """Configure source and target database connections"""
        self.source_db_config = source_config
        self.target_db_config = target_config
    
    def extract_schema_info(self, connection_config: Dict) -> List[Dict]:
        """Extract schema information from database"""
        schema_info = []
        
        with MySQLConnection(**connection_config) as conn:
            # Get tables
            tables_df = conn.execute_query("SHOW TABLES")
            if tables_df is None:
                return schema_info
                
            for _, row in tables_df.iterrows():
                table_name = row.iloc[0]
                
                # Get columns
                columns_df = conn.execute_query(f"DESCRIBE {table_name}")
                
                # Get foreign keys
                fks_df = conn.execute_query(f"""
                    SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}' 
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                
                schema_info.append({
                    'table_name': table_name,
                    'columns': columns_df.to_dict('records') if columns_df is not None else [],
                    'foreign_keys': fks_df.to_dict('records') if fks_df is not None else []
                })
                    
        return schema_info

    def profile_data(self, connection_config: Dict) -> List[Dict]:
        """Generate data profiles for each table"""
        profile_info = []
        
        with MySQLConnection(**connection_config) as conn:
            tables_df = conn.execute_query("SHOW TABLES")
            if tables_df is None:
                return profile_info
                
            for _, table_row in tables_df.iterrows():
                table_name = table_row.iloc[0]
                
                # Basic stats
                count_df = conn.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
                row_count = count_df.iloc[0]['cnt'] if count_df is not None else 0
                
                # Column profiles
                columns_df = conn.execute_query(f"DESCRIBE {table_name}")
                column_profiles = []
                
                if columns_df is not None:
                    for _, col_row in columns_df.iterrows():
                        col_name = col_row['Field']
                        col_type = col_row['Type']
                        
                        # Get sample values and NULL count
                        stats_df = conn.execute_query(f"""
                            SELECT 
                                SUM(CASE WHEN `{col_name}` IS NULL THEN 1 ELSE 0 END) as null_count,
                                COUNT(DISTINCT `{col_name}`) as distinct_count
                            FROM {table_name}
                        """)
                        
                        sample_df = conn.execute_query(f"""
                            SELECT `{col_name}` 
                            FROM {table_name} 
                            WHERE `{col_name}` IS NOT NULL
                            LIMIT 5
                        """)
                        
                        column_profiles.append({
                            'name': col_name,
                            'type': col_type,
                            'null_count': stats_df.iloc[0]['null_count'] if stats_df is not None else 0,
                            'distinct_count': stats_df.iloc[0]['distinct_count'] if stats_df is not None else 0,
                            'sample_values': sample_df[col_name].tolist() if sample_df is not None else []
                        })
                
                profile_info.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'columns': column_profiles
                })
                    
        return profile_info

