"""
Storage manager for coordinating multiple storage backends.

This module provides a unified interface for managing multiple storage
backends, supporting failover, load balancing, and storage strategies.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type
from enum import Enum

from src.financial_data_collector.core.interfaces import ModuleInterface, StorageInterface
from ..events import EventBus
from ..events.events import DataCollectedEvent, TaskCompletedEvent
from .data_models import FinancialData, NewsData, CrawlTask
from .clickhouse_storage import ClickHouseStorage

logger = logging.getLogger(__name__)


class StorageStrategy(Enum):
    """Storage strategy enumeration."""
    PRIMARY_ONLY = "primary_only"  # Use only primary storage
    REPLICA = "replica"  # Write to primary, read from replica
    SHARD = "shard"  # Distribute data across multiple storages
    FAILOVER = "failover"  # Use backup if primary fails


class StorageManager(ModuleInterface):
    """Manager for coordinating multiple storage backends."""
    
    def __init__(self, name: str = "StorageManager", config: Dict[str, Any] = None):
        super().__init__(name)
        self.config = config or {}
        self.event_bus: Optional[EventBus] = None
        
        # Storage backends
        self._storages: Dict[str, StorageInterface] = {}
        self._primary_storage: Optional[str] = None
        self._replica_storages: List[str] = []
        self._backup_storages: List[str] = []
        
        # Storage strategy
        self.strategy = StorageStrategy(
            self.config.get('strategy', StorageStrategy.PRIMARY_ONLY.value)
        )
        
        # Configuration
        self.auto_failover = self.config.get('auto_failover', True)
        self.retry_count = self.config.get('retry_count', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        
        # Health monitoring
        self._storage_health: Dict[str, bool] = {}
        self._last_health_check = {}
        
        # Performance metrics
        self._metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'storage_operations': {}
        }
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize storage manager with configuration."""
        try:
            logger.info(f"Initializing storage manager: {self.name}")
            
            # Update configuration
            self.config.update(config)
            
            # Initialize storage backends
            await self._initialize_storages()
            
            # Set up health monitoring
            await self._setup_health_monitoring()
            
            self._initialized = True
            logger.info(f"Storage manager initialized successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize storage manager: {e}")
            raise
    
    async def start(self) -> None:
        """Start the storage manager."""
        if not self._initialized:
            raise RuntimeError("Storage manager not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Starting storage manager: {self.name}")
            
            # Start all storage backends
            for name, storage in self._storages.items():
                try:
                    await storage.start()
                    self._storage_health[name] = True
                    logger.info(f"Started storage backend: {name}")
                except Exception as e:
                    logger.error(f"Failed to start storage backend {name}: {e}")
                    self._storage_health[name] = False
            
            # Verify at least one storage is available
            if not any(self._storage_health.values()):
                raise RuntimeError("No storage backends are available")
            
            logger.info(f"Storage manager started successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to start storage manager: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the storage manager."""
        try:
            logger.info(f"Stopping storage manager: {self.name}")
            
            # Stop all storage backends
            for name, storage in self._storages.items():
                try:
                    await storage.stop()
                    logger.info(f"Stopped storage backend: {name}")
                except Exception as e:
                    logger.error(f"Error stopping storage backend {name}: {e}")
            
            logger.info(f"Storage manager stopped: {self.name}")
            
        except Exception as e:
            logger.error(f"Error stopping storage manager: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage manager and all backends."""
        try:
            health_status = {
                "manager_status": "healthy",
                "total_storages": len(self._storages),
                "healthy_storages": 0,
                "storage_health": {},
                "strategy": self.strategy.value,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check health of all storage backends
            for name, storage in self._storages.items():
                try:
                    backend_health = await storage.health_check()
                    is_healthy = backend_health.get("status") == "healthy"
                    health_status["storage_health"][name] = {
                        "status": backend_health.get("status", "unknown"),
                        "message": backend_health.get("message", ""),
                        "response_time": backend_health.get("response_time_seconds", 0)
                    }
                    
                    if is_healthy:
                        health_status["healthy_storages"] += 1
                        self._storage_health[name] = True
                    else:
                        self._storage_health[name] = False
                        
                except Exception as e:
                    logger.error(f"Health check failed for storage {name}: {e}")
                    health_status["storage_health"][name] = {
                        "status": "unhealthy",
                        "message": str(e),
                        "response_time": 0
                    }
                    self._storage_health[name] = False
            
            # Determine overall manager health
            if health_status["healthy_storages"] == 0:
                health_status["manager_status"] = "unhealthy"
                health_status["message"] = "No healthy storage backends available"
            elif health_status["healthy_storages"] < len(self._storages):
                health_status["manager_status"] = "degraded"
                health_status["message"] = "Some storage backends are unhealthy"
            else:
                health_status["message"] = "All storage backends are healthy"
            
            # Add metrics
            health_status["metrics"] = self._metrics.copy()
            
            return health_status
            
        except Exception as e:
            logger.error(f"Storage manager health check failed: {e}")
            return {
                "manager_status": "unhealthy",
                "message": f"Health check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    # Storage management methods
    
    def register_storage(self, name: str, storage: StorageInterface, 
                        is_primary: bool = False, is_replica: bool = False,
                        is_backup: bool = False) -> None:
        """Register a storage backend."""
        try:
            self._storages[name] = storage
            self._storage_health[name] = False  # Will be updated on health check
            
            if is_primary:
                self._primary_storage = name
            if is_replica:
                self._replica_storages.append(name)
            if is_backup:
                self._backup_storages.append(name)
            
            logger.info(f"Registered storage backend: {name}")
            
        except Exception as e:
            logger.error(f"Failed to register storage backend {name}: {e}")
            raise
    
    def unregister_storage(self, name: str) -> None:
        """Unregister a storage backend."""
        try:
            if name in self._storages:
                del self._storages[name]
                del self._storage_health[name]
                
                # Update storage type lists
                if self._primary_storage == name:
                    self._primary_storage = None
                if name in self._replica_storages:
                    self._replica_storages.remove(name)
                if name in self._backup_storages:
                    self._backup_storages.remove(name)
                
                logger.info(f"Unregistered storage backend: {name}")
            
        except Exception as e:
            logger.error(f"Failed to unregister storage backend {name}: {e}")
    
    def set_storage_strategy(self, strategy: StorageStrategy) -> None:
        """Set the storage strategy."""
        self.strategy = strategy
        logger.info(f"Storage strategy set to: {strategy.value}")
    
    # Storage operations
    
    async def store_data(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data using the configured strategy."""
        try:
            self._metrics['total_operations'] += 1
            
            if self.strategy == StorageStrategy.PRIMARY_ONLY:
                result = await self._store_primary_only(data, key, metadata)
            elif self.strategy == StorageStrategy.REPLICA:
                result = await self._store_with_replica(data, key, metadata)
            elif self.strategy == StorageStrategy.SHARD:
                result = await self._store_sharded(data, key, metadata)
            elif self.strategy == StorageStrategy.FAILOVER:
                result = await self._store_with_failover(data, key, metadata)
            else:
                raise ValueError(f"Unsupported storage strategy: {self.strategy}")
            
            self._metrics['successful_operations'] += 1
            return result
            
        except Exception as e:
            self._metrics['failed_operations'] += 1
            logger.error(f"Failed to store data: {e}")
            raise
    
    async def retrieve_data(self, key: str) -> Any:
        """Retrieve data using the configured strategy."""
        try:
            self._metrics['total_operations'] += 1
            
            if self.strategy == StorageStrategy.PRIMARY_ONLY:
                result = await self._retrieve_primary_only(key)
            elif self.strategy == StorageStrategy.REPLICA:
                result = await self._retrieve_from_replica(key)
            elif self.strategy == StorageStrategy.SHARD:
                result = await self._retrieve_sharded(key)
            elif self.strategy == StorageStrategy.FAILOVER:
                result = await self._retrieve_with_failover(key)
            else:
                raise ValueError(f"Unsupported storage strategy: {self.strategy}")
            
            self._metrics['successful_operations'] += 1
            return result
            
        except Exception as e:
            self._metrics['failed_operations'] += 1
            logger.error(f"Failed to retrieve data: {e}")
            raise
    
    async def delete_data(self, key: str) -> bool:
        """Delete data using the configured strategy."""
        try:
            self._metrics['total_operations'] += 1
            
            if self.strategy == StorageStrategy.PRIMARY_ONLY:
                result = await self._delete_primary_only(key)
            elif self.strategy == StorageStrategy.REPLICA:
                result = await self._delete_with_replica(key)
            elif self.strategy == StorageStrategy.SHARD:
                result = await self._delete_sharded(key)
            elif self.strategy == StorageStrategy.FAILOVER:
                result = await self._delete_with_failover(key)
            else:
                raise ValueError(f"Unsupported storage strategy: {self.strategy}")
            
            self._metrics['successful_operations'] += 1
            return result
            
        except Exception as e:
            self._metrics['failed_operations'] += 1
            logger.error(f"Failed to delete data: {e}")
            return False
    
    async def list_data(self, prefix: str = "") -> List[str]:
        """List data keys using the configured strategy."""
        try:
            self._metrics['total_operations'] += 1
            
            if self.strategy == StorageStrategy.PRIMARY_ONLY:
                result = await self._list_primary_only(prefix)
            elif self.strategy == StorageStrategy.REPLICA:
                result = await self._list_from_replica(prefix)
            elif self.strategy == StorageStrategy.SHARD:
                result = await self._list_sharded(prefix)
            elif self.strategy == StorageStrategy.FAILOVER:
                result = await self._list_with_failover(prefix)
            else:
                raise ValueError(f"Unsupported storage strategy: {self.strategy}")
            
            self._metrics['successful_operations'] += 1
            return result
            
        except Exception as e:
            self._metrics['failed_operations'] += 1
            logger.error(f"Failed to list data: {e}")
            return []
    
    # Financial data specific methods
    
    async def store_financial_data(self, data: FinancialData, task_id: str = None) -> str:
        """Store financial data."""
        metadata = {"task_id": task_id, "data_type": "financial"}
        return await self.store_data(data, f"financial_{data.symbol}", metadata)
    
    async def store_news_data(self, data: NewsData, task_id: str = None) -> str:
        """Store news data."""
        metadata = {"task_id": task_id, "data_type": "news"}
        return await self.store_data(data, f"news_{hash(data.url)}", metadata)
    
    async def store_crawl_task(self, task: CrawlTask) -> str:
        """Store crawl task."""
        metadata = {"data_type": "task"}
        return await self.store_data(task, f"task_{task.task_id}", metadata)
    
    async def get_latest_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get latest prices for given symbols."""
        try:
            # Try primary storage first (usually ClickHouse)
            if self._primary_storage and self._storage_health.get(self._primary_storage):
                storage = self._storages[self._primary_storage]
                if hasattr(storage, 'get_latest_prices'):
                    return await storage.get_latest_prices(symbols)
            
            # Fallback to other storages
            for name, storage in self._storages.items():
                if self._storage_health.get(name) and hasattr(storage, 'get_latest_prices'):
                    return await storage.get_latest_prices(symbols)
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get latest prices: {e}")
            return {}
    
    async def get_market_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get market summary for the last N hours."""
        try:
            # Try primary storage first
            if self._primary_storage and self._storage_health.get(self._primary_storage):
                storage = self._storages[self._primary_storage]
                if hasattr(storage, 'get_market_summary'):
                    return await storage.get_market_summary(hours)
            
            # Fallback to other storages
            for name, storage in self._storages.items():
                if self._storage_health.get(name) and hasattr(storage, 'get_market_summary'):
                    return await storage.get_market_summary(hours)
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get market summary: {e}")
            return {}
    
    # Event bus integration
    
    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set event bus for publishing events."""
        self.event_bus = event_bus
        
        # Set event bus for all storage backends
        for storage in self._storages.values():
            if hasattr(storage, 'set_event_bus'):
                storage.set_event_bus(event_bus)
    
    # Private methods
    
    async def _initialize_storages(self) -> None:
        """Initialize all storage backends."""
        try:
            # Initialize ClickHouse storage if configured
            clickhouse_config = self.config.get('clickhouse', {})
            logger.info(f"ClickHouse config from StorageManager: {clickhouse_config}")
            logger.critical(f"ClickHouse config in StorageManager: {clickhouse_config}")
            if not clickhouse_config.get('host'):
                logger.critical("ClickHouse host is missing in configuration!")
            clickhouse_storage = ClickHouseStorage("ClickHouseStorage", clickhouse_config)
            await clickhouse_storage.initialize(clickhouse_config)
            
            self.register_storage(
                "clickhouse", 
                clickhouse_storage, 
                is_primary=True
            )
            
            logger.info("Initialized ClickHouse storage")
            
            # Initialize other storage backends as needed
            # PostgreSQL, Redis, etc.
            
        except Exception as e:
            logger.error(f"Failed to initialize storages: {e}")
            raise
    
    async def _setup_health_monitoring(self) -> None:
        """Set up health monitoring for storage backends."""
        try:
            # Initial health check
            for name in self._storages.keys():
                self._storage_health[name] = False
                self._last_health_check[name] = datetime.now()
            
            logger.info("Health monitoring setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup health monitoring: {e}")
    
    async def _get_healthy_storage(self, preferred: str = None) -> Optional[StorageInterface]:
        """Get a healthy storage backend."""
        # Try preferred storage first
        if preferred and self._storage_health.get(preferred):
            return self._storages[preferred]
        
        # Try primary storage
        if self._primary_storage and self._storage_health.get(self._primary_storage):
            return self._storages[self._primary_storage]
        
        # Try any healthy storage
        for name, storage in self._storages.items():
            if self._storage_health.get(name):
                return storage
        
        return None
    
    # Storage strategy implementations
    
    async def _store_primary_only(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data using primary storage only."""
        storage = await self._get_healthy_storage(self._primary_storage)
        if not storage:
            raise RuntimeError("No healthy primary storage available")
        
        return await storage.store_data(data, key, metadata)
    
    async def _store_with_replica(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data to primary and replica storages."""
        # Write to primary
        primary_storage = await self._get_healthy_storage(self._primary_storage)
        if not primary_storage:
            raise RuntimeError("No healthy primary storage available")
        
        result = await primary_storage.store_data(data, key, metadata)
        
        # Write to replicas asynchronously
        replica_tasks = []
        for replica_name in self._replica_storages:
            if self._storage_health.get(replica_name):
                replica_storage = self._storages[replica_name]
                replica_tasks.append(replica_storage.store_data(data, key, metadata))
        
        if replica_tasks:
            try:
                await asyncio.gather(*replica_tasks, return_exceptions=True)
            except Exception as e:
                logger.warning(f"Some replica writes failed: {e}")
        
        return result
    
    async def _store_sharded(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data using sharding strategy."""
        # Simple hash-based sharding
        shard_index = hash(key) % len(self._storages)
        shard_names = list(self._storages.keys())
        shard_name = shard_names[shard_index]
        
        storage = await self._get_healthy_storage(shard_name)
        if not storage:
            # Fallback to any healthy storage
            storage = await self._get_healthy_storage()
            if not storage:
                raise RuntimeError("No healthy storage available for sharding")
        
        return await storage.store_data(data, key, metadata)
    
    async def _store_with_failover(self, data: Any, key: str, metadata: Dict[str, Any]) -> str:
        """Store data with failover support."""
        storages_to_try = []
        
        # Add primary storage
        if self._primary_storage:
            storages_to_try.append(self._primary_storage)
        
        # Add backup storages
        storages_to_try.extend(self._backup_storages)
        
        # Try each storage until one succeeds
        last_error = None
        for storage_name in storages_to_try:
            if self._storage_health.get(storage_name):
                try:
                    storage = self._storages[storage_name]
                    result = await storage.store_data(data, key, metadata)
                    return result
                except Exception as e:
                    last_error = e
                    logger.warning(f"Storage {storage_name} failed, trying next: {e}")
                    continue
        
        raise RuntimeError(f"All storage backends failed. Last error: {last_error}")
    
    async def _retrieve_primary_only(self, key: str) -> Any:
        """Retrieve data from primary storage only."""
        storage = await self._get_healthy_storage(self._primary_storage)
        if not storage:
            raise RuntimeError("No healthy primary storage available")
        
        return await storage.retrieve_data(key)
    
    async def _retrieve_from_replica(self, key: str) -> Any:
        """Retrieve data from replica storage."""
        # Try replica storages first
        for replica_name in self._replica_storages:
            if self._storage_health.get(replica_name):
                try:
                    storage = self._storages[replica_name]
                    return await storage.retrieve_data(key)
                except Exception as e:
                    logger.warning(f"Replica {replica_name} failed: {e}")
                    continue
        
        # Fallback to primary
        return await self._retrieve_primary_only(key)
    
    async def _retrieve_sharded(self, key: str) -> Any:
        """Retrieve data from sharded storage."""
        # Try the same shard logic as storage
        shard_index = hash(key) % len(self._storages)
        shard_names = list(self._storages.keys())
        shard_name = shard_names[shard_index]
        
        storage = await self._get_healthy_storage(shard_name)
        if not storage:
            # Try all storages
            for name, storage in self._storages.items():
                if self._storage_health.get(name):
                    try:
                        return await storage.retrieve_data(key)
                    except Exception:
                        continue
            
            raise RuntimeError("Data not found in any storage")
        
        return await storage.retrieve_data(key)
    
    async def _retrieve_with_failover(self, key: str) -> Any:
        """Retrieve data with failover support."""
        storages_to_try = []
        
        # Add primary storage
        if self._primary_storage:
            storages_to_try.append(self._primary_storage)
        
        # Add backup storages
        storages_to_try.extend(self._backup_storages)
        
        # Try each storage until one succeeds
        last_error = None
        for storage_name in storages_to_try:
            if self._storage_health.get(storage_name):
                try:
                    storage = self._storages[storage_name]
                    return await storage.retrieve_data(key)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Storage {storage_name} failed, trying next: {e}")
                    continue
        
        raise RuntimeError(f"Data not found in any storage. Last error: {last_error}")
    
    async def _delete_primary_only(self, key: str) -> bool:
        """Delete data from primary storage only."""
        storage = await self._get_healthy_storage(self._primary_storage)
        if not storage:
            raise RuntimeError("No healthy primary storage available")
        
        return await storage.delete_data(key)
    
    async def _delete_with_replica(self, key: str) -> bool:
        """Delete data from primary and replica storages."""
        # Delete from primary
        primary_storage = await self._get_healthy_storage(self._primary_storage)
        if not primary_storage:
            raise RuntimeError("No healthy primary storage available")
        
        result = await primary_storage.delete_data(key)
        
        # Delete from replicas
        for replica_name in self._replica_storages:
            if self._storage_health.get(replica_name):
                try:
                    replica_storage = self._storages[replica_name]
                    await replica_storage.delete_data(key)
                except Exception as e:
                    logger.warning(f"Failed to delete from replica {replica_name}: {e}")
        
        return result
    
    async def _delete_sharded(self, key: str) -> bool:
        """Delete data from sharded storage."""
        # Same logic as retrieve
        shard_index = hash(key) % len(self._storages)
        shard_names = list(self._storages.keys())
        shard_name = shard_names[shard_index]
        
        storage = await self._get_healthy_storage(shard_name)
        if not storage:
            # Try all storages
            for name, storage in self._storages.items():
                if self._storage_health.get(name):
                    try:
                        if await storage.delete_data(key):
                            return True
                    except Exception:
                        continue
            return False
        
        return await storage.delete_data(key)
    
    async def _delete_with_failover(self, key: str) -> bool:
        """Delete data with failover support."""
        storages_to_try = []
        
        if self._primary_storage:
            storages_to_try.append(self._primary_storage)
        storages_to_try.extend(self._backup_storages)
        
        for storage_name in storages_to_try:
            if self._storage_health.get(storage_name):
                try:
                    storage = self._storages[storage_name]
                    if await storage.delete_data(key):
                        return True
                except Exception as e:
                    logger.warning(f"Storage {storage_name} failed: {e}")
                    continue
        
        return False
    
    async def _list_primary_only(self, prefix: str = "") -> List[str]:
        """List data from primary storage only."""
        storage = await self._get_healthy_storage(self._primary_storage)
        if not storage:
            raise RuntimeError("No healthy primary storage available")
        
        return await storage.list_data(prefix)
    
    async def _list_from_replica(self, prefix: str = "") -> List[str]:
        """List data from replica storage."""
        for replica_name in self._replica_storages:
            if self._storage_health.get(replica_name):
                try:
                    storage = self._storages[replica_name]
                    return await storage.list_data(prefix)
                except Exception as e:
                    logger.warning(f"Replica {replica_name} failed: {e}")
                    continue
        
        return await self._list_primary_only(prefix)
    
    async def _list_sharded(self, prefix: str = "") -> List[str]:
        """List data from all sharded storages."""
        all_keys = set()
        
        for name, storage in self._storages.items():
            if self._storage_health.get(name):
                try:
                    keys = await storage.list_data(prefix)
                    all_keys.update(keys)
                except Exception as e:
                    logger.warning(f"Storage {name} failed: {e}")
        
        return list(all_keys)
    
    async def _list_with_failover(self, prefix: str = "") -> List[str]:
        """List data with failover support."""
        storages_to_try = []
        
        if self._primary_storage:
            storages_to_try.append(self._primary_storage)
        storages_to_try.extend(self._backup_storages)
        
        for storage_name in storages_to_try:
            if self._storage_health.get(storage_name):
                try:
                    storage = self._storages[storage_name]
                    return await storage.list_data(prefix)
                except Exception as e:
                    logger.warning(f"Storage {storage_name} failed: {e}")
                    continue
        
        return []

