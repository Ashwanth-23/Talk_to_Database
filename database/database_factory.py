# database/database_factory.py
from enum import Enum
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class DatabaseType(Enum):
    """Enum for supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"

class BaseDatabase(ABC):
    """Abstract base class defining the interface for all database implementations"""
    
    @abstractmethod
    def connect(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Connect to database"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from database"""
        pass
    
    @abstractmethod
    def get_tables(self) -> list:
        """Get all tables/collections"""
        pass
    
    @abstractmethod
    def get_table_data(self, table_name: str) -> Dict[str, Any]:
        """Get data from specific table"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute database query"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate if connection is active"""
        pass

class DatabaseFactory:
    """Factory class for creating database instances"""
    
    @staticmethod
    def create_database(db_type: str) -> BaseDatabase:
        """
        Create and return appropriate database instance based on type
        
        Args:
            db_type: String identifying the database type
            
        Returns:
            Instance of specific database implementation
            
        Raises:
            ValueError: If database type is not supported
        """
        db_type = db_type.lower()
        
        if db_type == DatabaseType.POSTGRESQL.value:
            from .postgresql import PostgreSQLDatabase
            return PostgreSQLDatabase()
        elif db_type == DatabaseType.MYSQL.value:
            from .mysql_implementation import MySQLDatabase
            return MySQLDatabase()
        elif db_type == DatabaseType.SQLITE.value:
            from .sqlite_implementation import SQLiteDatabase
            return SQLiteDatabase()
        elif db_type == DatabaseType.MONGODB.value:
            from .mongodb_implementation import MongoDatabase
            return MongoDatabase()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

class DatabaseHandler:
    """Handler class that provides unified interface to different databases"""
    
    def __init__(self, db_type: str):
        """
        Initialize database handler with specific database type
        
        Args:
            db_type: String identifying the database type
        """
        self.db = DatabaseFactory.create_database(db_type)
    
    def connect(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Connect to database using provided credentials"""
        return self.db.connect(credentials)
    
    def disconnect(self) -> None:
        """Disconnect from database"""
        self.db.disconnect()
    
    def get_tables(self) -> list:
        """Get all tables/collections from database"""
        return self.db.get_tables()
    
    def get_table_data(self, table_name: str) -> Dict[str, Any]:
        """Get data from specific table"""
        return self.db.get_table_data(table_name)
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute database query"""
        return self.db.execute_query(query)
    
    def validate_connection(self) -> bool:
        """Validate if database connection is active"""
        return self.db.validate_connection()