from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class DomainEvent:
    event_id: str
    timestamp: datetime
    data: dict

@dataclass
class KlineDataCollectedEvent(DomainEvent):
    """K线数据采集完成事件"""
    symbol: str
    interval: str

@dataclass
class StockSymbolCollectedEvent(DomainEvent):
    """股票代码采集完成事件"""
    exchange: str