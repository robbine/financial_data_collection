# 在文件开头添加导入
import importlib
import asyncio
import logging
import inspect
from inspect import isclass
from mimetypes import init
from .di.container import DIContainer
from .events.event_bus import EventBus
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Type, Set
from datetime import datetime
from enum import Enum
from .interfaces import ModuleInterface
from .exceptions import ModuleInitializationError, ModuleStartError, ModuleDependencyError

class ModuleState(Enum):
    """
    Module lifecycle state enumeration.
    
    States:
        UNINITIALIZED: Module is registered but not yet initialized
        INITIALIZED: Module has been initialized but not started
        STARTING: Module is in the process of starting
        RUNNING: Module is running normally
        STOPPING: Module is in the process of stopping
        STOPPED: Module has been stopped
        ERROR: Module encountered an error
    """
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    
    def is_active(self) -> bool:
        """Check if the module is in an active state."""
        return self in (ModuleState.STARTING, ModuleState.RUNNING)
    
    def is_terminal(self) -> bool:
        """Check if the module is in a terminal state."""
        return self in (ModuleState.STOPPED, ModuleState.ERROR)
    
    def can_start(self) -> bool:
        """Check if the module can be started from current state."""
        return self in (
            ModuleState.UNINITIALIZED, 
            ModuleState.INITIALIZED, 
            ModuleState.STOPPED
        )
    
    def can_stop(self) -> bool:
        """Check if the module can be stopped from current state."""
        return self in (ModuleState.STARTING, ModuleState.RUNNING)


@dataclass
class ModuleConfig:
    """
    Configuration for a module.
    
    Attributes:
        name: Unique module identifier
        enabled: Whether the module should be started
        config: Module-specific configuration dictionary
        dependencies: List of module names this module depends on
        startup_order: Priority for startup (lower numbers start first)
        shutdown_order: Priority for shutdown (lower numbers stop first)
        health_check_interval: Seconds between health checks
        max_restart_attempts: Maximum number of automatic restart attempts
        restart_delay: Seconds to wait before attempting restart
    """
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    startup_order: int = 50
    shutdown_order: int = 50
    health_check_interval: int = 30  # seconds
    max_restart_attempts: int = 3
    restart_delay: int = 5  # seconds
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Module name cannot be empty")
        
        if self.health_check_interval < 1:
            raise ValueError("Health check interval must be at least 1 second")
        
        if self.max_restart_attempts < 0:
            raise ValueError("Max restart attempts cannot be negative")
        
        if self.restart_delay < 0:
            raise ValueError("Restart delay cannot be negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'config': self.config,
            'dependencies': self.dependencies,
            'startup_order': self.startup_order,
            'shutdown_order': self.shutdown_order,
            'health_check_interval': self.health_check_interval,
            'max_restart_attempts': self.max_restart_attempts,
            'restart_delay': self.restart_delay
        }


