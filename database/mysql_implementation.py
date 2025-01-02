from flask import Flask, request, jsonify
from mysql.connector import connect, Error
from typing import Dict, Any, Optional

class MySQLDatabase:
    def __init__(self):
        self.connection = None
        
    def connect(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Connect to MySQL database"""
        try:
            self.connection = connect(
                host=credentials.get('host', 'localhost'),
                user=credentials.get('user'),
                password=credentials.get('password'),
                database=credentials.get('dbname'),
                port=credentials.get('port', 3306)
            )
            return True, None
        except Error as e:
            return False, str(e)

    def disconnect(self) -> None:
        """Disconnect from MySQL database"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_tables(self) -> list:
        """Get all tables from the database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    table_name,
                    (SELECT COUNT(*) FROM information_schema.columns 
                     WHERE table_schema = DATABASE() 
                     AND table_name = t.table_name) as column_count,
                    0 as table_size
                FROM information_schema.tables t
                WHERE table_schema = DATABASE()
                ORDER BY table_name;
            """)
            tables = [{"name": row[0], "columns": row[1], "size": row[2]} 
                     for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Error as e:
            print(f"Error getting tables: {e}")
            return []

    def get_table_data(self, table_name: str) -> Dict[str, Any]:
        """Get data from a specific table"""
        try:
            cursor = self.connection.cursor()
            
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE()
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = [(row[0], row[1]) for row in cursor.fetchall()]
            
            # Get table data
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 100")
            rows = cursor.fetchall()
            
            cursor.close()
            return {
                "columns": [{"name": col[0], "type": col[1]} for col in columns],
                "data": rows
            }
        except Error as e:
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
                "results": results
            }
        except Error as e:
            raise Exception(f"Query execution error: {str(e)}")