"""
ClickHouse storage implementation for financial data collector.

This module provides a ClickHouse storage backend that implements
the StorageInterface and ModuleInterface for storing financial data,
news data, and crawl tasks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager

try:
    from clickhouse_driver import Client as ClickHouseClient
    from clickhouse_driver.errors import Error as ClickHouseError
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    ClickHouseClient = None
    ClickHouseError = Exception
    CLICKHOUSE_AVAILABLE = False

from ..interfaces import ModuleInterface, StorageInterface, BaseStorage
from ..events import EventBus
from ..events.events import DataCollectedEvent, TaskCompletedEvent
from .data_models import FinancialData, NewsData, CrawlTask, DataType, TaskStatus

logger = logging.getLogger(__name__)


class ClickHouseStorage(BaseStorage):
    """ClickHouse storage implementation for financial data."""
    
    def __init__(self, name: str = "ClickHouseStorage", config: Dict[str, Any] = None):
        super().__init__(name)
        self.config = config or {}
        # Set default values for configuration parameters
        self.config.setdefault('host', 'clickhouse')
        self.config.setdefault('port', 9000)
        self.config.setdefault('database', 'financial_data')
        self.config.setdefault('user', 'default')
        self.config.setdefault('password', '')
        logger.info(f"Initializing ClickHouse storage with parameters: {self.config}")
        
        # Test ClickHouse connectivity
        import socket
        from contextlib import closing
        
        try:
            # Resolve hostname
            host_ip = socket.gethostbyname(self.config['host'])
            logger.info(f"Resolved ClickHouse host {self.config['host']} to {host_ip}")
            
            # Check port connectivity
            with closing(socket.socket(socket.AF_INET, socket.SOCK_TCP)) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host_ip, self.config['port']))
                if result == 0:
                    logger.info(f"Successfully connected to ClickHouse at {host_ip}:{self.config['port']}")
                else:
                    logger.error(f"Failed to connect to ClickHouse at {host_ip}:{self.config['port']}, error code: {result}")
        except socket.gaierror as e:
            logger.error(f"Failed to resolve ClickHouse host {self.config['host']}: {e}")
        except Exception as e:
            logger.error(f"Error testing ClickHouse connectivity: {e}")
        self.client: Optional[ClickHouseClient] = None
        self.event_bus: Optional[EventBus] = None
        self._connected = False
        self._initialized = False
        
        # Connection parameters
        self.host = 'clickhouse'  # 强制设置为服务名
        self.port = self.config.get('port', 9000)
        self.database = self.config.get('database', 'financial_data')
        self.username = self.config.get('username', 'default')
        self.password = self.config.get('password', '')
        self.secure = self.config.get('secure', False)
        self.verify = self.config.get('verify', False)
        
        # Connection pool settings
        self.max_connections = self.config.get('max_connections', 10)
        self.connection_timeout = self.config.get('connection_timeout', 10)
        self.query_timeout = self.config.get('query_timeout', 30)
        
        # Storage settings
        self.compression = self.config.get('compression', True)
        self.batch_size = self.config.get('batch_size', 1000)
        self.flush_interval = self.config.get('flush_interval', 5)  # seconds
        
        # Data validation
        if not CLICKHOUSE_AVAILABLE:
            raise ImportError(
                "ClickHouse driver not available. Install with: pip install clickhouse-driver"
            )
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize ClickHouse storage with configuration."""
        logger.critical("Entering ClickHouseStorage.initialize() method")
        try:
            logger.info(f"Starting ClickHouse storage initialization")
            self.config = config.copy()
            logger.info(f"Received config: {self.config}")
            logger.info(f"Initializing ClickHouse storage: {self.name}")
            
            # Set default values for configuration parameters
            self.config.setdefault('host', 'clickhouse')
            self.config.setdefault('port', 9000)
            self.config.setdefault('database', 'financial_data')
            self.config.setdefault('user', 'default')
            self.config.setdefault('password', '')
            
            # Update configuration from defaults

            # Update connection parameters from new config
            self.host = self.config.get('host')
            if not self.host:
                raise ValueError("ClickHouse host is not configured. Please check your configuration file.")
            logger.critical(f"Using ClickHouse host: {self.host}")
            self.port = self.config.get('port', 9000)
            self.database = self.config.get('database', 'financial_data')
            self.username = self.config.get('username', 'default')
            self.password = self.config.get('password', '')
            self.secure = self.config.get('secure', False)
            self.verify = self.config.get('verify', False)
            logger.info(f"ClickHouse connection parameters - host: {self.host}, port: {self.port}, database: {self.database}, username: {self.username}, password: {'***' if self.password else ''}, secure: {self.secure}, verify: {self.verify}")

            # Connect to ClickHouse
            await self._connect()
            
            # Initialize database and tables
            await self._initialize_database()
            await self._create_tables()
            
            self._initialized = True
            logger.info(f"ClickHouse storage initialized successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse storage: {e}")
            raise
    
    async def start(self) -> None:
        """Start the ClickHouse storage service."""
        if not self._initialized:
            raise RuntimeError("Storage not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Starting ClickHouse storage: {self.name}")
            
            # Test connection
            await self._test_connection()
            
            self._connected = True
            logger.info(f"ClickHouse storage started successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to start ClickHouse storage: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the ClickHouse storage service."""
        try:
            logger.info(f"Stopping ClickHouse storage: {self.name}")
            
            if self.client:
                self.client.disconnect()
                self.client = None
            
            self._connected = False
            logger.info(f"ClickHouse storage stopped: {self.name}")
            
        except Exception as e:
            logger.error(f"Error stopping ClickHouse storage: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on ClickHouse storage."""
        try:
            if not self._connected:
                return {
                    "status": "unhealthy",
                    "message": "Not connected to ClickHouse",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Test basic query
            start_time = datetime.now()
            result = await self._execute_query("SELECT 1")
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Get database stats
            stats = await self._get_database_stats()
            
            return {
                "status": "healthy",
                "message": "ClickHouse storage is operational",
                "response_time_seconds": response_time,
                "database_stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"ClickHouse health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    # StorageInterface implementation
    
    async def store_data(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data in ClickHouse."""
        try:
            if isinstance(data, FinancialData):
                return await self.store_financial_data(data, metadata.get('task_id'))
            elif isinstance(data, NewsData):
                return await self.store_news_data(data, metadata.get('task_id'))
            elif isinstance(data, CrawlTask):
                return await self.store_crawl_task(data)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
                
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            raise
    
    async def retrieve_data(self, key: str) -> Any:
        """Retrieve data from ClickHouse by key."""
        try:
            # Parse key to determine data type and ID
            if key.startswith('financial_'):
                return await self.get_financial_data_by_id(key)
            elif key.startswith('news_'):
                return await self.get_news_data_by_id(key)
            elif key.startswith('task_'):
                return await self.get_crawl_task_by_id(key)
            else:
                raise ValueError(f"Unknown data key format: {key}")
                
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            raise
    
    async def delete_data(self, key: str) -> bool:
        """Delete data from ClickHouse by key."""
        try:
            # Parse key to determine table and ID
            if key.startswith('financial_'):
                return await self._delete_financial_data(key)
            elif key.startswith('news_'):
                return await self._delete_news_data(key)
            elif key.startswith('task_'):
                return await self._delete_crawl_task(key)
            else:
                raise ValueError(f"Unknown data key format: {key}")
                
        except Exception as e:
            logger.error(f"Failed to delete data: {e}")
            return False
    
    async def list_data(self, prefix: str = "") -> List[str]:
        """List data keys with optional prefix."""
        try:
            # This is a simplified implementation
            # In practice, you might want to maintain a separate index
            query = "SELECT DISTINCT symbol FROM financial_data"
            if prefix:
                query += f" WHERE symbol LIKE '{prefix}%'"
            
            result = await self._execute_query(query)
            return [f"financial_{row[0]}" for row in result]
            
        except Exception as e:
            logger.error(f"Failed to list data: {e}")
            return []
    
    # Financial data specific methods
    
    async def store_financial_data(self, data: FinancialData, task_id: str = None) -> str:
        """Store financial data in ClickHouse."""
        try:
            # Insert into financial_data table
            query = """
            INSERT INTO financial_data (
                symbol, data_type, price, open_price, high_price, low_price, close_price,
                volume, market_cap, change, change_percent, timestamp, source, metadata, task_id
            ) VALUES
            """
            
            values = [
                data.symbol, data.data_type.value, data.price, data.open_price,
                data.high_price, data.low_price, data.close_price, data.volume,
                data.market_cap, data.change, data.change_percent, data.timestamp,
                data.source, str(data.metadata), task_id
            ]
            
            await self._execute_insert(query, values)
            
            # Update latest_prices table
            await self._update_latest_prices(data)
            
            # Publish event
            if self.event_bus:
                event = DataCollectedEvent(
                    data=data.dict(),
                    source="clickhouse_storage",
                    metadata={"task_id": task_id, "symbol": data.symbol}
                )
                await self.event_bus.publish_async(event)
            
            data_key = f"financial_{data.symbol}_{data.timestamp.isoformat()}"
            logger.info(f"Stored financial data: {data_key}")
            return data_key
            
        except Exception as e:
            logger.error(f"Failed to store financial data: {e}")
            raise
    
    async def store_news_data(self, data: NewsData, task_id: str = None) -> str:
        """Store news data in ClickHouse."""
        try:
            query = """
            INSERT INTO news_data (
                title, content, url, symbols, sentiment, category, published_at,
                source, author, language, timestamp, metadata, task_id
            ) VALUES
            """
            
            values = [
                data.title, data.content, data.url, data.symbols, data.sentiment,
                data.category, data.published_at, data.source, data.author,
                data.language, data.timestamp, str(data.metadata), task_id
            ]
            
            await self._execute_insert(query, values)
            
            # Publish event
            if self.event_bus:
                event = DataCollectedEvent(
                    data=data.dict(),
                    source="clickhouse_storage",
                    metadata={"task_id": task_id, "symbols": data.symbols}
                )
                await self.event_bus.publish_async(event)
            
            data_key = f"news_{hash(data.url)}_{data.timestamp.isoformat()}"
            logger.info(f"Stored news data: {data_key}")
            return data_key
            
        except Exception as e:
            logger.error(f"Failed to store news data: {e}")
            raise
    
    async def store_crawl_task(self, task: CrawlTask) -> str:
        """Store crawl task in ClickHouse."""
        try:
            query = """
            INSERT INTO crawl_tasks (
                task_id, url, status, crawler_type, priority, config,
                created_at, started_at, completed_at, result, error,
                retry_count, max_retries, metadata
            ) VALUES
            """
            
            values = [
                task.task_id, task.url, task.status.value, task.crawler_type,
                task.priority, str(task.config), task.created_at, task.started_at,
                task.completed_at, str(task.result) if task.result else None,
                task.error, task.retry_count, task.max_retries, str(task.metadata)
            ]
            
            await self._execute_insert(query, values)
            
            # Publish event
            if self.event_bus and task.is_completed():
                event = TaskCompletedEvent(
                    task_id=task.task_id,
                    result=task.result,
                    source="clickhouse_storage"
                )
                await self.event_bus.publish_async(event)
            
            data_key = f"task_{task.task_id}"
            logger.info(f"Stored crawl task: {data_key}")
            return data_key
            
        except Exception as e:
            logger.error(f"Failed to store crawl task: {e}")
            raise
    
    # Query methods
    
    async def get_latest_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get latest prices for given symbols."""
        try:
            if not symbols:
                return {}
            
            placeholders = ', '.join(['%s'] * len(symbols))
            query = f"""
            SELECT symbol, price, change, change_percent, volume, timestamp
            FROM latest_prices
            WHERE symbol IN ({placeholders})
            """
            
            result = await self._execute_query(query, symbols)
            
            return {
                row[0]: {
                    'price': row[1],
                    'change': row[2],
                    'change_percent': row[3],
                    'volume': row[4],
                    'timestamp': row[5]
                }
                for row in result
            }
            
        except Exception as e:
            logger.error(f"Failed to get latest prices: {e}")
            return {}
    
    async def get_market_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get market summary for the last N hours."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = """
            SELECT 
                COUNT(*) as total_symbols,
                AVG(price) as avg_price,
                AVG(change_percent) as avg_change_percent,
                SUM(volume) as total_volume,
                COUNT(CASE WHEN change > 0 THEN 1 END) as gainers,
                COUNT(CASE WHEN change < 0 THEN 1 END) as losers
            FROM latest_prices
            WHERE timestamp >= %s
            """
            
            result = await self._execute_query(query, [cutoff_time])
            if not result:
                return {}
            
            row = result[0]
            return {
                'total_symbols': row[0],
                'avg_price': float(row[1]) if row[1] else 0,
                'avg_change_percent': float(row[2]) if row[2] else 0,
                'total_volume': row[3],
                'gainers': row[4],
                'losers': row[5],
                'period_hours': hours,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get market summary: {e}")
            return {}
    
    # Event bus integration
    
    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set event bus for publishing events."""
        self.event_bus = event_bus
    
    # Private methods
    
    async def _connect(self) -> None:
        """Connect to ClickHouse server."""
        try:
            self.client = ClickHouseClient(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                secure=self.secure,
                verify=self.verify,
                database=self.database,
                connect_timeout=self.connection_timeout,
                send_receive_timeout=self.query_timeout
            )
            
            # Test connection
            await self._test_connection()
            logger.info(f"Connected to ClickHouse: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test ClickHouse connection."""
        try:
            result = self.client.execute("SELECT 1")
            if not result:
                raise Exception("Connection test failed")
        except Exception as e:
            logger.error(f"ClickHouse connection test failed: {e}")
            raise
    
    async def _initialize_database(self) -> None:
        """Initialize ClickHouse database."""
        try:
            # Create database if not exists
            self.client.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Database '{self.database}' ready")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self) -> None:
        """Create necessary tables in ClickHouse."""
        try:
            # Financial data table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    symbol String,
                    data_type String,
                    price Nullable(Float64),
                    open_price Nullable(Float64),
                    high_price Nullable(Float64),
                    low_price Nullable(Float64),
                    close_price Nullable(Float64),
                    volume Nullable(UInt64),
                    market_cap Nullable(Float64),
                    change Nullable(Float64),
                    change_percent Nullable(Float64),
                    timestamp DateTime,
                    source String,
                    metadata String,
                    task_id Nullable(String)
                ) ENGINE = MergeTree()
                ORDER BY (symbol, timestamp)
                TTL timestamp + INTERVAL 1 YEAR
            """)
            
            # Latest prices table (materialized view)
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS latest_prices (
                    symbol String,
                    price Nullable(Float64),
                    change Nullable(Float64),
                    change_percent Nullable(Float64),
                    volume Nullable(UInt64),
                    timestamp DateTime
                ) ENGINE = ReplacingMergeTree(timestamp)
                ORDER BY symbol
            """)
            
            # News data table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS news_data (
                    title String,
                    content Nullable(String),
                    url String,
                    symbols Array(String),
                    sentiment Nullable(String),
                    category Nullable(String),
                    published_at Nullable(DateTime),
                    source String,
                    author Nullable(String),
                    language String,
                    timestamp DateTime,
                    metadata String,
                    task_id Nullable(String)
                ) ENGINE = MergeTree()
                ORDER BY (source, timestamp)
                TTL timestamp + INTERVAL 6 MONTH
            """)
            
            # Crawl tasks table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS crawl_tasks (
                    task_id String,
                    url String,
                    status String,
                    crawler_type String,
                    priority UInt8,
                    config String,
                    created_at DateTime,
                    started_at Nullable(DateTime),
                    completed_at Nullable(DateTime),
                    result Nullable(String),
                    error Nullable(String),
                    retry_count UInt8,
                    max_retries UInt8,
                    metadata String
                ) ENGINE = MergeTree()
                ORDER BY (created_at, task_id)
                TTL created_at + INTERVAL 1 MONTH
            """)
            
            # Create materialized view for latest prices
            self.client.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS latest_prices_mv
                TO latest_prices AS
                SELECT 
                    symbol,
                    price,
                    change,
                    change_percent,
                    volume,
                    timestamp
                FROM financial_data
                ORDER BY symbol, timestamp DESC
            """)
            
            logger.info("ClickHouse tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def _execute_query(self, query: str, params: List = None) -> List:
        """Execute a SELECT query."""
        try:
            if params:
                result = self.client.execute(query, params)
            else:
                result = self.client.execute(query)
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def _execute_insert(self, query: str, values: List) -> None:
        """Execute an INSERT query."""
        try:
            self.client.execute(query, [values])
        except Exception as e:
            logger.error(f"Insert execution failed: {e}")
            raise
    
    async def _update_latest_prices(self, data: FinancialData) -> None:
        """Update latest prices table."""
        try:
            query = """
            INSERT INTO latest_prices (
                symbol, price, change, change_percent, volume, timestamp
            ) VALUES
            """
            
            values = [
                data.symbol, data.price, data.change, data.change_percent,
                data.volume, data.timestamp
            ]
            
            self.client.execute(query, [values])
            
        except Exception as e:
            logger.warning(f"Failed to update latest prices: {e}")
    
    async def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            # Get table sizes
            query = """
            SELECT 
                table,
                formatReadableSize(sum(bytes)) as size,
                sum(rows) as rows
            FROM system.parts
            WHERE database = %s
            GROUP BY table
            """
            
            result = self.client.execute(query, [self.database])
            
            stats = {
                'tables': {
                    row[0]: {'size': row[1], 'rows': row[2]}
                    for row in result
                }
            }
            
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get database stats: {e}")
            return {}
    
    async def _delete_financial_data(self, key: str) -> bool:
        """Delete financial data by key."""
        try:
            # Extract symbol and timestamp from key
            parts = key.replace('financial_', '').split('_')
            if len(parts) < 2:
                return False
            
            symbol = parts[0]
            timestamp_str = '_'.join(parts[1:])
            
            query = """
            ALTER TABLE financial_data DELETE
            WHERE symbol = %s AND toString(timestamp) = %s
            """
            
            self.client.execute(query, [symbol, timestamp_str])
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete financial data: {e}")
            return False
    
    async def _delete_news_data(self, key: str) -> bool:
        """Delete news data by key."""
        # Similar implementation for news data
        return False
    
    async def _delete_crawl_task(self, key: str) -> bool:
        """Delete crawl task by key."""
        try:
            task_id = key.replace('task_', '')
            query = "ALTER TABLE crawl_tasks DELETE WHERE task_id = %s"
            self.client.execute(query, [task_id])
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete crawl task: {e}")
            return False
    
    async def get_financial_data_by_id(self, key: str) -> Optional[FinancialData]:
        """Get financial data by ID."""
        # Implementation for retrieving financial data
        return None
    
    async def get_news_data_by_id(self, key: str) -> Optional[NewsData]:
        """Get news data by ID."""
        # Implementation for retrieving news data
        return None
    
    async def get_crawl_task_by_id(self, key: str) -> Optional[CrawlTask]:
        """Get crawl task by ID."""
        # Implementation for retrieving crawl task
        return None

