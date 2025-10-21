"""
Base middleware classes and pipeline implementation.
"""

from typing import Any, Callable, List, Optional
from abc import ABC, abstractmethod
import asyncio
import logging

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """Abstract base class for middleware."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.enabled = True
    
    @abstractmethod
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """
        Process data through this middleware.
        
        Args:
            data: The data to process
            next_middleware: The next middleware in the pipeline
            
        Returns:
            Processed data
        """
        pass
    
    def enable(self) -> None:
        """Enable this middleware."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable this middleware."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if middleware is enabled."""
        return self.enabled


class MiddlewarePipeline:
    """Pipeline for processing data through multiple middleware components."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or "MiddlewarePipeline"
        self._middlewares: List[Middleware] = []
        self._enabled = True
    
    def add_middleware(self, middleware: Middleware, position: Optional[int] = None) -> 'MiddlewarePipeline':
        """
        Add middleware to the pipeline.
        
        Args:
            middleware: The middleware to add
            position: Position to insert at (None for end)
            
        Returns:
            Self for method chaining
        """
        if position is None:
            self._middlewares.append(middleware)
        else:
            self._middlewares.insert(position, middleware)
        return self
    
    def remove_middleware(self, middleware: Middleware) -> 'MiddlewarePipeline':
        """
        Remove middleware from the pipeline.
        
        Args:
            middleware: The middleware to remove
            
        Returns:
            Self for method chaining
        """
        if middleware in self._middlewares:
            self._middlewares.remove(middleware)
        return self
    
    def get_middlewares(self) -> List[Middleware]:
        """Get all middlewares in the pipeline."""
        return self._middlewares.copy()
    
    async def process(self, data: Any) -> Any:
        """
        Process data through the middleware pipeline.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        if not self._enabled:
            return data
        
        async def process_next(index: int, current_data: Any) -> Any:
            if index >= len(self._middlewares):
                return current_data
            
            middleware = self._middlewares[index]
            
            if not middleware.is_enabled():
                return await process_next(index + 1, current_data)
            
            try:
                return await middleware.process(current_data, lambda: process_next(index + 1, current_data))
            except Exception as e:
                logger.error(f"Error in middleware {middleware.name}: {e}")
                raise
        
        return await process_next(0, data)
    
    def enable(self) -> None:
        """Enable the pipeline."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the pipeline."""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if pipeline is enabled."""
        return self._enabled
    
    def clear(self) -> None:
        """Clear all middlewares from the pipeline."""
        self._middlewares.clear()
    
    def __len__(self) -> int:
        """Get number of middlewares in pipeline."""
        return len(self._middlewares)
    
    def __iter__(self):
        """Iterate over middlewares."""
        return iter(self._middlewares)


class MiddlewareRegistry:
    """Registry for managing middleware instances."""
    
    def __init__(self):
        self._middlewares: dict = {}
        self._pipelines: dict = {}
    
    def register_middleware(self, name: str, middleware: Middleware) -> None:
        """Register a middleware."""
        self._middlewares[name] = middleware
    
    def register_pipeline(self, name: str, pipeline: MiddlewarePipeline) -> None:
        """Register a pipeline."""
        self._pipelines[name] = pipeline
    
    def get_middleware(self, name: str) -> Optional[Middleware]:
        """Get a middleware by name."""
        return self._middlewares.get(name)
    
    def get_pipeline(self, name: str) -> Optional[MiddlewarePipeline]:
        """Get a pipeline by name."""
        return self._pipelines.get(name)
    
    def list_middlewares(self) -> List[str]:
        """List all registered middleware names."""
        return list(self._middlewares.keys())
    
    def list_pipelines(self) -> List[str]:
        """List all registered pipeline names."""
        return list(self._pipelines.keys())
