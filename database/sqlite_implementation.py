import sqlite3
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import requests

class SQLiteDatabase:
    def __init__(self):
        self.connection = None
        
    def connect(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Connect to SQLite database using connection string"""
        try:
            connection_string = credentials.get('dbname')
            print("connection_string", connection_string)

            if not connection_string:
                return False, "Connection string is required"
            
            # Parse SQLite Cloud connection string
            try:
                parsed = urlparse(connection_string)
                if parsed.scheme != 'sqlitecloud':
                    return False, "Invalid connection string format. Must start with 'sqlitecloud://'"
                
                # Extract components
                host = parsed.hostname
                port = parsed.port
                database = parsed.path.lstrip('/')
                query_params = parse_qs(parsed.query)
                api_key = query_params.get('apikey', [None])[0]

                print("host", host, "port",port, "database", database,"query_params", query_params, "api_key",api_key)
                
                if not all([host, port, database, api_key]):
                    return False, "Missing required connection parameters"
                
                # Store connection parameters
                self.host = host
                self.port = port
                self.database = database
                self.api_key = api_key
                
                # Test connection by making a simple query
                response = requests.get(
                    f"https://{host}/api/v1/databases/{database}",
                    headers={'Authorization': f'Bearer {api_key}'}
                )
                print("Response",response)
                
                if response.status_code != 200:
                    return False, f"Connection failed: {response.text}"
                
                return True, None
                
            except Exception as e:
                return False, f"Invalid connection string: {str(e)}"
                
        except Exception as e:
            return False, str(e)

    def disconnect(self) -> None:
        """Disconnect from SQLite database"""
        self.api_key = None
        self.host = None
        self.port = None
        self.database = None

    def get_tables(self) -> list:
        """Get all tables from the database"""
        try:
            response = requests.get(
                f"https://{self.host}/api/v1/databases/{self.database}/tables",
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            
            if response.status_code != 200:
                return []
                
            tables_data = response.json()
            return [
                {
                    "name": table["name"],
                    "columns": len(table.get("columns", [])),
                    "size": table.get("rows", 0)
                }
                for table in tables_data
            ]
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []

    def get_table_data(self, table_name: str) -> Dict[str, Any]:
        """Get data from a specific table"""
        try:
            response = requests.post(
                f"https://{self.host}/api/v1/databases/{self.database}/query",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={'query': f"SELECT * FROM {table_name} LIMIT 100"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Query failed: {response.text}")
                
            result = response.json()
            return {
                "columns": [{"name": col["name"], "type": col["type"]} for col in result["columns"]],
                "data": result["rows"]
            }
        except Exception as e:
            raise Exception(f"Error fetching table data: {str(e)}")

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        try:
            response = requests.post(
                f"https://{self.host}/api/v1/databases/{self.database}/query",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={'query': query}
            )
            
            if response.status_code != 200:
                raise Exception(f"Query failed: {response.text}")
                
            result = response.json()
            return {
                "columns": [col["name"] for col in result["columns"]],
                "results": result["rows"]
            }
        except Exception as e:
            raise Exception(f"Query execution error: {str(e)}")