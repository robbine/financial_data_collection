import sys
import logging
import signal
import asyncio
from typing import Dict, Any, Optional, List
from dependency_injector import containers, providers
from .core.config import ConfigManager
from .core.events import EventBus
from .core.health_checker import HealthMonitor
from .core.metrics import MetricsCollector
from .core.module_manager import ModuleManager
from .core.plugin_registry import PluginRegistry
from .core.storage.storage_adapter import PrimaryFallbackAdapter
from .utils.logging import setup_structured_logging
from .core.events import ModuleStartedEvent, ModuleStoppedEvent, HealthCheckEvent
from .core.exceptions import DependencyError, ConfigError
# 配置日志记录
logger = logging.getLogger(__name__)

class Container(containers.DeclarativeContainer):
    """依赖注入容器，管理应用组件的生命周期和依赖关系。"""
    config = providers.Configuration()
    event_bus = providers.Singleton(EventBus)
    health_monitor = providers.Singleton(HealthMonitor, event_bus=event_bus)
    metrics_collector = providers.Singleton(MetricsCollector)
    module_manager = providers.Singleton(
        ModuleManager,
        di_container=providers.Self(),
        event_bus=event_bus
    )
    plugin_registry = providers.Singleton(PluginRegistry)
    storage_adapter = providers.Singleton(
        PrimaryFallbackAdapter,
        config=config.storage
    )

