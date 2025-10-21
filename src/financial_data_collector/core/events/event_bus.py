"""
Event Bus implementation.

Provides a centralized event bus for publishing and subscribing to events.
"""

from typing import Dict, List, Callable, Any, Optional
import asyncio
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from .events import Event

logger = logging.getLogger(__name__)


class EventBus:
    """
    Centralized event bus for publishing and subscribing to events.
    
    Supports both synchronous and asynchronous event handling.
    """
    
    def __init__(self, max_workers: int = 10):
        self._handlers: Dict[str, List[Callable]] = {}
        self._async_handlers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._is_running = True
    
    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            handler: Function to handle the event
        """
        with self._lock:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)
    
    def subscribe_async(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """
        Subscribe to an event with async handler.
        
        Args:
            event_name: Name of the event to subscribe to
            handler: Async function to handle the event
        """
        with self._lock:
            if event_name not in self._async_handlers:
                self._async_handlers[event_name] = []
            self._async_handlers[event_name].append(handler)
    
    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Name of the event to unsubscribe from
            handler: Handler function to remove
        """
        with self._lock:
            if event_name in self._handlers:
                try:
                    self._handlers[event_name].remove(handler)
                except ValueError:
                    pass
            
            if event_name in self._async_handlers:
                try:
                    self._async_handlers[event_name].remove(handler)
                except ValueError:
                    pass
    
    def publish(self, event: Event) -> None:
        """
        Publish an event synchronously.
        
        Args:
            event: The event to publish
        """
        if not self._is_running:
            return
        
        # Handle synchronous handlers
        if event.name in self._handlers:
            for handler in self._handlers[event.name]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event.name}: {e}")
        
        # Handle asynchronous handlers in background
        if event.name in self._async_handlers:
            for handler in self._async_handlers[event.name]:
                self._executor.submit(self._run_async_handler, handler, event)
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: The event to publish
        """
        if not self._is_running:
            return
        
        # Handle synchronous handlers
        if event.name in self._handlers:
            for handler in self._handlers[event.name]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event.name}: {e}")
        
        # Handle asynchronous handlers
        if event.name in self._async_handlers:
            tasks = []
            for handler in self._async_handlers[event.name]:
                tasks.append(self._run_async_handler_await(handler, event))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _run_async_handler(self, handler: Callable, event: Event) -> None:
        """Run async handler in thread pool."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(handler(event))
            loop.close()
        except Exception as e:
            logger.error(f"Error in async event handler for {event.name}: {e}")
    
    async def _run_async_handler_await(self, handler: Callable, event: Event) -> None:
        """Run async handler with await."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in async event handler for {event.name}: {e}")
    
    def get_subscribers(self, event_name: str) -> List[Callable]:
        """
        Get all subscribers for an event.
        
        Args:
            event_name: Name of the event
            
        Returns:
            List of subscriber functions
        """
        with self._lock:
            sync_handlers = self._handlers.get(event_name, [])
            async_handlers = self._async_handlers.get(event_name, [])
            return sync_handlers + async_handlers
    
    def get_all_events(self) -> List[str]:
        """
        Get all registered event names.
        
        Returns:
            List of event names
        """
        with self._lock:
            all_events = set(self._handlers.keys()) | set(self._async_handlers.keys())
            return list(all_events)
    
    def clear_subscribers(self, event_name: Optional[str] = None) -> None:
        """
        Clear subscribers for an event or all events.
        
        Args:
            event_name: Name of the event to clear, or None for all events
        """
        with self._lock:
            if event_name is None:
                self._handlers.clear()
                self._async_handlers.clear()
            else:
                self._handlers.pop(event_name, None)
                self._async_handlers.pop(event_name, None)
    
    def stop(self) -> None:
        """Stop the event bus and cleanup resources."""
        self._is_running = False
        self._executor.shutdown(wait=True)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
