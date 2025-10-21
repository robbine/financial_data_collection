"""
Module lifecycle manager for the financial data collector.

This module provides comprehensive module management including:
- Module registration and discovery
- Lifecycle management (start, stop, restart)
- Dependency resolution
- Health monitoring
- Configuration management
"""

from typing import Dict, List, Optional, Any, Type, Callable, Set
import asyncio
import logging
import threading
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .di import DIContainer
from .events import EventBus, ModuleStartedEvent, ModuleStoppedEvent, HealthCheckEvent
from .interfaces import ModuleInterface

logger = logging.getLogger(__name__)


class ModuleState(Enum):
    """Module state enumeration."""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ModuleConfig:
    """Configuration for a module."""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    startup_order: int = 0
    shutdown_order: int = 0
    health_check_interval: int = 30  # seconds
    max_restart_attempts: int = 3
    restart_delay: int = 5  # seconds


@dataclass
class ModuleInfo:
    """Information about a module."""
    name: str
    module_class: Type
    instance: Optional[Any] = None
    state: ModuleState = ModuleState.UNINITIALIZED
    config: ModuleConfig = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    error_message: Optional[str] = None



class ModuleManager:
    """Manager for module lifecycle and operations."""
    
    def __init__(self, di_container: DIContainer, event_bus: EventBus):
        self.di_container = di_container
        self.event_bus = event_bus
        self._modules: Dict[str, ModuleInfo] = {}
        self._module_dependencies: Dict[str, Set[str]] = {}
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
        self._lock = threading.Lock()
        self._running = False
    
    def register_module(self, 
                      name: str, 
                      module_class: Type[ModuleInterface], 
                      config: ModuleConfig) -> None:
        """
        Register a module.
        
        Args:
            name: Module name
            module_class: Module class
            config: Module configuration
        """
        with self._lock:
            if name in self._modules:
                logger.warning(f"Module {name} is already registered, replacing...")
            
            self._modules[name] = ModuleInfo(
                name=name,
                module_class=module_class,
                config=config
            )
            
            # Build dependency graph
            self._module_dependencies[name] = set(config.dependencies)
            
            logger.info(f"Module {name} registered with dependencies: {config.dependencies}")
    
    def unregister_module(self, name: str) -> None:
        """Unregister a module."""
        with self._lock:
            if name in self._modules:
                # Stop module if running
                if self._modules[name].state in [ModuleState.RUNNING, ModuleState.STARTING]:
                    asyncio.create_task(self._stop_module(name))
                
                # Cancel health check task
                if name in self._health_check_tasks:
                    self._health_check_tasks[name].cancel()
                    del self._health_check_tasks[name]
                
                del self._modules[name]
                if name in self._module_dependencies:
                    del self._module_dependencies[name]
                
                logger.info(f"Module {name} unregistered")
    
    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """Get module information."""
        return self._modules.get(name)
    
    def list_modules(self) -> List[str]:
        """List all registered module names."""
        return list(self._modules.keys())
    
    def get_modules_by_state(self, state: ModuleState) -> List[str]:
        """Get modules in a specific state."""
        return [
            name for name, info in self._modules.items()
            if info.state == state
        ]
    
    async def start_all_modules(self) -> None:
        """Start all enabled modules in dependency order."""
        with self._lock:
            if self._running:
                logger.warning("Module manager is already running")
                return
            
            self._running = True
            self._calculate_startup_order()
        
        logger.info("Starting all modules...")
        
        for module_name in self._startup_order:
            if module_name in self._modules:
                await self._start_module(module_name)
        
        # Start health check tasks
        await self._start_health_checks()
        
        logger.info("All modules started")
    
    async def stop_all_modules(self) -> None:
        """Stop all modules in reverse dependency order."""
        with self._lock:
            if not self._running:
                logger.warning("Module manager is not running")
                return
            
            self._running = False
            self._calculate_shutdown_order()
        
        logger.info("Stopping all modules...")
        
        # Stop health check tasks
        await self._stop_health_checks()
        
        # Stop modules in reverse order
        for module_name in reversed(self._shutdown_order):
            if module_name in self._modules:
                await self._stop_module(module_name)
        
        logger.info("All modules stopped")
    
    async def restart_module(self, name: str) -> bool:
        """Restart a specific module."""
        if name not in self._modules:
            logger.error(f"Module {name} not found")
            return False
        
        module_info = self._modules[name]
        
        # Check restart limits
        if module_info.restart_count >= module_info.config.max_restart_attempts:
            logger.error(f"Module {name} has exceeded maximum restart attempts")
            return False
        
        logger.info(f"Restarting module {name}...")
        
        # Stop module
        await self._stop_module(name)
        
        # Wait before restart
        await asyncio.sleep(module_info.config.restart_delay)
        
        # Start module
        success = await self._start_module(name)
        
        if success:
            module_info.restart_count += 1
            logger.info(f"Module {name} restarted successfully")
        else:
            logger.error(f"Failed to restart module {name}")
        
        return success
    
    async def _start_module(self, name: str) -> bool:
        """Start a specific module."""
        module_info = self._modules[name]
        
        if not module_info.config.enabled:
            logger.info(f"Module {name} is disabled, skipping")
            return True
        
        if module_info.state in [ModuleState.RUNNING, ModuleState.STARTING]:
            logger.warning(f"Module {name} is already running or starting")
            return True
        
        try:
            # Check dependencies
            if not await self._check_dependencies(name):
                logger.error(f"Module {name} dependencies not satisfied")
                return False
            
            # Create module instance
            module_info.state = ModuleState.STARTING
            module_info.start_time = datetime.now()
            
            # Get instance from DI container or create new
            try:
                module_info.instance = self.di_container.get(module_info.module_class)
            except:
                module_info.instance = module_info.module_class()
            
            # Initialize module
            await module_info.instance.initialize(module_info.config.config)
            module_info.state = ModuleState.INITIALIZED
            
            # Start module
            await module_info.instance.start()
            module_info.state = ModuleState.RUNNING
            
            # Publish event
            await self.event_bus.publish_async(
                ModuleStartedEvent(module_name=name, source="module_manager")
            )
            
            logger.info(f"Module {name} started successfully")
            return True
            
        except Exception as e:
            module_info.state = ModuleState.ERROR
            module_info.error_message = str(e)
            logger.error(f"Failed to start module {name}: {e}")
            return False
    
    async def _stop_module(self, name: str) -> None:
        """Stop a specific module."""
        module_info = self._modules[name]
        
        if module_info.state not in [ModuleState.RUNNING, ModuleState.STARTING]:
            logger.info(f"Module {name} is not running")
            return
        
        try:
            module_info.state = ModuleState.STOPPING
            
            if module_info.instance:
                await module_info.instance.stop()
            
            module_info.state = ModuleState.STOPPED
            module_info.stop_time = datetime.now()
            
            # Publish event
            await self.event_bus.publish_async(
                ModuleStoppedEvent(module_name=name, source="module_manager")
            )
            
            logger.info(f"Module {name} stopped successfully")
            
        except Exception as e:
            module_info.state = ModuleState.ERROR
            module_info.error_message = str(e)
            logger.error(f"Error stopping module {name}: {e}")
    
    async def _check_dependencies(self, module_name: str) -> bool:
        """Check if module dependencies are satisfied."""
        dependencies = self._module_dependencies.get(module_name, set())
        
        for dep_name in dependencies:
            if dep_name not in self._modules:
                logger.error(f"Module {module_name} dependency {dep_name} not found")
                return False
            
            dep_info = self._modules[dep_name]
            if dep_info.state != ModuleState.RUNNING:
                logger.error(f"Module {module_name} dependency {dep_name} is not running")
                return False
        
        return True
    
    def _calculate_startup_order(self) -> None:
        """Calculate module startup order based on dependencies."""
        self._startup_order = []
        visited = set()
        temp_visited = set()
        
        def visit(module_name: str):
            if module_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {module_name}")
            if module_name in visited:
                return
            
            temp_visited.add(module_name)
            
            # Visit dependencies first
            for dep in self._module_dependencies.get(module_name, set()):
                visit(dep)
            
            temp_visited.remove(module_name)
            visited.add(module_name)
            self._startup_order.append(module_name)
        
        # Visit all modules
        for module_name in self._modules.keys():
            if module_name not in visited:
                visit(module_name)
        
        # Sort by startup_order
        self._startup_order.sort(key=lambda name: self._modules[name].config.startup_order)
    
    def _calculate_shutdown_order(self) -> None:
        """Calculate module shutdown order (reverse of startup)."""
        self._shutdown_order = self._startup_order.copy()
    
    async def _start_health_checks(self) -> None:
        """Start health check tasks for all modules."""
        for module_name, module_info in self._modules.items():
            if module_info.config.enabled and module_info.state == ModuleState.RUNNING:
                task = asyncio.create_task(self._health_check_loop(module_name))
                self._health_check_tasks[module_name] = task
    
    async def _stop_health_checks(self) -> None:
        """Stop all health check tasks."""
        for task in self._health_check_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self._health_check_tasks.values(), return_exceptions=True)
        self._health_check_tasks.clear()
    
    async def _health_check_loop(self, module_name: str) -> None:
        """Health check loop for a module."""
        while self._running and module_name in self._modules:
            try:
                await self._perform_health_check(module_name)
                await asyncio.sleep(self._modules[module_name].config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for module {module_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _perform_health_check(self, module_name: str) -> None:
        """Perform health check for a module."""
        module_info = self._modules[module_name]
        
        if not module_info.instance or module_info.state != ModuleState.RUNNING:
            return
        
        try:
            health_data = await module_info.instance.health_check()
            module_info.last_health_check = datetime.now()
            module_info.health_status = health_data.get('status', 'healthy')
            
            # Publish health check event
            await self.event_bus.publish_async(
                HealthCheckEvent(
                    module_name=module_name,
                    status=module_info.health_status,
                    details=health_data,
                    source="module_manager"
                )
            )
            
        except Exception as e:
            module_info.health_status = 'unhealthy'
            logger.error(f"Health check failed for module {module_name}: {e}")
    
    def get_module_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all modules."""
        status = {}
        
        for name, info in self._modules.items():
            status[name] = {
                'state': info.state.value,
                'enabled': info.config.enabled,
                'start_time': info.start_time.isoformat() if info.start_time else None,
                'stop_time': info.stop_time.isoformat() if info.stop_time else None,
                'restart_count': info.restart_count,
                'last_health_check': info.last_health_check.isoformat() if info.last_health_check else None,
                'health_status': info.health_status,
                'error_message': info.error_message
            }
        
        return status
    
    def is_running(self) -> bool:
        """Check if module manager is running."""
        return self._running
