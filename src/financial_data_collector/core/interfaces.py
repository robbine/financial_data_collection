"""
Core interfaces and abstract base classes for the financial data collector.

This module defines the interfaces that all modules must implement to ensure
compatibility and interoperability within the system.
"""

from typing import Any, Dict, List, Optional, Union, Callable, AsyncGenerator
from abc import ABC, abstractmethod
import asyncio
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Data source type enumeration."""
    WEB = "web"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"


class DataFormat(Enum):
    """Data format enumeration."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    PARQUET = "parquet"
    TEXT = "text"
    BINARY = "binary"


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Core Module Interfaces

class ModuleInterface(ABC):
    """Base interface for all modules."""
    def __init__(self, name: str):
        self.name = name
        self._initialized = False
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the module with configuration."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the module."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the module."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        pass
    
    def get_name(self) -> str:
        """Get module name."""
        return self.__class__.__name__


# Data Collection Interfaces

class DataCollectorInterface(ModuleInterface):
    """Interface for data collection modules."""
    
    @abstractmethod
    def get_supported_sources(self) -> List[DataSourceType]:
        """Get supported data source types."""
        pass
    
    @abstractmethod
    async def collect_data(self, source: str, config: Dict[str, Any]) -> Any:
        """Collect data from a source."""
        pass
    
    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """Validate if a source is supported."""
        pass


class WebCrawlerInterface(DataCollectorInterface):
    """Interface for web crawler modules."""
    
    @abstractmethod
    async def crawl_url(self, url: str, config: Dict[str, Any]) -> Any:
        """Crawl a specific URL."""
        pass
    
    @abstractmethod
    async def crawl_multiple_urls(self, urls: List[str], config: Dict[str, Any]) -> List[Any]:
        """Crawl multiple URLs."""
        pass
    
    @abstractmethod
    def get_crawl_delay(self) -> float:
        """Get delay between requests."""
        pass


class APICollectorInterface(DataCollectorInterface):
    """Interface for API data collection modules."""
    
    @abstractmethod
    async def make_request(self, endpoint: str, params: Dict[str, Any]) -> Any:
        """Make an API request."""
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> int:
        """Get rate limit per minute."""
        pass
    
    @abstractmethod
    def get_authentication_required(self) -> bool:
        """Check if authentication is required."""
        pass


# Data Processing Interfaces

class DataProcessorInterface(ModuleInterface):
    """Interface for data processing modules."""
    
    @abstractmethod
    async def process_data(self, data: Any, config: Dict[str, Any]) -> Any:
        """Process data."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[DataFormat]:
        """Get supported data formats."""
        pass
    
    @abstractmethod
    def get_processing_capabilities(self) -> List[str]:
        """Get processing capabilities."""
        pass


class DataTransformerInterface(DataProcessorInterface):
    """Interface for data transformation modules."""
    
    @abstractmethod
    async def transform_data(self, data: Any, transformation_config: Dict[str, Any]) -> Any:
        """Transform data."""
        pass
    
    @abstractmethod
    def get_transformation_types(self) -> List[str]:
        """Get supported transformation types."""
        pass


class DataValidatorInterface(DataProcessorInterface):
    """Interface for data validation modules."""
    
    @abstractmethod
    async def validate_data(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema."""
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> List[str]:
        """Get available validation rules."""
        pass


# Storage Interfaces

