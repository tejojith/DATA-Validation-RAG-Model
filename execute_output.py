import os
import sqlparse
from connect_alchemy import MySQLConnection
from typing import Dict, List
import pandas as pd
from datetime import datetime

class ExecuteOutput:
    def __init__(self, script_filename: str):
        self.script_filename = script_filename
        self.script_path = os.path.join('results', script_filename)
    
    def execute_and_capture_results(self, db_config: Dict) -> List[Dict]:
        """Execute script and capture results for API response"""
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"Script file {self.script_filename} not found")
        
        conn = MySQLConnection(**db_config)
        results = []
        
        try:
            with open(self.script_path, 'r', encoding='utf-8') as file:
                script_content = file.read()
            
            # Parse SQL statements
            statements = sqlparse.split(script_content)
            
            for stmt in statements:
                cleaned = stmt.strip()
                if cleaned and not cleaned.startswith('--'):  # Skip empty and comment lines
                    try:
                        result = conn.execute_query(cleaned)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
                        # Create filename
                        filename = f"outputs/result_{timestamp}.csv"
                        result.to_csv(filename, index=False)

                        if result is not None and not result.empty:
                            results.append({
                                'query': cleaned,
                                'result': result.to_dict('records'),
                                'row_count': len(result),
                                'success': True
                            })
                        else:
                            results.append({
                                'query': cleaned,
                                'result': 'Query executed successfully (no data returned)',
                                'row_count': 0,
                                'success': True
                            })
                    except Exception as e:
                        results.append({
                            'query': cleaned,
                            'error': str(e),
                            'success': False
                        })
        
        except Exception as e:
            results.append({
                'query': 'File reading error',
                'error': str(e),
                'success': False
            })
        finally:
            conn.close()
        
        return results
    
    def execute_final(self, db_config: Dict):
        """Execute script and print results to console (original functionality)"""
        if not os.path.exists(self.script_path):
            print(f"❌ Script file {self.script_filename} not found")
            return
        
        conn = MySQLConnection(**db_config)
        
        try:
            with open(self.script_path, 'r', encoding='utf-8') as file:
                script_content = file.read()
            
            print(f"\n🚀 Executing script: {self.script_filename}")
            print("=" * 60)
            
            # Parse SQL statements
            statements = sqlparse.split(script_content)
            
            for i, stmt in enumerate(statements, 1):
                cleaned = stmt.strip()
                if cleaned and not cleaned.startswith('--'):  # Skip empty and comment lines
                    print(f"\n📝 Query {i}:")
                    print(cleaned)
                    print("-" * 40)
                    
                    try:
                        result = conn.execute_query(cleaned)
                        
                        if result is not None and not result.empty:
                            print(f"✅ Success! ({len(result)} rows)")
                            if len(result) <= 10:  # Show all rows if 10 or fewer
                                print(result.to_string(index=False))
                            else:  # Show first 5 and last 5 if more than 10
                                print("First 5 rows:")
                                print(result.head().to_string(index=False))
                                print("...")
                                print("Last 5 rows:")
                                print(result.tail().to_string(index=False))
                                print(f"({len(result)} total rows)")
                        else:
                            print("✅ Query executed successfully (no data returned)")
                    
                    except Exception as e:
                        print(f"❌ Error: {str(e)}")
        
        except Exception as e:
            print(f"❌ Error reading script file: {str(e)}")
        finally:
            conn.close()
            print("\n" + "=" * 60)
            print("🏁 Script execution completed")
    
    def validate_script(self) -> tuple:
        """Validate if the script file exists and is readable"""
        try:
            if not os.path.exists(self.script_path):
                return False, f"Script file {self.script_filename} not found"
            
            with open(self.script_path, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content.strip():
                    return False, "Script file is empty"
            
            return True, "Script file is valid"
        
        except Exception as e:
            return False, f"Error validating script: {str(e)}"