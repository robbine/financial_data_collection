"""
Event System module.

This module provides event-driven architecture capabilities including:
- Event bus for publishing and subscribing to events
- Event handlers for processing events
- Event types and data structures
"""

from .events import (
    Event,
    DataCollectedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    ErrorEvent,
    ModuleStartedEvent,  # 添加此行
    ModuleStoppedEvent,   # 确保已存在
    ConfigChangedEvent,
    HealthCheckEvent
)
from .event_bus import EventBus
from .handlers import EventHandler, AsyncEventHandler
from .events import Event, DataCollectedEvent, TaskCompletedEvent, ErrorEvent
from .domain_events import DomainEvent, KlineDataCollectedEvent, StockSymbolCollectedEvent

__all__ = [
    'EventBus',
    'EventHandler',
    'AsyncEventHandler', 
    'Event',
    'DataCollectedEvent',
    'TaskCompletedEvent',
    'ErrorEvent',
    "ModuleStartedEvent",
    "ModuleStoppedEvent",
    "ConfigChangedEvent",
    "HealthCheckEvent",
    "DomainEvent",
    "KlineDataCollectedEvent",
    "StockSymbolCollectedEvent",
]
