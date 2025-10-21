"""
Event definitions and data structures.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum
import uuid


class EventType(Enum):
    """Event type enumeration."""
    DATA_COLLECTED = "data_collected"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR = "error"
    MODULE_STARTED = "module_started"
    MODULE_STOPPED = "module_stopped"
    CONFIG_CHANGED = "config_changed"
    HEALTH_CHECK = "health_check"


@dataclass
class Event:
    """Base event class."""
    
    name: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "name": self.name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata
        }


@dataclass
class DataCollectedEvent(Event):
    """Event fired when data is collected."""
    
    def __init__(self, data: Any, source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.DATA_COLLECTED.value,
            data=data,
            source=source,
            metadata=metadata or {}
        )


@dataclass
class TaskCompletedEvent(Event):
    """Event fired when a task is completed."""
    
    def __init__(self, task_id: str, result: Any, source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.TASK_COMPLETED.value,
            data={"task_id": task_id, "result": result},
            source=source,
            metadata=metadata or {}
        )


@dataclass
class TaskFailedEvent(Event):
    """Event fired when a task fails."""
    
    def __init__(self, task_id: str, error: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.TASK_FAILED.value,
            data={"task_id": task_id, "error": error},
            source=source,
            metadata=metadata or {}
        )


@dataclass
class ErrorEvent(Event):
    """Event fired when an error occurs."""
    
    def __init__(self, error: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.ERROR.value,
            data={"error": error},
            source=source,
            metadata=metadata or {}
        )


@dataclass
class ModuleStartedEvent(Event):
    """Event fired when a module starts."""
    
    def __init__(self, module_name: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.MODULE_STARTED.value,
            data={"module_name": module_name},
            source=source,
            metadata=metadata or {}
        )


@dataclass
class ModuleStoppedEvent(Event):
    """Event fired when a module stops."""
    
    def __init__(self, module_name: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.MODULE_STOPPED.value,
            data={"module_name": module_name},
            source=source,
            metadata=metadata or {}
        )


@dataclass
class ConfigChangedEvent(Event):
    """Event fired when configuration changes."""
    
    def __init__(self, config_key: str, old_value: Any, new_value: Any, source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.CONFIG_CHANGED.value,
            data={"config_key": config_key, "old_value": old_value, "new_value": new_value},
            source=source,
            metadata=metadata or {}
        )


@dataclass
class HealthCheckEvent(Event):
    """Event fired during health checks."""
    
    def __init__(self, module_name: str, status: str, details: Dict[str, Any], source: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(
            name=EventType.HEALTH_CHECK.value,
            data={"module_name": module_name, "status": status, "details": details},
            source=source,
            metadata=metadata or {}
        )