@dataclass
class ModuleInfo:
    """
    Runtime information about a module.
    
    Attributes:
        name: Module name
        module_class: Python class implementing ModuleInterface
        instance: Instantiated module object (None if not created)
        state: Current lifecycle state
        config: Module configuration
        start_time: When the module was last started
        stop_time: When the module was last stopped
        restart_count: Number of times module has been restarted
        last_health_check: Timestamp of last health check
        health_status: Current health status string
        error_message: Last error message if in ERROR state
    """
    name: str
    module_class: Type
    instance: Optional[Any] = None
    state: ModuleState = ModuleState.UNINITIALIZED
    config: Optional[ModuleConfig] = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate module info after initialization."""
        if not self.name:
            raise ValueError("Module name cannot be empty")
        
        if not self.module_class:
            raise ValueError("Module class cannot be None")
    
    @property
    def is_healthy(self) -> bool:
        """Check if module is in a healthy state."""
        return (
            self.state == ModuleState.RUNNING and 
            self.health_status in ("healthy", "unknown")
        )
    
    @property
    def uptime_seconds(self) -> Optional[float]:
        """Calculate module uptime in seconds."""
        if self.start_time and self.state == ModuleState.RUNNING:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    @property
    def can_restart(self) -> bool:
        """Check if module can be restarted."""
        return (
            self.restart_count < self.config.max_restart_attempts
            if self.config else False
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert module info to dictionary for serialization."""
        return {
            'name': self.name,
            'module_class': f"{self.module_class.__module__}.{self.module_class.__name__}",
            'state': self.state.value,
            'enabled': self.config.enabled if self.config else False,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'stop_time': self.stop_time.isoformat() if self.stop_time else None,
            'uptime_seconds': self.uptime_seconds,
            'restart_count': self.restart_count,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'health_status': self.health_status,
            'is_healthy': self.is_healthy,
            'error_message': self.error_message,
            'dependencies': self.config.dependencies if self.config else [],
            'can_restart': self.can_restart
        }
    
    def clear_error(self):
        """Clear error state and message."""
        self.error_message = None
        if self.state == ModuleState.ERROR:
            self.state = ModuleState.STOPPED
    
    def record_start(self):
        """Record module start time."""
        self.start_time = datetime.now()
        self.stop_time = None
        self.error_message = None
    
    def record_stop(self):
        """Record module stop time."""
        self.stop_time = datetime.now()
    
    def record_error(self, error_message: str):
        """Record an error."""
        self.error_message = error_message
        self.state = ModuleState.ERROR
        self.stop_time = datetime.now()
    
    def record_health_check(self, status: str):
        """Record a health check result."""
        self.last_health_check = datetime.now()
        self.health_status = status


@dataclass
class ModuleStats:
    """
    Statistics about a module.
    
    Used for monitoring and reporting purposes.
    """
    name: str
    state: str
    enabled: bool
    uptime_seconds: Optional[float] = None
    restart_count: int = 0
    health_status: str = "unknown"
    last_health_check: Optional[str] = None
    error_count: int = 0
    success_rate: float = 1.0
    dependencies_satisfied: bool = True
    
    @classmethod
    def from_module_info(cls, info: ModuleInfo) -> "ModuleStats":
        """Create stats from ModuleInfo."""
        return cls(
            name=info.name,
            state=info.state.value,
            enabled=info.config.enabled if info.config else False,
            uptime_seconds=info.uptime_seconds,
            restart_count=info.restart_count,
            health_status=info.health_status,
            last_health_check=info.last_health_check.isoformat() if info.last_health_check else None
        )
        
        
