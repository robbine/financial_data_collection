"""
Storage module for financial data collector.

This module provides storage interfaces and implementations for various
storage backends including ClickHouse, PostgreSQL, Redis, etc.
"""

from .data_models import (
    FinancialData,
    NewsData,
    CrawlTask,
    DataType,
    TaskStatus
)

from .storage_manager import StorageManager
from .clickhouse_storage import ClickHouseStorage

__all__ = [
    'FinancialData',
    'NewsData', 
    'CrawlTask',
    'DataType',
    'TaskStatus',
    'StorageManager',
    'ClickHouseStorage'
]

