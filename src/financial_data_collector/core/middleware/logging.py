"""
Logging middleware implementation.
"""

from typing import Any, Callable
import logging
import time
from datetime import datetime
from .base import Middleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(Middleware):
    """Middleware for logging data processing."""
    
    def __init__(self, log_level: int = logging.INFO, log_data: bool = False):
        super().__init__("LoggingMiddleware")
        self.log_level = log_level
        self.log_data = log_data
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with logging."""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        # Log entry
        if self.log_data:
            logger.log(self.log_level, f"[{timestamp}] Processing data: {data}")
        else:
            logger.log(self.log_level, f"[{timestamp}] Processing data (type: {type(data).__name__})")
        
        try:
            # Process through next middleware
            result = await next_middleware()
            
            # Log completion
            processing_time = time.time() - start_time
            if self.log_data:
                logger.log(self.log_level, f"[{timestamp}] Completed processing: {result} (took {processing_time:.3f}s)")
            else:
                logger.log(self.log_level, f"[{timestamp}] Completed processing (took {processing_time:.3f}s)")
            
            return result
            
        except Exception as e:
            # Log error
            processing_time = time.time() - start_time
            logger.error(f"[{timestamp}] Error processing data: {e} (took {processing_time:.3f}s)")
            raise


class PerformanceMiddleware(Middleware):
    """Middleware for performance monitoring."""
    
    def __init__(self, threshold_seconds: float = 1.0):
        super().__init__("PerformanceMiddleware")
        self.threshold_seconds = threshold_seconds
        self._stats = {
            "total_processed": 0,
            "total_time": 0.0,
            "slow_operations": 0
        }
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with performance monitoring."""
        start_time = time.time()
        
        try:
            result = await next_middleware()
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self._stats["total_processed"] += 1
            self._stats["total_time"] += processing_time
            
            # Check for slow operations
            if processing_time > self.threshold_seconds:
                self._stats["slow_operations"] += 1
                logger.warning(f"Slow operation detected: {processing_time:.3f}s (threshold: {self.threshold_seconds}s)")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._stats["total_processed"] += 1
            self._stats["total_time"] += processing_time
            raise
    
    def get_stats(self) -> dict:
        """Get performance statistics."""
        stats = self._stats.copy()
        if stats["total_processed"] > 0:
            stats["average_time"] = stats["total_time"] / stats["total_processed"]
        else:
            stats["average_time"] = 0.0
        return stats
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self._stats = {
            "total_processed": 0,
            "total_time": 0.0,
            "slow_operations": 0
        }
