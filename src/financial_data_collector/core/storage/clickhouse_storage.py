"""
ClickHouse storage implementation for financial data collector.

Provides ClickHouse backend for storing financial data, news, and crawl tasks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

try:
    from clickhouse_driver import Client as ClickHouseClient
    from clickhouse_driver.errors import Error as ClickHouseError
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    ClickHouseClient = None
    ClickHouseError = Exception
    CLICKHOUSE_AVAILABLE = False

from ..interfaces import BaseStorage
from ..events import EventBus
from ..events.events import DataCollectedEvent
from .data_models import FinancialData, DataType

logger = logging.getLogger(__name__)


class ClickHouseStorage(BaseStorage):
    """ClickHouse storage for financial data collector."""

    def __init__(self, name: str = "ClickHouseStorage", config: Dict[str, Any] = None):
        super().__init__(name)
        if not CLICKHOUSE_AVAILABLE:
            raise ImportError("ClickHouse driver not installed. Run `pip install clickhouse-driver`")
        
        self.config = config or {}
        self.config.setdefault('host', 'clickhouse')
        self.config.setdefault('port', 9000)
        self.config.setdefault('database', 'financial_data')
        self.config.setdefault('user', 'default')
        self.config.setdefault('password', '')
        self.config.setdefault('batch_size', 1000)
        
        # Add debug logging
        import logging
        logger = logging.getLogger(__name__)
        
        self.client: Optional[ClickHouseClient] = None
        self.event_bus: Optional[EventBus] = None
        self._connected = False
        self._initialized = False
        
        self.host = self.config['host']
        self.port = self.config['port']
        self.database = self.config['database']
        self.username = self.config['user']
        self.password = self.config['password']
        self.batch_size = self.config['batch_size']
        #logger.error(f"ClickHouse connection parameters - User: '{self.username}', Password: '{self.password}', Host: '{self.host}', Port: {self.port}, DB: '{self.database}'")
        

    async def initialize(self) -> None:
        """Initialize ClickHouse storage: connect, create database and tables."""
        await self._connect()
        await self._initialize_database()
        await self._create_tables()
        self._initialized = True
        logger.info(f"ClickHouseStorage initialized successfully.")

    async def _connect(self) -> None:
        """Connect to ClickHouse server."""
        loop = asyncio.get_event_loop()

        def _sync_connect():
            self.client = ClickHouseClient(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                connect_timeout=10,
                send_receive_timeout=30
            )
            self.client.execute("SELECT 1")
        
        await loop.run_in_executor(None, _sync_connect)
        self._connected = True
        logger.info(f"Connected to ClickHouse at {self.host}:{self.port}")

    async def _initialize_database(self) -> None:
        """Create database if not exists."""
        self.client.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        logger.info(f"Database '{self.database}' is ready.")

    async def _create_tables(self) -> None:
        """Create necessary tables."""
        self.client.execute(f"""
        CREATE TABLE IF NOT EXISTS tv_klines_minute (
            symbol String,
            timestamp DateTime,
            open Float64,
            high Float64,
            low Float64,
            close Float64,
            volume Float64,
            turnover Float64,
            update_time DateTime DEFAULT now(),
            create_time DateTime DEFAULT now()
        ) ENGINE = ReplacingMergeTree(update_time)
        PARTITION BY toYYYYMMDD(timestamp)
        ORDER BY (symbol, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """)
        logger.info("Table 'tv_klines_minute' is ready.")

    async def insert_kline_data(self, kline_data: Union[FinancialData, List[FinancialData]]) -> int:
        """Batch insert K-line data into ClickHouse."""
        if not kline_data:
            return 0
        if isinstance(kline_data, FinancialData):
            kline_data = [kline_data]

        # Prepare batch data as list of lists
        batch = [
            [
                item.symbol,
                item.timestamp,
                item.open,
                item.high,
                item.low,
                item.close,
                item.volume,
                getattr(item, 'turnover', 0.0),
                datetime.now(),
                datetime.now()
            ]
            for item in kline_data
        ]

        inserted_rows = 0
        loop = asyncio.get_event_loop()
        for i in range(0, len(batch), self.batch_size):
            sub_batch = batch[i:i+self.batch_size]

            def _sync_insert():
                self.client.execute(
                    "INSERT INTO tv_klines_minute (symbol, timestamp, open, high, low, close, volume, turnover, update_time, create_time) VALUES",
                    sub_batch
                )
            await loop.run_in_executor(None, _sync_insert)
            inserted_rows += len(sub_batch)

        # Publish event after insertion
        if self.event_bus:
            await self.event_bus.publish(DataCollectedEvent(
                source=self.name,
                data_type=DataType.KLINE,
                count=inserted_rows,
                timestamp=datetime.now()
            ))
        logger.info(f"Inserted {inserted_rows} K-line records.")
        return inserted_rows

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus

    async def health_check(self) -> Dict[str, Any]:
        """Simple health check."""
        try:
            result = self.client.execute("SELECT 1")
            return {"status": "healthy", "message": "ClickHouse is responsive"} if result else {"status": "unhealthy"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}
