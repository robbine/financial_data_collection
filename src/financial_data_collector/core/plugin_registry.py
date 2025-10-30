from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
import logging

logger = logging.getLogger(__name__)

class FinancialPlugin(ABC):
    @abstractmethod
    def initialize(self, config: Dict) -> None:
        pass
    
    @abstractmethod
    def get_plugin_id(self) -> str:
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        pass

class PluginRegistry:
    _instance: Optional['PluginRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins: Dict[str, FinancialPlugin] = {}
            cls._instance._plugin_classes: Dict[str, Type[FinancialPlugin]] = {}
            cls._instance._initialized = False
        return cls._instance
    
    def initialize(self, config: Dict):
        if self._initialized:
            return
        
        self._enabled = config.get('features', {}).get('plugin_system', False)
        self._initialized = True
        
        if not self._enabled:
            logger.info("Plugin system is disabled via configuration")
            return
        
        # 仅在启用时加载插件定义
        self._load_plugin_definitions(config)
    
    def _load_plugin_definitions(self, config: Dict):
        # 实际插件加载逻辑（当前为空实现）
        pass
    
    def register_plugin_class(self, plugin_id: str, plugin_class: Type[FinancialPlugin]) -> None:
        if not self._enabled:
            return
        self._plugin_classes[plugin_id] = plugin_class
    
    def create_plugin_instance(self, plugin_id: str, config: Dict) -> Optional[FinancialPlugin]:
        if not self._enabled:
            return None
        
        if plugin_id not in self._plugin_classes:
            logger.error(f"Plugin {plugin_id} not registered")
            return None
        
        try:
            plugin = self._plugin_classes[plugin_id]()
            plugin.initialize(config)
            self._plugins[plugin_id] = plugin
            return plugin
        except Exception as e:
            logger.error(f"Failed to create plugin {plugin_id}: {str(e)}")
            return None
    
    def shutdown_all(self) -> None:
        if not self._initialized or not self._enabled:
            return
        
        for plugin in self._plugins.values():
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin: {str(e)}")
        self._plugins.clear()