class FinancialDataCollectorApp:
    """金融数据采集应用主类，实现符合SEC 17a-4和FINRA Rule 4511的量化数据基础设施。

    职责包括：环境初始化、依赖注入配置、服务生命周期编排、数据供应链协调
    和金融级监控指标暴露。
    """
    def __init__(self):
        self.config: Optional[Dict[str, Any]] = None
        self.di_container: Optional[Container] = None
        self.event_bus: Optional[EventBus] = None
        self.module_manager: Optional[ModuleManager] = None
        self.health_monitor: Optional[HealthMonitor] = None
        self._shutdown_event = asyncio.Event()
        self._metrics_collector: Optional[MetricsCollector] = None
        self.plugin_registry: Optional[PluginRegistry] = None

    async def initialize(self) -> None:
        """初始化应用组件和依赖关系。

        Args:
            config_path: 配置文件路径，默认为开发环境配置

        Raises:
            ConfigError: 配置文件加载失败时
            DependencyError: 依赖组件初始化失败时
        """
        # 加载配置文件
        try:
            # 1. 加载配置文件
            config_manager = ConfigManager()
            config_manager.load_config()
            self.config = config_manager.get_config()
            logger.info("Loaded configuration")

            # 2. 设置结构化日志
            await self._setup_logging()

            # 3. 初始化依赖注入容器
            await self._setup_dependency_injection()

            # 4. 初始化模块管理器 ⭐ 关键步骤
            await self._setup_module_manager()

            # 5. 注册系统信号处理器
            self._register_signal_handlers()

            # 6. 初始化健康监控
            await self._setup_health_monitor()

            # 7. 初始化指标收集器
            await self._setup_metrics_collector()

            # 8. 初始化插件注册表
            await self._setup_plugin_registry()

            logger.info("Application initialization completed successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}", exc_info=True)
            raise
    
    async def _setup_logging(self) -> None:
        """设置结构化日志"""
        log_config = self.config.get("logging", {})
        app_config = self.config.get("app", {})
        
        setup_structured_logging(
            log_level=log_config.get("level", "INFO"),
            service_name=app_config.get("name", "financial-data-collector")
        )
        
        logger.info(f"Logging initialized with level: {log_config.get('level', 'INFO')}")


    async def _setup_dependency_injection(self) -> None:
        """配置依赖注入容器并注册核心组件。"""
        self.di_container = Container()
        self.di_container.config.from_dict(self.config)

        # 初始化事件总线
        self.event_bus = self.di_container.event_bus()
        
        # 注册模块生命周期事件监听器
        self.event_bus.subscribe("module_started", self._handle_module_started)
        self.event_bus.subscribe("module_stopped", self._handle_module_stopped)
        self.event_bus.subscribe("module_error", self._handle_module_error)
        self.event_bus.subscribe("health_check", self._handle_module_health_check)
        
        logger.info("Dependency injection container configured")

    async def _setup_module_manager(self) -> None:
        """初始化并配置模块管理器 ⭐ 核心方法"""
        try:
            # 1. 从 DI 容器获取 ModuleManager 实例
            self.module_manager = self.di_container.module_manager()
            
            # 2. 转换配置格式为 ModuleManager 期望的格式
            modules_config = self._convert_modules_config()
            
            if not modules_config.get("modules"):
                logger.warning("No modules configuration found, application may not function properly")
                return
            
            # 3. 初始化 ModuleManager（加载模块定义）
            await self.module_manager.initialize(modules_config)
            
            # 4. 验证必需模块是否已注册
            self._validate_required_modules()
            
            registered_count = len(self.module_manager.list_modules())
            logger.info(f"Module manager initialized with {registered_count} modules")
            
            # 记录已注册的模块
            for module_name in self.module_manager.list_modules():
                module_info = self.module_manager.get_module(module_name)
                logger.debug(
                    f"Module '{module_name}': "
                    f"enabled={module_info.config.enabled}, "
                    f"dependencies={module_info.config.dependencies}"
                )
            
        except ValueError as e:
            logger.error(f"Module configuration error: {e}")
            raise ConfigError(f"Invalid module configuration: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize module manager: {e}", exc_info=True)
            raise DependencyError(f"Module manager initialization failed: {e}")

    def _convert_modules_config(self) -> Dict[str, Any]:
        """
        将当前配置格式转换为 ModuleManager 期望的格式
        
        当前格式:
        modules:
          config_manager:
            class: src.financial_data_collector.core.config.manager.ConfigManager
            enabled: true
            dependencies: []
        
        目标格式:
        modules:
          - name: "config_manager"
            class_path: "src.financial_data_collector.core.config.manager.ConfigManager"
            enabled: true
            config: {}
            dependencies: []
            startup_order: 50
            shutdown_order: 50
            health_check_interval: 30
        """
        source_modules = self.config.get("modules", {})
        
        converted_modules = []
        
        # 定义默认的启动顺序（数字越小越先启动）
        default_startup_order = {
            "config_manager": 10,
            "clickhouse_storage": 20,
            "data_cleaner": 30,
            "task_scheduler": 40,
        }
        
        for module_name, module_config in source_modules.items():
            if not isinstance(module_config, dict):
                logger.warning(f"Invalid module config for '{module_name}', skipping")
                continue
            
            # 提取类路径（可能是 'class' 或 'class_path'）
            class_path = module_config.get("class") or module_config.get("class_path")
            if not class_path:
                logger.warning(f"Module '{module_name}' missing class path, skipping")
                continue
            
            # 构建标准化的模块配置
            converted_module = {
                "name": module_name,
                "class_path": class_path,
                "enabled": module_config.get("enabled", True),
                "config": module_config.get("config", {}),
                "dependencies": module_config.get("dependencies", []),
                "startup_order": module_config.get(
                    "startup_order", 
                    default_startup_order.get(module_name, 50)
                ),
                "shutdown_order": module_config.get("shutdown_order", 50),
                "health_check_interval": module_config.get("health_check_interval", 30),
                "max_restart_attempts": module_config.get("max_restart_attempts", 3),
                "restart_delay": module_config.get("restart_delay", 5)
            }
            
            converted_modules.append(converted_module)
        
        # 按启动顺序排序
        converted_modules.sort(key=lambda m: m["startup_order"])
        
        logger.debug(f"Converted {len(converted_modules)} module configurations")
        
        return {"modules": converted_modules}

    def _validate_required_modules(self) -> None:
        """验证必需模块是否已注册"""
        # 根据你的配置，这些是核心模块
        required_modules = ["config_manager"]
        registered_modules = self.module_manager.list_modules()
        
        missing_modules = [m for m in required_modules if m not in registered_modules]
        
        if missing_modules:
            raise ConfigError(
                f"Required modules not registered: {', '.join(missing_modules)}"
            )
        
        # 验证启用的模块
        enabled_modules = [
            name for name in registered_modules
            if self.module_manager.get_module(name).config.enabled
        ]
        
        logger.info(f"Validated {len(enabled_modules)} enabled modules")

    async def _setup_health_monitor(self) -> None:
        """初始化健康监控"""
        try:
            self.health_monitor = self.di_container.health_monitor()
            await self.health_monitor.start_monitoring()
            logger.info("Health monitor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize health monitor: {e}")
            # 健康监控失败不应阻止应用启动
            self.health_monitor = None

    async def _setup_metrics_collector(self) -> None:
        """初始化指标收集器"""
        try:
            self._metrics_collector = self.di_container.metrics_collector()
            
            app_config = self.config.get("app", {})
            self._metrics_collector.set_system_info({
                'version': app_config.get('version', '1.0.0'),
                'environment': 'development' if app_config.get('debug') else 'production',
                'service': app_config.get('name', 'financial-data-collector')
            })
            
            await self._metrics_collector.start()
            
            # 注册模块状态指标
            self._register_module_metrics()
            
            logger.info("Metrics collector initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize metrics collector: {e}")
            self._metrics_collector = None

    async def _setup_plugin_registry(self) -> None:
        """初始化插件注册表"""
        features = self.config.get('features', {})
        
        if features.get('plugin_registry_wedge', False):
            try:
                self.plugin_registry = self.di_container.plugin_registry()
                if self.plugin_registry:
                    # 检查initialize是否为异步方法
                    if hasattr(self.plugin_registry, 'initialize'):
                        if asyncio.iscoroutinefunction(self.plugin_registry.initialize):
                            await self.plugin_registry.initialize(self.config)
                        else:
                            self.plugin_registry.initialize(self.config)  # 非异步调用
                        logger.info("Plugin registry initialized")
                    else:
                        logger.warning("PluginRegistry has no initialize method")
                    logger.info("Plugin registry initialized")
            except Exception as e:
                logger.error(f"Failed to initialize plugin registry: {e}")
                self.plugin_registry = None
        else:
            self.plugin_registry = None
            logger.info("Plugin registry disabled")

    def _register_module_metrics(self) -> None:
        """注册模块相关的监控指标"""
        if not self._metrics_collector:
            return
        
        try:
            # 注册模块状态指标
            self._metrics_collector.register_gauge(
                "module_status",
                "Module status (0=stopped, 1=running, 2=error)",
                labels=["module_name", "state"]
            )
            
            # 注册模块重启次数指标
            self._metrics_collector.register_counter(
                "module_restart_total",
                "Total number of module restarts",
                labels=["module_name"]
            )
            
            # 注册健康检查失败次数
            self._metrics_collector.register_counter(
                "module_health_check_failures_total",
                "Total number of failed health checks",
                labels=["module_name"]
            )
            
            logger.debug("Module metrics registered")
            
        except Exception as e:
            logger.error(f"Failed to register module metrics: {e}")

    # ========== 事件处理器 ==========

    async def _handle_module_started(self, event: ModuleStartedEvent) -> None:
        """处理模块启动事件"""
        logger.info(f"✓ Module started: {event.module_name}")
        
        # 更新指标
        if self._metrics_collector:
            try:
                self._metrics_collector.set_gauge(
                    "module_status",
                    1.0,
                    labels={"module_name": event.module_name, "state": "running"}
                )
            except Exception as e:
                logger.error(f"Failed to update metrics for {event.module_name}: {e}")
        
        # 更新健康监控
        if self.health_monitor:
            try:
                self.health_monitor.update_component_status(
                    event.module_name,
                    "healthy",
                    {"message": "Module started successfully"}
                )
            except Exception as e:
                logger.error(f"Failed to update health status for {event.module_name}: {e}")

    async def _handle_module_stopped(self, event: ModuleStoppedEvent) -> None:
        """处理模块停止事件"""
        logger.info(f"✗ Module stopped: {event.module_name}")
        
        # 更新指标
        if self._metrics_collector:
            try:
                self._metrics_collector.set_gauge(
                    "module_status",
                    0.0,
                    labels={"module_name": event.module_name, "state": "stopped"}
                )
            except Exception as e:
                logger.error(f"Failed to update metrics for {event.module_name}: {e}")
        
        # 更新健康监控
        if self.health_monitor:
            try:
                self.health_monitor.update_component_status(
                    event.module_name,
                    "stopped",
                    {"message": "Module stopped"}
                )
            except Exception as e:
                logger.error(f"Failed to update health status for {event.module_name}: {e}")

    async def _handle_module_error(self, event: Any) -> None:
        """处理模块错误事件"""
        module_name = getattr(event, 'module_name', 'unknown')
        error_msg = getattr(event, 'error_message', 'Unknown error')
        
        logger.error(f"⚠ Module error in {module_name}: {error_msg}")
        
        # 更新指标
        if self._metrics_collector:
            try:
                self._metrics_collector.set_gauge(
                    "module_status",
                    2.0,
                    labels={"module_name": module_name, "state": "error"}
                )
            except Exception as e:
                logger.error(f"Failed to update metrics for {module_name}: {e}")
        
        # 更新健康监控
        if self.health_monitor:
            try:
                self.health_monitor.update_component_status(
                    module_name,
                    "unhealthy",
                    {"error": error_msg}
                )
            except Exception as e:
                logger.error(f"Failed to update health status for {module_name}: {e}")
        
        # 尝试重启模块
        if self.module_manager:
            asyncio.create_task(self._try_restart_module(module_name))

    async def _handle_module_health_check(self, event: HealthCheckEvent) -> None:
        """处理模块健康检查事件"""
        if event.status == "unhealthy":
            logger.warning(
                f"⚠ Module {event.module_name} health check failed: {event.details}"
            )
            
            if self._metrics_collector:
                try:
                    self._metrics_collector.increment_counter(
                        "module_health_check_failures_total",
                        labels={"module_name": event.module_name}
                    )
                except Exception as e:
                    logger.error(f"Failed to update health check metrics: {e}")

    async def _try_restart_module(self, module_name: str) -> None:
        """尝试重启模块"""
        try:
            logger.info(f"🔄 Attempting to restart module: {module_name}")
            success = await self.module_manager.restart_module(module_name)
            
            if success:
                logger.info(f"✓ Module {module_name} restarted successfully")
                if self._metrics_collector:
                    self._metrics_collector.increment_counter(
                        "module_restart_total",
                        labels={"module_name": module_name}
                    )
            else:
                logger.error(f"✗ Failed to restart module: {module_name}")
                
        except Exception as e:
            logger.error(f"Error restarting module {module_name}: {e}", exc_info=True)

    def _register_signal_handlers(self) -> None:
        """注册系统信号处理器以支持优雅关闭。"""
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._initiate_shutdown)
            
        logger.debug("Signal handlers registered")

    def _initiate_shutdown(self) -> None:
        """启动应用关闭流程。"""
        if not self._shutdown_event.is_set():
            logger.warning("Received shutdown signal, initiating graceful shutdown")
            self._shutdown_event.set()
            asyncio.create_task(self.stop())

    async def start(self) -> None:
        """启动应用服务和处理流程。

        Returns:
            None
        """
        app_config = self.config.get("app", {})
        logger.info(f"🚀 Starting {app_config.get('name', 'Financial Data Collector')}")

        try:
            # 启动所有模块 ⭐
            await self.module_manager.start_all_modules()
            
            logger.info("✓ All modules started successfully")
            
            # 记录模块状态
            module_statuses = self.module_manager.get_module_statuses()
            running_count = sum(
                1 for status in module_statuses
                if status['state'] == 'running'
            )
            logger.info(f"📊 Module Status: {running_count}/{len(module_statuses)} running")
            
            for module in module_statuses:
                name = module['name']
                state = module['state']
                state_emoji = {
                    'running': '✓',
                    'stopped': '✗',
                    'error': '⚠'
                }.get(state, '?')
                logger.debug(f"  {state_emoji} {name}: {state}")
            
            # 等待关闭事件
            logger.info("💤 Application is running, waiting for shutdown signal...")
            await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"❌ Error during application start: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """优雅关闭应用并释放资源。

        符合金融系统资源管理最佳实践，确保数据完整性和一致性。
        """
        logger.info("🛑 Starting graceful shutdown process")

        try:
            # 1. 停止所有模块 ⭐
            if self.module_manager:
                logger.info("Stopping all modules...")
                await asyncio.wait_for(
                    self.module_manager.stop_all_modules(),
                    timeout=30.0
                )
                logger.info("✓ All modules stopped successfully")

        except asyncio.TimeoutError:
            logger.warning("⚠ Timeout during module shutdown, forcing shutdown")
            if self.module_manager:
                running_modules = self.module_manager.get_modules_by_state(
                    ModuleState.RUNNING
                )
                if running_modules:
                    logger.warning(f"Modules still running: {', '.join(running_modules)}")
                    
        except Exception as e:
            logger.error(f"❌ Error during module shutdown: {e}", exc_info=True)
            
        finally:
            # 2. 停止健康监控
            if self.health_monitor:
                try:
                    await asyncio.wait_for(
                        self.health_monitor.stop(),
                        timeout=5.0
                    )
                    logger.debug("✓ Health monitor stopped")
                except Exception as e:
                    logger.error(f"Error stopping health monitor: {e}")

            # 3. 停止指标收集
            if self._metrics_collector:
                try:
                    # 发送最终指标
                    await self._export_final_metrics()
                    
                    await asyncio.wait_for(
                        self._metrics_collector.stop(),
                        timeout=5.0
                    )
                    logger.debug("✓ Metrics collector stopped")
                except Exception as e:
                    logger.error(f"Error stopping metrics collector: {e}")

            logger.info("✅ Graceful shutdown completed")
            
    async def _export_final_metrics(self) -> None:
        """导出最终的模块状态指标"""
        if not self.module_manager or not self._metrics_collector:
            return
        
        try:
            module_status = self.module_manager.get_module_status()
            for name, status in module_status.items():
                state_value = {
                    'stopped': 0.0,
                    'running': 1.0,
                    'error': 2.0
                }.get(status['state'], -1.0)
                
                self._metrics_collector.set_gauge(
                    "module_status",
                    state_value,
                    labels={"module_name": name, "state": status['state']}
                )
            
            logger.debug("Final metrics exported")
                
        except Exception as e:
            logger.error(f"Error exporting final metrics: {e}")

    # ========== 管理接口 ==========

    def get_module_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模块的状态信息"""
        if not self.module_manager:
            return {}
        return self.module_manager.get_module_status()

    async def restart_module(self, module_name: str) -> bool:
        """手动重启指定模块"""
        if not self.module_manager:
            logger.error("Module manager not initialized")
            return False
        
        try:
            return await self.module_manager.restart_module(module_name)
        except Exception as e:
            logger.error(f"Failed to restart module {module_name}: {e}")
            return False

    def list_modules(self) -> List[str]:
        """列出所有已注册的模块"""
        if not self.module_manager:
            return []
        return self.module_manager.list_modules()

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config or {}

async def main():  # sourcery skip: avoid-global-variables
    """应用入口点。"""
    app = FinancialDataCollectorApp()
    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        print("\n⚠ Received interrupt signal")
    except Exception as e:
        print(f"❌ Application error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 确保清理
        await app.stop()
        
    return 0

if __name__ == "__main__":
    asyncio.run(main())