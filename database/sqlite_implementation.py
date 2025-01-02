import sqlite3
from typing import Dict, Any, Optional
from pathlib import Path

class SQLiteDatabase:
    def __init__(self):
        self.connection = None
        
    def connect(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Connect to SQLite database"""
        try:
            db_path = credentials.get('dbname')
            if not db_path:
                return False, "Database path is required"
            
            # Ensure the database file exists
            if not Path(db_path).exists():
                return False, f"Database file {db_path} does not exist"
                
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            return True, None
        except sqlite3.Error as e:
            return False, str(e)

    def disconnect(self) -> None:
        """Disconnect from SQLite database"""
        if self.connection:
            self.connection.close()

    def get_tables(self) -> list:
        """Get all tables from the database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    name as table_name,
                    (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count,
                    0 as table_size
                FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
            """)
            tables = [{"name": row[0], "columns": row[1], "size": row[2]} 
                     for row in cursor.fetchall()]
            cursor.close()
            return tables
        except sqlite3.Error as e:
            print(f"Error getting tables: {e}")
            return []

    def get_table_data(self, table_name: str) -> Dict[str, Any]:
        """Get data from a specific table"""
        try:
            cursor = self.connection.cursor()
            
            # Get column information
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = [(row[1], row[2]) for row in cursor.fetchall()]
            
            # Get table data
            cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 100")
            rows = cursor.fetchall()
            
            cursor.close()
            return {
                "columns": [{"name": col[0], "type": col[1]} for col in columns],
                "data": [tuple(row) for row in rows]
            }
        except sqlite3.Error as e:
            raise Exception(f"Error fetching table data: {str(e)}")

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get results for SELECT queries
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE)
                self.connection.commit()
                columns = []
                results = []
            
            cursor.close()
            return {
                "columns": columns,
                "results": [tuple(row) for row in results]
            }
        except sqlite3.Error as e:
            raise Exception(f"Query execution error: {str(e)}")