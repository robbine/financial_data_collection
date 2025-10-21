"""
Health check system for the financial data collector.

This module provides comprehensive health checking capabilities including:
- Individual module health checks
- System-wide health monitoring
- Health check scheduling and reporting
- Alerting and notification integration
"""

from typing import Dict, List, Optional, Any, Callable, Union
import asyncio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from .events import EventBus, HealthCheckEvent
from .interfaces import ModuleInterface

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    module_name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    response_time: float = 0.0
    error: Optional[str] = None


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    enabled: bool = True
    interval: int = 30  # seconds
    timeout: int = 10  # seconds
    retry_count: int = 3
    retry_delay: int = 5  # seconds
    alert_threshold: int = 3  # consecutive failures before alert
    recovery_threshold: int = 2  # consecutive successes to consider recovered


class HealthChecker(ABC):
    """Abstract base class for health checkers."""
    
    @abstractmethod
    async def check_health(self, module: ModuleInterface) -> HealthCheckResult:
        """Perform health check on a module."""
        pass
    
    @abstractmethod
    def get_checker_name(self) -> str:
        """Get the name of this health checker."""
        pass


class BasicHealthChecker(HealthChecker):
    """Basic health checker that calls module's health_check method."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    async def check_health(self, module: ModuleInterface) -> HealthCheckResult:
        """Perform basic health check."""
        start_time = time.time()
        
        try:
            # Call module's health check with timeout
            health_data = await asyncio.wait_for(
                module.health_check(),
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            # Determine status from health data
            status_str = health_data.get('status', 'unknown')
            if status_str == 'healthy':
                status = HealthStatus.HEALTHY
            elif status_str == 'degraded':
                status = HealthStatus.DEGRADED
            elif status_str == 'unhealthy':
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.UNKNOWN
            
            return HealthCheckResult(
                module_name=module.get_name(),
                status=status,
                message=health_data.get('message', 'Health check passed'),
                timestamp=datetime.now(),
                details=health_data,
                response_time=response_time
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                module_name=module.get_name(),
                status=HealthStatus.UNHEALTHY,
                message="Health check timeout",
                timestamp=datetime.now(),
                response_time=time.time() - start_time,
                error="Timeout"
            )
        except Exception as e:
            return HealthCheckResult(
                module_name=module.get_name(),
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def get_checker_name(self) -> str:
        """Get checker name."""
        return "BasicHealthChecker"


class CustomHealthChecker(HealthChecker):
    """Custom health checker with user-defined check function."""
    
    def __init__(self, name: str, check_function: Callable[[ModuleInterface], Any]):
        self.name = name
        self.check_function = check_function
    
    async def check_health(self, module: ModuleInterface) -> HealthCheckResult:
        """Perform custom health check."""
        start_time = time.time()
        
        try:
            result = await self.check_function(module)
            response_time = time.time() - start_time
            
            # Determine status from result
            if isinstance(result, dict):
                status_str = result.get('status', 'healthy')
                message = result.get('message', 'Custom health check passed')
                details = result
            else:
                status_str = 'healthy' if result else 'unhealthy'
                message = 'Custom health check passed' if result else 'Custom health check failed'
                details = {'result': result}
            
            if status_str == 'healthy':
                status = HealthStatus.HEALTHY
            elif status_str == 'degraded':
                status = HealthStatus.DEGRADED
            elif status_str == 'unhealthy':
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.UNKNOWN
            
            return HealthCheckResult(
                module_name=module.get_name(),
                status=status,
                message=message,
                timestamp=datetime.now(),
                details=details,
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheckResult(
                module_name=module.get_name(),
                status=HealthStatus.UNHEALTHY,
                message=f"Custom health check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def get_checker_name(self) -> str:
        """Get checker name."""
        return self.name


class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._modules: Dict[str, ModuleInterface] = {}
        self._health_checkers: Dict[str, HealthChecker] = {}
        self._configs: Dict[str, HealthCheckConfig] = {}
        self._results: Dict[str, List[HealthCheckResult]] = {}
        self._consecutive_failures: Dict[str, int] = {}
        self._consecutive_successes: Dict[str, int] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        self._lock = asyncio.Lock()
    
    def register_module(self, module: ModuleInterface, 
                       config: HealthCheckConfig = None,
                       health_checker: HealthChecker = None) -> None:
        """Register a module for health monitoring."""
        module_name = module.get_name()
        
        self._modules[module_name] = module
        self._configs[module_name] = config or HealthCheckConfig()
        self._health_checkers[module_name] = health_checker or BasicHealthChecker()
        self._results[module_name] = []
        self._consecutive_failures[module_name] = 0
        self._consecutive_successes[module_name] = 0
        
        logger.info(f"Module {module_name} registered for health monitoring")
    
    def unregister_module(self, module_name: str) -> None:
        """Unregister a module from health monitoring."""
        if module_name in self._modules:
            # Cancel monitoring task
            if module_name in self._monitoring_tasks:
                self._monitoring_tasks[module_name].cancel()
                del self._monitoring_tasks[module_name]
            
            # Remove from all tracking
            del self._modules[module_name]
            del self._configs[module_name]
            del self._health_checkers[module_name]
            del self._results[module_name]
            del self._consecutive_failures[module_name]
            del self._consecutive_successes[module_name]
            
            logger.info(f"Module {module_name} unregistered from health monitoring")
    
    async def start_monitoring(self) -> None:
        """Start health monitoring for all registered modules."""
        if self._running:
            logger.warning("Health monitoring is already running")
            return
        
        self._running = True
        
        # Start monitoring tasks for each module
        for module_name in self._modules.keys():
            await self._start_module_monitoring(module_name)
        
        logger.info("Health monitoring started for all modules")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        if not self._running:
            logger.warning("Health monitoring is not running")
            return
        
        self._running = False
        
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        self._monitoring_tasks.clear()
        
        logger.info("Health monitoring stopped")
    
    async def _start_module_monitoring(self, module_name: str) -> None:
        """Start monitoring for a specific module."""
        if module_name in self._monitoring_tasks:
            return
        
        config = self._configs[module_name]
        if not config.enabled:
            logger.info(f"Health monitoring disabled for module {module_name}")
            return
        
        task = asyncio.create_task(self._monitoring_loop(module_name))
        self._monitoring_tasks[module_name] = task
    
    async def _monitoring_loop(self, module_name: str) -> None:
        """Monitoring loop for a module."""
        config = self._configs[module_name]
        
        while self._running and module_name in self._modules:
            try:
                await self._perform_health_check(module_name)
                await asyncio.sleep(config.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error for {module_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _perform_health_check(self, module_name: str) -> None:
        """Perform health check for a module."""
        module = self._modules[module_name]
        health_checker = self._health_checkers[module_name]
        config = self._configs[module_name]
        
        # Perform health check with retries
        result = None
        for attempt in range(config.retry_count):
            try:
                result = await health_checker.check_health(module)
                break
            except Exception as e:
                if attempt < config.retry_count - 1:
                    await asyncio.sleep(config.retry_delay)
                    continue
                else:
                    result = HealthCheckResult(
                        module_name=module_name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed after {config.retry_count} attempts",
                        timestamp=datetime.now(),
                        error=str(e)
                    )
        
        if result:
            await self._process_health_result(module_name, result)
    
    async def _process_health_result(self, module_name: str, result: HealthCheckResult) -> None:
        """Process health check result."""
        async with self._lock:
            # Store result
            self._results[module_name].append(result)
            
            # Keep only recent results (last 100)
            if len(self._results[module_name]) > 100:
                self._results[module_name] = self._results[module_name][-100:]
            
            # Update consecutive counters
            if result.status == HealthStatus.HEALTHY:
                self._consecutive_successes[module_name] += 1
                self._consecutive_failures[module_name] = 0
            else:
                self._consecutive_failures[module_name] += 1
                self._consecutive_successes[module_name] = 0
            
            # Check for alerts
            config = self._configs[module_name]
            if (self._consecutive_failures[module_name] >= config.alert_threshold and
                result.status != HealthStatus.HEALTHY):
                await self._trigger_alert(module_name, result)
            
            # Publish health check event
            await self.event_bus.publish_async(
                HealthCheckEvent(
                    module_name=module_name,
                    status=result.status.value,
                    details={
                        'message': result.message,
                        'response_time': result.response_time,
                        'consecutive_failures': self._consecutive_failures[module_name],
                        'consecutive_successes': self._consecutive_successes[module_name]
                    },
                    source="health_monitor"
                )
            )
    
    async def _trigger_alert(self, module_name: str, result: HealthCheckResult) -> None:
        """Trigger alert for unhealthy module."""
        logger.warning(f"Health alert for module {module_name}: {result.message}")
        
        # Reset consecutive failures to avoid spam
        self._consecutive_failures[module_name] = 0
    
    async def get_module_health(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get health status for a module."""
        if module_name not in self._modules:
            return None
        
        results = self._results.get(module_name, [])
        if not results:
            return {
                'status': 'unknown',
                'message': 'No health checks performed',
                'last_check': None
            }
        
        latest_result = results[-1]
        return {
            'status': latest_result.status.value,
            'message': latest_result.message,
            'last_check': latest_result.timestamp.isoformat(),
            'response_time': latest_result.response_time,
            'consecutive_failures': self._consecutive_failures.get(module_name, 0),
            'consecutive_successes': self._consecutive_successes.get(module_name, 0),
            'total_checks': len(results)
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        if not self._modules:
            return {
                'status': 'unknown',
                'message': 'No modules registered',
                'modules': {}
            }
        
        module_health = {}
        healthy_count = 0
        total_count = len(self._modules)
        
        for module_name in self._modules.keys():
            health = await self.get_module_health(module_name)
            module_health[module_name] = health
            
            if health and health['status'] == 'healthy':
                healthy_count += 1
        
        # Determine overall status
        if healthy_count == total_count:
            overall_status = 'healthy'
        elif healthy_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        return {
            'status': overall_status,
            'message': f'{healthy_count}/{total_count} modules healthy',
            'modules': module_health,
            'summary': {
                'total_modules': total_count,
                'healthy_modules': healthy_count,
                'unhealthy_modules': total_count - healthy_count
            }
        }
    
    async def get_health_history(self, module_name: str, 
                               hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history for a module."""
        if module_name not in self._results:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_results = [
            result for result in self._results[module_name]
            if result.timestamp >= cutoff_time
        ]
        
        return [
            {
                'timestamp': result.timestamp.isoformat(),
                'status': result.status.value,
                'message': result.message,
                'response_time': result.response_time,
                'error': result.error
            }
            for result in recent_results
        ]
    
    def is_monitoring(self) -> bool:
        """Check if health monitoring is running."""
        return self._running