class ModuleManager:
    """Manager for module lifecycle and operations."""
    
    def __init__(self, di_container, event_bus: EventBus):
        self.logger = logging.getLogger(__name__)
        self.di_container = di_container
        self.event_bus = event_bus
        self._modules: Dict[str, ModuleInfo] = {}
        self._module_dependencies: Dict[str, Set[str]] = {}
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._initialized = False  # ⭐ 添加初始化标志
    
    def list_modules(self) -> List[str]:
        """返回所有已注册模块的名称列表"""
        return list(self._modules.keys())
    
    def get_module(self, module_name: str) -> Optional[ModuleInfo]:
        """通过模块名称获取模块信息
        
        Args:
            module_name: 要获取的模块名称
        
        Returns:
            模块信息对象，若模块不存在则返回None
        """
        return self._modules.get(module_name)
        
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化模块管理器
        
        Args:
            config: 包含模块管理器配置的字典，格式示例:
            {
                "modules": [
                    {
                        "name": "module_name",
                        "class_path": "package.module.ClassName",
                        "enabled": true,
                        "config": {},
                        "dependencies": [],
                        "startup_order": 100,
                        "shutdown_order": 100,
                        "health_check_interval": 30
                    }
                ]
            }
        """
        async with self._lock:
            if self._initialized:
                self.logger.warning("ModuleManager has already been initialized")
                return

            try:
                # 1. 验证配置有效性
                if not isinstance(config, dict) or "modules" not in config:
                    raise ValueError("Invalid ModuleManager configuration - missing 'modules' section")

                # 2. 注册配置中定义的模块
                failed_modules = []
                for module_config in config["modules"]:
                    try:
                        self._register_module_from_config(module_config)
                    except Exception as e:
                        failed_modules.append({
                            'name': module_config.get('name', 'unknown'),
                            'error': str(e)
                        })
                        self.logger.error(f"Failed to register module {module_config.get('name')}: {e}")

                # 如果有模块注册失败，记录但继续
                if failed_modules:
                    self.logger.warning(f"Failed to register {len(failed_modules)} modules: {failed_modules}")

                # 3. 验证依赖关系
                self._validate_dependency_graph()

                # 4. 完成初始化
                self._initialized = True
                self.logger.info(f"ModuleManager initialized successfully with {len(self._modules)} modules")

            except Exception as e:
                self.logger.error(f"Failed to initialize ModuleManager: {e}")
                # 清理部分注册的模块
                self._modules.clear()
                self._module_dependencies.clear()
                raise

    def _register_module_from_config(self, module_config: Dict[str, Any]) -> None:
        """从配置字典注册模块（内部方法，调用者需持有锁）"""
        # 1. 解析基本配置
        name = module_config.get("name")
        class_path = module_config.get("class_path")
        enabled = module_config.get("enabled", True)

        if not name:
            raise ValueError("Module configuration missing 'name' field")
        if not class_path:
            raise ValueError(f"Module '{name}' configuration missing 'class_path' field")

        # 2. 动态导入模块类
        try:
            module_class = self._import_class(class_path)
            
            # 验证是否为类
            if not isclass(module_class):
                raise TypeError(f"{class_path} is not a class")
            
            # 验证是否实现 ModuleInterface
            if not issubclass(module_class, ModuleInterface):
                raise TypeError(f"Class {class_path} does not implement ModuleInterface")
                
        except ImportError as e:
            raise ImportError(f"Failed to import module class {class_path}: {e}")
        except AttributeError as e:
            raise AttributeError(f"Class not found in module {class_path}: {e}")

        # 3. 创建模块配置对象
        config = ModuleConfig(
            name=name,
            enabled=enabled,
            config=module_config.get("config", {}),
            dependencies=module_config.get("dependencies", []),
            startup_order=module_config.get("startup_order", 50),
            shutdown_order=module_config.get("shutdown_order", 50),
            health_check_interval=module_config.get("health_check_interval", 30),
            max_restart_attempts=module_config.get("max_restart_attempts", 3),
            restart_delay=module_config.get("restart_delay", 5)
        )

        # 4. 注册模块（不需要再加锁，因为调用者已持有锁）
        # 直接操作内部状态，避免 register_module 中的锁冲突
        if name in self._modules:
            self.logger.warning(f"Module {name} is already registered, replacing...")
        
        self._modules[name] = ModuleInfo(
            name=name,
            module_class=module_class,
            config=config
        )
        
        self._module_dependencies[name] = set(config.dependencies)
        self.logger.info(f"Module {name} registered with dependencies: {config.dependencies}")

    @staticmethod
    def _import_class(class_path: str) -> Type:
        """
        从类路径导入类
        
        Args:
            class_path: 完整的类路径，如 "package.module.ClassName"
            
        Returns:
            导入的类对象
            
        Raises:
            ImportError: 模块导入失败
            AttributeError: 类不存在
            ValueError: 路径格式错误
        """
        if "." not in class_path:
            raise ValueError(f"Invalid class path '{class_path}': must contain module and class name")
        
        module_path, class_name = class_path.rsplit(".", 1)
        
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except ImportError as e:
            raise ImportError(f"Cannot import module '{module_path}': {e}")
        except AttributeError as e:
            raise AttributeError(f"Class '{class_name}' not found in module '{module_path}': {e}")

    def _validate_dependency_graph(self) -> None:
        """
        验证依赖关系图中是否存在循环依赖和缺失依赖
        
        Raises:
            ValueError: 检测到循环依赖或缺失依赖
        """
        visited = set()
        temp_visited = set()
        missing_deps = []

        def visit(module_name: str, path: List[str] = None):
            if path is None:
                path = []
            
            if module_name in temp_visited:
                cycle = " -> ".join(path + [module_name])
                raise ValueError(f"Circular dependency detected: {cycle}")
            
            if module_name in visited:
                return

            temp_visited.add(module_name)
            path.append(module_name)
            
            for dep in self._module_dependencies.get(module_name, set()):
                if dep not in self._modules:
                    missing_deps.append((module_name, dep))
                else:
                    visit(dep, path.copy())
            
            temp_visited.remove(module_name)
            visited.add(module_name)

        # 检查所有模块
        for module_name in self._modules.keys():
            if module_name not in visited:
                visit(module_name)
        
        # 报告缺失的依赖
        if missing_deps:
            error_msg = "Missing dependencies found:\n"
            for module, dep in missing_deps:
                error_msg += f"  - Module '{module}' depends on missing module '{dep}'\n"
            raise ValueError(error_msg.strip())
        
        self.logger.info("Dependency graph validation passed")
        

    async def start_all_modules(self) -> None:
        """
        启动所有已注册且启用的模块，遵循启动顺序和依赖关系
        
        Raises:
            RuntimeError: 当模块管理器未初始化或已在运行时
            ModuleStartError: 当关键模块启动失败时
        """
        async with self._lock:
            if not self._initialized:
                raise RuntimeError("ModuleManager has not been initialized")
            if self._running:
                self.logger.warning("Modules are already running")
                return

            self.logger.info("Starting all enabled modules...")
            self._running = True
            failed_critical_modules = []
            startup_tasks = []

            try:
                # 1. 按启动顺序排序模块
                sorted_modules = sorted(
                    [m for m in self._modules.values() if m.config.enabled],
                    key=lambda x: x.config.startup_order
                )

                if not sorted_modules:
                    self.logger.warning("No enabled modules found to start")
                    return

                # 2. 为每个模块创建启动任务
                for module_info in sorted_modules:
                    task = asyncio.create_task(
                        self._start_module(module_info),
                        name=f"start_module_{module_info.name}"
                    )
                    startup_tasks.append(task)

                # 3. 等待所有启动任务完成
                results = await asyncio.gather(*startup_tasks, return_exceptions=True)

                # 4. 处理启动结果
                for i, result in enumerate(results):
                    module_info = sorted_modules[i]
                    if isinstance(result, Exception):
                        self.logger.error(
                            f"Module {module_info.name} failed to start: {str(result)}",
                            exc_info=result
                        )
                        module_info.record_error(str(result))
                        if self._is_critical_module(module_info):
                            failed_critical_modules.append(module_info.name)

                # 5. 如果有关键模块启动失败，抛出异常
                if failed_critical_modules:
                    raise ModuleStartError(
                        f"Critical modules failed to start: {', '.join(failed_critical_modules)}"
                    )

                self.logger.info("All enabled modules have been processed")

            except Exception as e:
                self.logger.error(f"Failed to start modules: {str(e)}", exc_info=e)
                self._running = False
                raise

    async def _start_module(self, module_info: ModuleInfo) -> None:
        """
        启动单个模块的内部辅助方法
        
        Args:
            module_info: 要启动的模块信息对象
        
        Raises:
            ModuleDependencyError: 依赖模块未运行
            ModuleStartError: 模块启动失败
        """
        if not module_info.config.enabled:
            self.logger.debug(f"Skipping disabled module: {module_info.name}")
            return

        if module_info.state.is_active():
            self.logger.warning(f"Module {module_info.name} is already active")
            return

        if not module_info.state.can_start():
            raise ModuleStartError(
                f"Cannot start module {module_info.name} from state {module_info.state.value}"
            )

        # 检查依赖项
        await self._check_module_dependencies(module_info)

        self.logger.info(f"Starting module {module_info.name}...")
        module_info.state = ModuleState.STARTING

        try:
            # 创建模块实例
            instance = await self._create_module_instance(module_info)
            module_info.instance = instance
            
            if not instance._initialized:
                self.logger.info(f"Initializing module {module_info.name}")
                init_method = getattr(instance, 'initialize', None)
                if callable(init_method):
                    sig = inspect.signature(init_method)
                    if 'config' in sig.parameters:
                        await init_method(module_info.config.config)
                    else:
                        await init_method()
                else:
                    self.logger.warning(f"Module {module_info.name} has no initialize method")
                instance._initialized = True

            # 调用模块的start方法
            if hasattr(instance, 'start'):
                if asyncio.iscoroutinefunction(instance.start):
                    await instance.start()
                else:
                    # 对于同步start方法，在线程池中运行
                    await asyncio.to_thread(instance.start)
            else:
                self.logger.warning(f"Module {module_info.name} has no start method")

            # 更新模块状态
            module_info.state = ModuleState.RUNNING
            module_info.record_start()
            self.logger.info(f"Successfully started module {module_info.name}")

            # 启动健康检查任务
            await self._start_health_check_task(module_info)

        except Exception as e:
            self.logger.error(f"Module {module_info.name} failed to start: {str(e)}", exc_info=e)
            module_info.record_error(str(e))
            raise ModuleStartError(f"Module {module_info.name} start failed: {str(e)}") from e

    async def restart_module(self, module_name: str) -> None:
        """重启指定模块：先停再启"""
        module_info = self.get_module(module_name)
        if not module_info:
            self.logger.warning(f"Restart requested for unknown module: {module_name}")
            return

        # 停止模块
        try:
            if module_info.instance and module_info.state in (ModuleState.STARTING, ModuleState.RUNNING):
                self.logger.info(f"Stopping module {module_name} for restart...")
                module_info.state = ModuleState.STOPPING

                if hasattr(module_info.instance, 'stop'):
                    if asyncio.iscoroutinefunction(module_info.instance.stop):
                        await module_info.instance.stop()
                    else:
                        await asyncio.to_thread(module_info.instance.stop)

                module_info.record_stop()
                module_info.state = ModuleState.STOPPED

                # 取消旧的健康检查任务
                task = self._health_check_tasks.get(module_name)
                if task and not task.done():
                    task.cancel()
                self._health_check_tasks.pop(module_name, None)
            else:
                self.logger.debug(f"Module {module_name} is not running; skipping stop step")
        except Exception as e:
            self.logger.error(f"Failed to stop module {module_name} during restart: {e}", exc_info=e)
            # 继续尝试启动

        # 重新启动模块
        try:
            await self._start_module(module_info)
            self.logger.info(f"Module {module_name} restarted successfully")
        except Exception as e:
            self.logger.error(f"Failed to restart module {module_name}: {e}", exc_info=e)
            raise

    async def _check_module_dependencies(self, module_info: ModuleInfo) -> None:
        """
        检查模块的所有依赖项是否都在运行中
        
        Args:
            module_info: 要检查的模块信息
        
        Raises:
            ModuleDependencyError: 当任何依赖项未运行时
        """
        missing_deps = []
        for dep_name in module_info.config.dependencies:
            dep_info = self.get_module(dep_name)
            if not dep_info:
                missing_deps.append(f"{dep_name} (not found)")
                continue
            if dep_info.state != ModuleState.RUNNING:
                missing_deps.append(f"{dep_name} (state: {dep_info.state.value})")

        if missing_deps:
            raise ModuleDependencyError(
                f"Module {module_info.name} has unmet dependencies: {', '.join(missing_deps)}"
            )

    async def _create_module_instance(self, module_info: ModuleInfo) -> Any:
        """
        创建模块实例并注入依赖
        
        Args:
            module_info: 模块信息对象
        
        Returns:
            创建的模块实例
        
        Raises:
            ModuleInitializationError: 实例创建失败时
        """
        try:
            # 获取构造函数参数
            constructor_params = await self._resolve_constructor_dependencies(
                module_info.module_class
            )

            # 添加模块配置参数
            if hasattr(module_info.module_class, '__init__'):
                sig = inspect.signature(module_info.module_class.__init__)
                if 'config' in sig.parameters:
                    constructor_params['config'] = module_info.config.config
                if 'event_bus' in sig.parameters:
                    constructor_params['event_bus'] = self.event_bus

            # 创建实例
            instance = module_info.module_class(**constructor_params)
            return instance

        except Exception as e:
            raise ModuleInitializationError(
                f"Failed to create instance for {module_info.name}: {str(e)}"
            ) from e

    async def _resolve_constructor_dependencies(self, module_class: Type) -> Dict[str, Any]:
        """
        解析模块构造函数的依赖项
        
        Args:
            module_class: 模块类
        
        Returns:
            包含解析后的依赖项的字典
        """
        params = {}
        if not hasattr(module_class, '__init__'):
            return params

        sig = inspect.signature(module_class.__init__)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 尝试从DI容器解析依赖
            if hasattr(self.di_container, 'has_dependency') and self.di_container.has_dependency(param_name):
                params[param_name] = await self.di_container.get_dependency(param_name)
            elif param.default != inspect.Parameter.empty:
                params[param_name] = param.default

        return params

    async def _start_health_check_task(self, module_info: ModuleInfo) -> None:
        """
        为模块启动健康检查任务
        
        Args:
            module_info: 模块信息对象
        """
        # 停止现有健康检查任务（如果存在）
        if module_info.name in self._health_check_tasks:
            task = self._health_check_tasks[module_info.name]
            if not task.done():
                task.cancel()
            del self._health_check_tasks[module_info.name]

        # 创建新的健康检查任务
        async def health_check_loop():
            while True:
                try:
                    await self._perform_health_check(module_info)
                except Exception as e:
                    self.logger.error(
                        f"Health check failed for {module_info.name}: {str(e)}",
                        exc_info=e
                    )
                try:
                    await asyncio.sleep(module_info.config.health_check_interval)
                except asyncio.CancelledError:
                    return 

        task = asyncio.create_task(
            health_check_loop(),
            name=f"health_check_{module_info.name}"
        )
        self._health_check_tasks[module_info.name] = task

        # 添加任务完成回调
        def task_done_callback(task: asyncio.Task):
            try:
                # 被取消的任务不应再调用 exception()
                if task.cancelled():
                    return
                exc = task.exception()
                if exc:
                    self.logger.error(
                        f"Health check task for {module_info.name} failed: {exc}"
                    )
            except asyncio.CancelledError:
                # 在回调读取异常时如果抛出取消，直接忽略
                return
            except Exception as e:
                self.logger.error(
                    f"Error in health check task callback for {module_info.name}: {str(e)}"
                )

        task.add_done_callback(task_done_callback)

    async def _perform_health_check(self, module_info: ModuleInfo) -> None:
        """
        执行模块健康检查
        
        Args:
            module_info: 模块信息对象
        """
        if not module_info.instance or not module_info.state.is_active():
            return

        try:
            # 检查模块是否有health_check方法
            if hasattr(module_info.instance, 'health_check'):
                if asyncio.iscoroutinefunction(module_info.instance.health_check):
                    status = await module_info.instance.health_check()
                else:
                    status = await asyncio.to_thread(module_info.instance.health_check)
            else:
                # 如果没有健康检查方法，默认视为健康
                status = 'healthy'

            raw_status = status
            normalized_status = status.get('status', 'unknown') if isinstance(status, dict) else status
            module_info.record_health_check(normalized_status)
            self.logger.debug(f"Health check for {module_info.name}: {raw_status}")

            # 如果模块不健康且可以重启，尝试重启
            if normalized_status != 'healthy' and module_info.can_restart:
                self.logger.warning(
                    f"Module {module_info.name} is unhealthy ({raw_status}), attempting restart..."
                )
                await self.restart_module(module_info.name)

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            module_info.record_health_check('error')
            module_info.record_error(error_msg)
            raise

    def _is_critical_module(self, module_info: ModuleInfo) -> bool:
        """
        判断模块是否为关键模块
        
        关键模块是指那些启动失败会导致整个应用无法正常工作的模块
        
        Args:
            module_info: 模块信息对象
        
        Returns:
            如果是关键模块则返回True，否则返回False
        """
        # 可以根据模块名称、标签或配置来判断
        critical_module_names = {'config_manager', 'clickhouse_storage', 'task_scheduler'}
        return module_info.name in critical_module_names
