from ..events import KlineDataCollectedEvent
from ..storage.storage_adapter import PrimaryFallbackAdapter

class KlineDataPersistenceHandler:
    def __init__(self, storage_adapter: PrimaryFallbackAdapter):
        self.storage_adapter = storage_adapter

    async def handle(self, event: KlineDataCollectedEvent):
        # 实现金融级事务保证
        async with self._create_transaction():
            count = await self.storage_adapter.insert_kline_data(event.data)
            # 记录数据操作审计日志
            self._record_audit_log(event, count)

    async def _create_transaction(self):
        # 实现TCC模式分布式事务
        pass