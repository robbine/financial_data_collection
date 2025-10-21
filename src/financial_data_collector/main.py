"""
Main application entry point for the financial data collector.

This module demonstrates the complete modular system integration including:
- Dependency injection setup
- Event system configuration
- Module registration and management
- Health monitoring
- Plugin system initialization
"""

import sys
import os
import asyncio
import logging
import signal
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Logging system initialized with INFO level")

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root.resolve()))

from .core.di import DIContainer
from .core.events import EventBus
from .core.module_manager import ModuleManager, ModuleConfig
from .core.health_checker import HealthMonitor, HealthCheckConfig
from .core.plugins import PluginRegistry
from .core.middleware import MiddlewareRegistry
from .core.interfaces import BaseModule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Logging system initialized with INFO level")


class FinancialDataCollectorApp:
    """Main application class for the financial data collector."""
    
    def __init__(self):
        self.di_container = DIContainer()
        self.event_bus = EventBus()
        self.module_manager = ModuleManager(self.di_container, self.event_bus)
        self.health_monitor = HealthMonitor(self.event_bus)
        self.plugin_registry = PluginRegistry()
        self.middleware_registry = MiddlewareRegistry()
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.shutdown())
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the application."""
        logger.info("Initializing Financial Data Collector...")
        
        # Setup dependency injection
        await self._setup_dependency_injection(config)
        
        # Setup event system
        await self._setup_event_system(config)
        
        # Setup plugins
        await self._setup_plugins(config)
        
        # Setup middleware
        await self._setup_middleware(config)
        
        # Register modules
        await self._register_modules(config)
        
        logger.info("Application initialized successfully")
    
    async def start(self) -> None:
        """Start the application."""
        if self.running:
            logger.warning("Application is already running")
            return
        
        logger.info("Starting Financial Data Collector...")
        
        try:
            # Start health monitoring
            await self.health_monitor.start_monitoring()
            
            # Start all modules
            await self.module_manager.start_all_modules()
            
            self.running = True
            logger.info("Application started successfully")
            
            # Keep running
            await self._run_forever()
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the application."""
        if not self.running:
            return
        
        logger.info("Shutting down Financial Data Collector...")
        
        try:
            # Stop health monitoring
            await self.health_monitor.stop_monitoring()
            
            # Stop all modules
            await self.module_manager.stop_all_modules()
            
            # Stop event bus
            self.event_bus.stop()
            
            self.running = False
            logger.info("Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _setup_dependency_injection(self, config: Dict[str, Any]) -> None:
        """Setup dependency injection container."""
        logger.info("Setting up dependency injection...")
        
        # Register core services
        self.di_container.register_instance(DIContainer, self.di_container)
        self.di_container.register_instance(EventBus, self.event_bus)
        self.di_container.register_instance(ModuleManager, self.module_manager)
        self.di_container.register_instance(HealthMonitor, self.health_monitor)
        self.di_container.register_instance(PluginRegistry, self.plugin_registry)
        self.di_container.register_instance(MiddlewareRegistry, self.middleware_registry)
        
        # Register any additional services from config
        services = config.get('services', {})
        for service_name, service_config in services.items():
            if 'class' in service_config:
                service_class = service_config['class']
                if 'singleton' in service_config and service_config['singleton']:
                    self.di_container.register_singleton(service_class, service_class)
                else:
                    self.di_container.register_factory(service_class, lambda: service_class())
        
        logger.info("Dependency injection setup complete")
    
    async def _setup_event_system(self, config: Dict[str, Any]) -> None:
        """Setup event system."""
        logger.info("Setting up event system...")
        
        # Register event handlers from config
        event_handlers = config.get('event_handlers', {})
        for event_name, handler_config in event_handlers.items():
            if 'handler' in handler_config:
                handler = handler_config['handler']
                self.event_bus.subscribe(event_name, handler)
                logger.info(f"Registered event handler for {event_name}")
        
        logger.info("Event system setup complete")
    
    async def _setup_plugins(self, config: Dict[str, Any]) -> None:
        """Setup plugin system."""
        logger.info("Setting up plugin system...")
        
        # Add discovery paths
        discovery_paths = config.get('plugin_discovery_paths', [])
        for path in discovery_paths:
            self.plugin_registry.add_discovery_path(path)
        
        # Discover plugins
        discovered_plugins = self.plugin_registry.discover_plugins()
        logger.info(f"Discovered {len(discovered_plugins)} plugins: {discovered_plugins}")
        
        # Initialize plugins from config
        plugins = config.get('plugins', {})
        for plugin_name, plugin_config in plugins.items():
            if plugin_name in self.plugin_registry.list_plugins():
                plugin_instance = self.plugin_registry.create_plugin_instance(plugin_name)
                if plugin_instance:
                    plugin_instance.initialize(plugin_config.get('config', {}))
                    logger.info(f"Initialized plugin: {plugin_name}")
        
        logger.info("Plugin system setup complete")
    
    async def _setup_middleware(self, config: Dict[str, Any]) -> None:
        """Setup middleware system."""
        logger.info("Setting up middleware system...")
        # 注册中间件
        middleware_configs = config.get('middleware', {})
        for middleware_name, middleware_config in middleware_configs.items():
            if 'class' in middleware_config and middleware_config.get('enabled', True):
                try:
                    # 动态导入并验证类
                    middleware_class = self.import_string(middleware_config['class'])
                    # 传递配置参数实例化
                    middleware_instance = middleware_class(**middleware_config.get('params', {}))
                    self.middleware_registry.register_middleware(middleware_name, middleware_instance)
                    logger.info(f"Registered middleware: {middleware_name}")
                except Exception as e:
                    logger.error(f"Failed to register middleware {middleware_name}: {str(e)}")
                    # 根据需求选择抛出异常或继续执行
                    # raise

        logger.info("Middleware system setup complete")

    def import_string(self, dotted_path):
        import importlib
        import inspect
        try:
            module_path, class_name = dotted_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            if not inspect.isclass(cls):
                raise TypeError(f"{dotted_path} is not a valid class")
            return cls
        except (ValueError, ImportError, AttributeError) as e:
            raise ImportError(f"Failed to import {dotted_path}: {str(e)}") from e
    
    async def _register_modules(self, config: Dict[str, Any]) -> None:
        """Register modules with the module manager."""
        logger.info("Registering modules...")
        
        # Register modules from config
        modules = config.get('modules', {})
        logger.debug(f"Modules configuration type: {type(modules)}, content: {modules}")

        # 添加模块配置检查
        if not modules:
            logger.warning("No modules configured for registration")
            return
        
        for module_name, module_config in modules.items():
            logger.debug(f"Processing module: {module_name}")
            try:
                if 'class' in module_config:
                    module_class_path = module_config['class']
                    module_class = self.import_string(module_class_path)
                    config_obj = ModuleConfig(
                        name=module_name,
                        enabled=module_config.get('enabled', True),
                        config=module_config.get('config', {}),
                        dependencies=module_config.get('dependencies', []),
                        startup_order=module_config.get('startup_order', 0),
                        shutdown_order=module_config.get('shutdown_order', 0),
                        health_check_interval=module_config.get('health_check_interval', 30),
                        max_restart_attempts=module_config.get('max_restart_attempts', 3),
                        restart_delay=module_config.get('restart_delay', 5)
                    )
                    
                    self.module_manager.register_module(module_name, module_class, config_obj)
                    
                    # Register with health monitor
                    health_config = HealthCheckConfig(
                        enabled=module_config.get('health_check_enabled', True),
                        interval=module_config.get('health_check_interval', 30),
                        timeout=module_config.get('health_check_timeout', 10),
                        retry_count=module_config.get('health_check_retry_count', 3),
                        retry_delay=module_config.get('health_check_retry_delay', 5),
                        alert_threshold=module_config.get('health_check_alert_threshold', 3),
                        recovery_threshold=module_config.get('health_check_recovery_threshold', 2)
                    )
                    
                    self.health_monitor.register_module(
                        module_class(), health_config
                    )
                    
                    logger.info(f"Registered module: {module_name}")
            except Exception as e:
                logger.error(f"Failed to register module {module_name}: {str(e)}", exc_info=True)
                # 继续处理下一个模块
                continue
        
        # Register StorageManager
        from financial_data_collector.core.storage.storage_manager import StorageManager
        storage_config = ModuleConfig(
        name='storage_manager',
        enabled=True,
        config=config.get('storage', {}),
        dependencies=[],
        restart_delay=5
    )
        self.module_manager.register_module('storage_manager', StorageManager, storage_config)

        logger.info("Module registration complete")
    
    async def _run_forever(self) -> None:
        """Keep the application running."""
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()
    
    def get_status(self) -> Dict[str, Any]:
        """Get application status."""
        return {
            'running': self.running,
            'modules': self.module_manager.get_module_status(),
            'system_health': asyncio.run(self.health_monitor.get_system_health()),
            'plugins': self.plugin_registry.list_plugins(),
            'middleware': self.middleware_registry.list_middlewares()
        }


async def main():
    """Main entry point."""
    # Load configuration using ConfigManager
    from src.financial_data_collector.core.config.manager import ConfigManager
    config_manager = ConfigManager()
    config_manager.load_config()
    config = config_manager.get_config()

    # Create and run application
    app = FinancialDataCollectorApp()

    try:
        await app.initialize(config)
        await app.start()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    
    # Create and run application
    app = FinancialDataCollectorApp()
    
    try:
        await app.initialize(config)
        await app.start()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
