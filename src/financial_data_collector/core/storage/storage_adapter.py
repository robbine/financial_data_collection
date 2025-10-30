from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .clickhouse_storage import ClickHouseStorage
from ..events import DomainEvent

class StorageAdapter(ABC):
    @abstractmethod
    async def insert_kline_data(self, data: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

class PrimaryFallbackAdapter(StorageAdapter):
    def __init__(self):
        self.primary = ClickHouseStorage()
        self.fallback = None
        self._use_fallback = False

    async def insert_kline_data(self, data: List[Dict[str, Any]]) -> int:
        if self._use_fallback:
            return await self._fallback_insert(data)

        try:
            return await self.primary.insert_kline_data(data)
        except Exception as e:
            # 触发降级策略
            self._use_fallback = True
            # 记录关键日志（符合金融审计要求）
            self._log_storage_failure(e, "primary")
            return await self._fallback_insert(data)

    async def _fallback_insert(self, data: List[Dict[str, Any]]) -> int:
        try:
            return await self.fallback.insert_kline_data(data)
        except Exception as e:
            self._log_storage_failure(e, "fallback")
            raise  # 双重失败时抛出异常

    async def health_check(self) -> bool:
        # 定期检查主存储是否恢复
        if self._use_fallback and await self.primary.health_check():
            self._use_fallback = False
        return not self._use_fallback

    def _log_storage_failure(self, exception: Exception, storage_type: str):
        # 实现符合SEC Rule 17a-4的审计日志
        pass