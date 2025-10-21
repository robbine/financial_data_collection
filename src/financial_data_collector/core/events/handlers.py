"""
Event handlers and decorators.
"""

from typing import Callable, Any, Optional
import asyncio
import functools
from .events import Event


class EventHandler:
    """Base class for event handlers."""
    
    def __init__(self, event_name: str, handler_func: Callable[[Event], None]):
        self.event_name = event_name
        self.handler_func = handler_func
    
    def handle(self, event: Event) -> None:
        """Handle the event."""
        self.handler_func(event)


class AsyncEventHandler:
    """Base class for async event handlers."""
    
    def __init__(self, event_name: str, handler_func: Callable[[Event], Any]):
        self.event_name = event_name
        self.handler_func = handler_func
    
    async def handle(self, event: Event) -> None:
        """Handle the event asynchronously."""
        await self.handler_func(event)


def event_handler(event_name: str):
    """
    Decorator for registering event handlers.
    
    Args:
        event_name: Name of the event to handle
    """
    def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
        @functools.wraps(func)
        def wrapper(event: Event) -> None:
            return func(event)
        
        wrapper._event_name = event_name
        wrapper._is_event_handler = True
        return wrapper
    
    return decorator


def async_event_handler(event_name: str):
    """
    Decorator for registering async event handlers.
    
    Args:
        event_name: Name of the event to handle
    """
    def decorator(func: Callable[[Event], Any]) -> Callable[[Event], Any]:
        @functools.wraps(func)
        async def wrapper(event: Event) -> Any:
            return await func(event)
        
        wrapper._event_name = event_name
        wrapper._is_async_event_handler = True
        return wrapper
    
    return decorator


class EventHandlerRegistry:
    """Registry for managing event handlers."""
    
    def __init__(self):
        self._handlers: dict = {}
        self._async_handlers: dict = {}
    
    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        if handler.event_name not in self._handlers:
            self._handlers[handler.event_name] = []
        self._handlers[handler.event_name].append(handler)
    
    def register_async_handler(self, handler: AsyncEventHandler) -> None:
        """Register an async event handler."""
        if handler.event_name not in self._async_handlers:
            self._async_handlers[handler.event_name] = []
        self._async_handlers[handler.event_name].append(handler)
    
    def get_handlers(self, event_name: str) -> list:
        """Get handlers for an event."""
        return self._handlers.get(event_name, [])
    
    def get_async_handlers(self, event_name: str) -> list:
        """Get async handlers for an event."""
        return self._async_handlers.get(event_name, [])
    
    def unregister_handler(self, event_name: str, handler: EventHandler) -> None:
        """Unregister an event handler."""
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    def unregister_async_handler(self, event_name: str, handler: AsyncEventHandler) -> None:
        """Unregister an async event handler."""
        if event_name in self._async_handlers:
            try:
                self._async_handlers[event_name].remove(handler)
            except ValueError:
                pass