class StorageInterface(ModuleInterface):
    """Interface for storage modules."""
    
    @abstractmethod
    async def store_data(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data and return storage key."""
        pass
    
    @abstractmethod
    async def retrieve_data(self, key: str) -> Any:
        """Retrieve data by key."""
        pass
    
    @abstractmethod
    async def delete_data(self, key: str) -> bool:
        """Delete data by key."""
        pass
    
    @abstractmethod
    async def list_data(self, prefix: str = "") -> List[str]:
        """List stored data keys."""
        pass


class DatabaseInterface(StorageInterface):
    """Interface for database storage modules."""
    
    @abstractmethod
    async def execute_query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a database query."""
        pass
    
    @abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """Create a database table."""
        pass
    
    @abstractmethod
    async def insert_record(self, table_name: str, data: Dict[str, Any]) -> str:
        """Insert a record into a table."""
        pass


class CacheInterface(StorageInterface):
    """Interface for cache storage modules."""
    
    @abstractmethod
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get data from cache."""
        pass
    
    @abstractmethod
    async def set_cache(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """Set data in cache."""
        pass
    
    @abstractmethod
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        pass


# Task Scheduling Interfaces

class TaskSchedulerInterface(ModuleInterface):
    """Interface for task scheduling modules."""
    
    @abstractmethod
    async def schedule_task(self, task_id: str, task_func: Callable, 
                           schedule: str, config: Dict[str, Any]) -> bool:
        """Schedule a task."""
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status."""
        pass
    
    @abstractmethod
    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        pass


# Configuration Interfaces

class ConfigManagerInterface(ModuleInterface):
    """Interface for configuration management modules."""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        pass


# Monitoring Interfaces

class MonitoringInterface(ModuleInterface):
    """Interface for monitoring modules."""
    
    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        pass
    
    @abstractmethod
    async def log_event(self, event: str, data: Dict[str, Any]) -> None:
        """Log an event."""
        pass
    
    @abstractmethod
    async def get_metrics_history(self, metric_name: str, 
                                start_time: datetime, 
                                end_time: datetime) -> List[Dict[str, Any]]:
        """Get metrics history."""
        pass


# Notification Interfaces

class NotificationInterface(ModuleInterface):
    """Interface for notification modules."""
    
    @abstractmethod
    async def send_notification(self, message: str, 
                              recipients: List[str], 
                              notification_type: str) -> bool:
        """Send a notification."""
        pass
    
    @abstractmethod
    def get_supported_channels(self) -> List[str]:
        """Get supported notification channels."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test notification service connection."""
        pass


# Abstract Base Classes

class BaseModule(ModuleInterface):
    """Base implementation for modules."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        super().__init__(name)
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self._initialized = False
        self._started = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the module."""
        self.config = config
        self._initialized = True
        self.logger.info(f"Module {self.name} initialized")
    
    async def start(self) -> None:
        """Start the module."""
        if not self._initialized:
            raise RuntimeError(f"Module {self.name} not initialized")
        
        self._started = True
        self.logger.info(f"Module {self.name} started")
    
    async def stop(self) -> None:
        """Stop the module."""
        self._started = False
        self.logger.info(f"Module {self.name} stopped")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "timestamp": datetime.now().isoformat()
        }
    
    def is_initialized(self) -> bool:
        """Check if module is initialized."""
        return self._initialized
    
    def is_started(self) -> bool:
        """Check if module is started."""
        return self._started


class BaseDataCollector(BaseModule, DataCollectorInterface):
    """Base implementation for data collectors."""
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(name)
        self.supported_sources: List[DataSourceType] = []
    
    def get_supported_sources(self) -> List[DataSourceType]:
        """Get supported data source types."""
        return self.supported_sources
    
    def validate_source(self, source: str) -> bool:
        """Validate if a source is supported."""
        # Override in subclasses for specific validation
        return True


class BaseDataProcessor(BaseModule, DataProcessorInterface):
    """Base implementation for data processors."""
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(name)
        self.supported_formats: List[DataFormat] = []
        self.processing_capabilities: List[str] = []
    
    def get_supported_formats(self) -> List[DataFormat]:
        """Get supported data formats."""
        return self.supported_formats
    
    def get_processing_capabilities(self) -> List[str]:
        """Get processing capabilities."""
        return self.processing_capabilities


class BaseStorage(BaseModule, StorageInterface):
    """Base implementation for storage modules."""
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(name)
        self.storage_type: str = "generic"
    
    async def store_data(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data and return storage key."""
        raise NotImplementedError("Subclasses must implement store_data")
    
    async def retrieve_data(self, key: str) -> Any:
        """Retrieve data by key."""
        raise NotImplementedError("Subclasses must implement retrieve_data")
    
    async def delete_data(self, key: str) -> bool:
        """Delete data by key."""
        raise NotImplementedError("Subclasses must implement delete_data")
    
    async def list_data(self, prefix: str = "") -> List[str]:
        """List stored data keys."""
        raise NotImplementedError("Subclasses must implement list_data")
