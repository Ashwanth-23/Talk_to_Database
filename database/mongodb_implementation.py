from pymongo import MongoClient
from typing import Dict, Any, Optional
import pandas as pd

class MongoDatabase:
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Connect to MongoDB database"""
        try:
            host = credentials.get('host', 'localhost')
            port = credentials.get('port', 27017)
            username = credentials.get('user')
            password = credentials.get('password')
            database = credentials.get('dbname')

            # Construct MongoDB URI
            if username and password:
                uri = f"mongodb+srv://{username}:{password}@{host}/{database}"
            else:
                uri = f"mongodb://{host}:{port}/{database}"

            self.client = MongoClient(uri)
            self.db = self.client[database]
            
            # Test connection
            self.client.server_info()
            return True, None
        except Exception as e:
            return False, str(e)

    def disconnect(self) -> None:
        """Disconnect from MongoDB database"""
        if self.client:
            self.client.close()

    def get_tables(self) -> list:
        """Get all collections from the database"""
        try:
            collections = self.db.list_collection_names()
            tables = []
            for coll_name in collections:
                count = self.db[coll_name].count_documents({})
                # Get a sample document to estimate fields
                sample = self.db[coll_name].find_one()
                field_count = len(sample.keys()) if sample else 0
                tables.append({
                    "name": coll_name,
                    "columns": field_count,
                    "size": count
                })
            return tables
        except Exception as e:
            print(f"Error getting collections: {e}")
            return []

    def get_table_data(self, table_name: str) -> Dict[str, Any]:
        """Get data from a specific collection"""
        try:
            # Get documents
            cursor = self.db[table_name].find().limit(100)
            documents = list(cursor)
            
            # Convert to pandas DataFrame for easier handling
            df = pd.DataFrame(documents)

            # Handle empty collection case
            if not documents:
                return {
                    "columns": [],
                "data": []
                }
            
            # Convert ObjectId to string and handle nested documents
            def process_document(doc):
                processed = {}
                for key, value in doc.items():
                    if key == '_id':
                        processed[key] = str(value)
                    elif isinstance(value, dict):
                        processed[key] = str(value)  # Convert nested docs to string
                    elif isinstance(value, list):
                        processed[key] = str(value)  # Convert arrays to string
                    else:
                        processed[key] = value
                return processed
            
            # Process all documents
            processed_docs = [process_document(doc) for doc in documents]

            # Get column types - convert all to string type for consistent display
            columns = [{"name": str(col), "type": "string"} for col in df.columns]
            
            # Convert DataFrame to list of tuples
            data = [tuple(str(cell) if cell is not None else "NULL" for cell in row) 
                   for row in df.values]
            
            return {
                "columns": columns,
                "data": data
            }
        except Exception as e:
            raise Exception(f"Error fetching collection data: {str(e)}")
            return {
            "columns": [],
            "data": []
                }

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a MongoDB query and return results"""
        try:
            print(query)
            # Convert natural language to MongoDB query using OpenAI
            # For now, we'll assume the query is already in MongoDB format
            import json
            query_dict = json.loads(query)
            
            collection_name = query_dict.get("collection")
            operation = query_dict.get("operation")
            
            if not collection_name or not operation:
                raise ValueError("Query must specify collection and operation")
            
            collection = self.db[collection_name]
            
            if operation == "find":
                filter_dict = query_dict.get("filter", {})
                projection = query_dict.get("projection", None)
                cursor = collection.find(filter_dict, projection)
                documents = list(cursor)
                
                # Convert to pandas DataFrame
                df = pd.DataFrame(documents)
                if '_id' in df.columns:
                    df['_id'] = df['_id'].astype(str)
                
                columns = list(df.columns)
                results = [tuple(row) for row in df.values]
                
                return {
                    "columns": columns,
                    "results": results
                }
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            raise Exception(f"Query execution error: {str(e)}")