"""
Database crawler implementation for financial data collection.

This module provides database-based data collection capabilities for
various financial databases and data warehouses.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json

import asyncpg
import aiosqlite
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ..interfaces import BaseModule, DataCollectorInterface, DatabaseInterface
from ..events import EventBus, DataCollectedEvent

logger = logging.getLogger(__name__)


class DatabaseCollector(BaseModule, DataCollectorInterface, DatabaseInterface):
    """
    Database-based data collector for financial data sources.
    
    Supports multiple database types:
    - PostgreSQL
    - SQLite
    - MySQL
    - Oracle
    - SQL Server
    """
    
    def __init__(self, name: str = "DatabaseCollector"):
        super().__init__(name)
        self.supported_sources = ["database", "postgresql", "sqlite", "mysql", "oracle", "sqlserver"]
        self.engine: Optional[Any] = None
        self.session_factory: Optional[Any] = None
        self.event_bus: Optional[EventBus] = None
        self.config: Dict[str, Any] = {}
        
        # Database connection pool
        self.connection_pool: Optional[Any] = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the database collector with configuration."""
        self.config = config
        
        # Database configuration
        self.database_url = config.get("database_url")
        self.database_type = config.get("database_type", "postgresql")
        self.pool_size = config.get("pool_size", 10)
        self.max_overflow = config.get("max_overflow", 20)
        self.pool_timeout = config.get("pool_timeout", 30)
        self.pool_recycle = config.get("pool_recycle", 3600)
        
        # Query configuration
        self.query_timeout = config.get("query_timeout", 30)
        self.batch_size = config.get("batch_size", 1000)
        self.max_rows = config.get("max_rows", 10000)
        
        # Financial data specific settings
        self.financial_tables = config.get("financial_tables", {
            "stocks": "stock_data",
            "quotes": "quote_data", 
            "news": "financial_news",
            "companies": "company_data"
        })
        
        logger.info(f"DatabaseCollector initialized for {self.database_type}")
    
    async def start(self) -> None:
        """Start the database collector."""
        if not self._initialized:
            raise RuntimeError("DatabaseCollector not initialized")
        
        if not self.database_url:
            raise ValueError("Database URL is required")
        
        try:
            # Create database engine based on type
            if self.database_type == "postgresql":
                self.engine = create_async_engine(
                    self.database_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    echo=False
                )
            elif self.database_type == "sqlite":
                self.engine = create_async_engine(
                    self.database_url,
                    echo=False
                )
            else:
                # For other database types, use synchronous engine
                self.engine = create_engine(
                    self.database_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    echo=False
                )
            
            # Create session factory
            if self.database_type in ["postgresql", "sqlite"]:
                self.session_factory = sessionmaker(
                    self.engine, 
                    class_=AsyncSession, 
                    expire_on_commit=False
                )
            else:
                self.session_factory = sessionmaker(
                    self.engine, 
                    expire_on_commit=False
                )
            
            # Test connection
            await self._test_connection()
            
            self._started = True
            logger.info("DatabaseCollector started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start DatabaseCollector: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the database collector."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
        
        self._started = False
        logger.info("DatabaseCollector stopped")
    
    def get_supported_sources(self) -> List[str]:
        """Get supported data source types."""
        return self.supported_sources
    
    async def collect_data(self, source: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data from a database source."""
        if not self.engine:
            raise RuntimeError("DatabaseCollector not started")
        
        query = config.get("query")
        table_name = config.get("table_name")
        filters = config.get("filters", {})
        limit = config.get("limit", self.max_rows)
        
        if not query and not table_name:
            raise ValueError("Either query or table_name is required")
        
        try:
            # Execute query
            if query:
                result = await self.execute_query(query, config.get("params", {}))
            else:
                # Build query from table and filters
                result = await self._query_table(table_name, filters, limit)
            
            # Process the result
            processed_data = await self._process_database_result(result, config)
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish_async(
                    DataCollectedEvent(
                        data=processed_data,
                        source=f"database_collector:{source}",
                        metadata={"table_name": table_name, "query": query[:100] if query else None}
                    )
                )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to collect data from database: {e}")
            raise
    
    async def execute_query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a database query."""
        if not self.engine:
            raise RuntimeError("DatabaseCollector not started")
        
        try:
            if self.database_type in ["postgresql", "sqlite"]:
                # Async execution
                async with self.engine.begin() as conn:
                    result = await conn.execute(text(query), params)
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    return [dict(zip(columns, row)) for row in rows]
            else:
                # Synchronous execution
                with self.engine.connect() as conn:
                    result = conn.execute(text(query), params)
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    return [dict(zip(columns, row)) for row in rows]
                    
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """Create a database table."""
        if not self.engine:
            raise RuntimeError("DatabaseCollector not started")
        
        try:
            # Build CREATE TABLE statement
            columns = []
            for column_name, column_type in schema.items():
                columns.append(f"{column_name} {column_type}")
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            
            if self.database_type in ["postgresql", "sqlite"]:
                async with self.engine.begin() as conn:
                    await conn.execute(text(create_sql))
            else:
                with self.engine.connect() as conn:
                    conn.execute(text(create_sql))
                    conn.commit()
            
            logger.info(f"Table {table_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    async def insert_record(self, table_name: str, data: Dict[str, Any]) -> str:
        """Insert a record into a table."""
        if not self.engine:
            raise RuntimeError("DatabaseCollector not started")
        
        try:
            # Build INSERT statement
            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f":{col}" for col in columns]
            
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            if self.database_type in ["postgresql", "sqlite"]:
                async with self.engine.begin() as conn:
                    result = await conn.execute(text(insert_sql), data)
                    return str(result.lastrowid) if hasattr(result, 'lastrowid') else "success"
            else:
                with self.engine.connect() as conn:
                    result = conn.execute(text(insert_sql), data)
                    conn.commit()
                    return str(result.lastrowid) if hasattr(result, 'lastrowid') else "success"
                    
        except Exception as e:
            logger.error(f"Failed to insert record into {table_name}: {e}")
            raise
    
    async def store_data(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data and return storage key."""
        # This would typically store data in a specific table
        table_name = metadata.get("table_name", "financial_data")
        
        record_data = {
            "key": key,
            "data": json.dumps(data) if not isinstance(data, str) else data,
            "metadata": json.dumps(metadata),
            "created_at": datetime.now().isoformat()
        }
        
        return await self.insert_record(table_name, record_data)
    
    async def retrieve_data(self, key: str) -> Any:
        """Retrieve data by key."""
        query = "SELECT data FROM financial_data WHERE key = :key"
        result = await self.execute_query(query, {"key": key})
        
        if result:
            return json.loads(result[0]["data"])
        return None
    
    async def delete_data(self, key: str) -> bool:
        """Delete data by key."""
        query = "DELETE FROM financial_data WHERE key = :key"
        try:
            await self.execute_query(query, {"key": key})
            return True
        except Exception as e:
            logger.error(f"Failed to delete data with key {key}: {e}")
            return False
    
    async def list_data(self, prefix: str = "") -> List[str]:
        """List stored data keys."""
        if prefix:
            query = "SELECT key FROM financial_data WHERE key LIKE :prefix"
            params = {"prefix": f"{prefix}%"}
        else:
            query = "SELECT key FROM financial_data"
            params = {}
        
        result = await self.execute_query(query, params)
        return [row["key"] for row in result]
    
    async def _query_table(self, table_name: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Query a table with filters."""
        # Build WHERE clause
        where_conditions = []
        params = {}
        
        for column, value in filters.items():
            if isinstance(value, list):
                placeholders = [f":{column}_{i}" for i in range(len(value))]
                where_conditions.append(f"{column} IN ({', '.join(placeholders)})")
                for i, v in enumerate(value):
                    params[f"{column}_{i}"] = v
            else:
                where_conditions.append(f"{column} = :{column}")
                params[column] = value
        
        # Build query
        query = f"SELECT * FROM {table_name}"
        if where_conditions:
            query += f" WHERE {' AND '.join(where_conditions)}"
        query += f" LIMIT {limit}"
        
        return await self.execute_query(query, params)
    
    async def _process_database_result(self, result: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process database query result."""
        processed_data = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "row_count": len(result),
            "data": result
        }
        
        # Add financial data analysis if applicable
        if result:
            processed_data["analysis"] = self._analyze_financial_data(result)
        
        return processed_data
    
    def _analyze_financial_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze financial data for insights."""
        if not data:
            return {}
        
        analysis = {
            "total_records": len(data),
            "columns": list(data[0].keys()) if data else []
        }
        
        # Analyze numeric columns
        numeric_columns = []
        for column in analysis["columns"]:
            if any(isinstance(row.get(column), (int, float)) for row in data if row.get(column) is not None):
                numeric_columns.append(column)
        
        if numeric_columns:
            analysis["numeric_columns"] = numeric_columns
            
            # Calculate basic statistics for numeric columns
            for column in numeric_columns:
                values = [row.get(column) for row in data if row.get(column) is not None]
                if values:
                    analysis[f"{column}_stats"] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values)
                    }
        
        return analysis
    
    async def _test_connection(self) -> None:
        """Test database connection."""
        try:
            if self.database_type in ["postgresql", "sqlite"]:
                async with self.engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
            else:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            
            logger.info("Database connection test successful")
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self.engine:
            return {
                "status": "unhealthy",
                "message": "Database engine not initialized",
                "details": {"engine_initialized": False}
            }
        
        try:
            # Test database connection
            await self._test_connection()
            
            # Get database info
            db_info = await self._get_database_info()
            
            return {
                "status": "healthy",
                "message": "DatabaseCollector is working",
                "details": {
                    "engine_initialized": True,
                    "connection_successful": True,
                    "database_type": self.database_type,
                    "database_info": db_info
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "details": {
                    "engine_initialized": True,
                    "connection_successful": False,
                    "error": str(e)
                }
            }
    
    async def _get_database_info(self) -> Dict[str, Any]:
        """Get database information."""
        try:
            if self.database_type == "postgresql":
                query = """
                SELECT 
                    current_database() as database_name,
                    version() as version,
                    current_user as current_user,
                    inet_server_addr() as server_address
                """
            elif self.database_type == "sqlite":
                query = "SELECT sqlite_version() as version"
            else:
                query = "SELECT 1 as test"
            
            result = await self.execute_query(query, {})
            return result[0] if result else {}
            
        except Exception as e:
            logger.warning(f"Failed to get database info: {e}")
            return {"error": str(e)}
