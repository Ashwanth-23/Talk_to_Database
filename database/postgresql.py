# postgresql.py
from typing import Dict, Any, Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

class PostgreSQLDatabase:
    def __init__(self):
        self.connection = None
        
    def connect(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                dbname=credentials.get('dbname'),
                user=credentials.get('user'),
                password=credentials.get('password'),
                host=credentials.get('host', 'localhost'),
                port=credentials.get('port', 5432)
            )
            return True, None
        except psycopg2.Error as e:
            return False, str(e)

    def disconnect(self) -> None:
        """Disconnect from PostgreSQL database"""
        if self.connection:
            self.connection.close()

    def get_tables(self) -> list:
        """Get all tables from the database with their details"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    table_name,
                    (SELECT COUNT(*) FROM information_schema.columns 
                     WHERE table_schema = 'public' 
                     AND table_name = t.table_name) as column_count,
                    pg_total_relation_size(quote_ident(table_name)) as table_size
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [{"name": row[0], "columns": row[1], "size": row[2]} 
                     for row in cursor.fetchall()]
            cursor.close()
            return tables
        except psycopg2.Error as e:
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
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = [(row[0], row[1]) for row in cursor.fetchall()]
            
            # Get table data
            query = sql.SQL("SELECT * FROM {} LIMIT 100").format(
                sql.Identifier(table_name)
            )
            cursor.execute(query)
            rows = cursor.fetchall()
            
            cursor.close()
            return {
                "columns": [{"name": col[0], "type": col[1]} for col in columns],
                "data": rows
            }
        except psycopg2.Error as e:
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
        except psycopg2.Error as e:
            raise Exception(f"Query execution error: {str(e)}")

    def validate_connection(self) -> bool:
        """Validate if the connection is still active"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            return True
        except (psycopg2.Error, AttributeError):
            return False