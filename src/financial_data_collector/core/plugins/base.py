"""
Base plugin classes and interfaces.
"""

from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Abstract base class for all plugins."""
    
    def __init__(self, name: Optional[str] = None, version: str = "1.0.0"):
        self.name = name or self.__class__.__name__
        self.version = version
        self.enabled = True
        self.initialized = False
        self.config: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        pass
    
    @abstractmethod
    def execute(self, data: Any) -> Any:
        """
        Execute the plugin on the given data.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        pass
    
    def enable(self) -> None:
        """Enable the plugin."""
        self.enabled = True
        logger.info(f"Plugin {self.name} enabled")
    
    def disable(self) -> None:
        """Disable the plugin."""
        self.enabled = False
        logger.info(f"Plugin {self.name} disabled")
    
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self.enabled and self.initialized
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "initialized": self.initialized,
            "metadata": self.metadata
        }
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update plugin metadata."""
        self.metadata[key] = value
        self.metadata["last_used"] = datetime.now().isoformat()
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        self.initialized = False
        logger.info(f"Plugin {self.name} cleaned up")


class DataProcessorPlugin(Plugin):
    """Base class for data processing plugins."""
    
    def __init__(self, name: Optional[str] = None, version: str = "1.0.0"):
        super().__init__(name, version)
        self.input_types: List[type] = []
        self.output_types: List[type] = []
    
    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """
        Process the input data.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        pass
    
    def execute(self, data: Any) -> Any:
        """Execute the data processing plugin."""
        if not self.is_enabled():
            raise RuntimeError(f"Plugin {self.name} is not enabled or initialized")
        
        # Validate input type
        if self.input_types and not isinstance(data, tuple(self.input_types)):
            raise TypeError(f"Plugin {self.name} expects data of type {self.input_types}, got {type(data)}")
        
        try:
            result = self.process_data(data)
            self.update_metadata("execution_count", self.metadata.get("execution_count", 0) + 1)
            return result
        except Exception as e:
            logger.error(f"Error in plugin {self.name}: {e}")
            raise


class DataCollectorPlugin(Plugin):
    """Base class for data collection plugins."""
    
    def __init__(self, name: Optional[str] = None, version: str = "1.0.0"):
        super().__init__(name, version)
        self.supported_sources: List[str] = []
        self.collection_methods: List[str] = []
    
    @abstractmethod
    def collect_data(self, source: str, config: Dict[str, Any]) -> Any:
        """
        Collect data from the specified source.
        
        Args:
            source: Data source identifier
            config: Collection configuration
            
        Returns:
            Collected data
        """
        pass
    
    def execute(self, data: Any) -> Any:
        """Execute the data collection plugin."""
        if not self.is_enabled():
            raise RuntimeError(f"Plugin {self.name} is not enabled or initialized")
        
        if isinstance(data, dict) and "source" in data and "config" in data:
            return self.collect_data(data["source"], data["config"])
        else:
            raise ValueError(f"Plugin {self.name} expects data with 'source' and 'config' keys")


class DataTransformerPlugin(Plugin):
    """Base class for data transformation plugins."""
    
    def __init__(self, name: Optional[str] = None, version: str = "1.0.0"):
        super().__init__(name, version)
        self.transformation_type: str = "generic"
        self.parameters: Dict[str, Any] = {}
    
    @abstractmethod
    def transform_data(self, data: Any) -> Any:
        """
        Transform the input data.
        
        Args:
            data: Input data to transform
            
        Returns:
            Transformed data
        """
        pass
    
    def execute(self, data: Any) -> Any:
        """Execute the data transformation plugin."""
        if not self.is_enabled():
            raise RuntimeError(f"Plugin {self.name} is not enabled or initialized")
        
        try:
            result = self.transform_data(data)
            self.update_metadata("transformation_count", self.metadata.get("transformation_count", 0) + 1)
            return result
        except Exception as e:
            logger.error(f"Error in plugin {self.name}: {e}")
            raise


class PluginManager:
    """Manager for plugin lifecycle and operations."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_dependencies: Dict[str, List[str]] = {}
    
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin."""
        if plugin.name in self._plugins:
            logger.warning(f"Plugin {plugin.name} is already registered, replacing...")
        
        self._plugins[plugin.name] = plugin
        logger.info(f"Plugin {plugin.name} registered")
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin."""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            plugin.cleanup()
            del self._plugins[plugin_name]
            logger.info(f"Plugin {plugin_name} unregistered")
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())
    
    def get_plugins_by_type(self, plugin_type: type) -> List[Plugin]:
        """Get plugins of a specific type."""
        return [plugin for plugin in self._plugins.values() if isinstance(plugin, plugin_type)]
    
    def initialize_plugin(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Initialize a plugin with configuration."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.initialize(config)
            plugin.initialized = True
            logger.info(f"Plugin {plugin_name} initialized")
        else:
            raise ValueError(f"Plugin {plugin_name} not found")
    
    def execute_plugin(self, plugin_name: str, data: Any) -> Any:
        """Execute a plugin with data."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.execute(data)
        else:
            raise ValueError(f"Plugin {plugin_name} not found")
    
    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a plugin."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.enable()
        else:
            raise ValueError(f"Plugin {plugin_name} not found")
    
    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a plugin."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.disable()
        else:
            raise ValueError(f"Plugin {plugin_name} not found")
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information."""
        plugin = self.get_plugin(plugin_name)
        return plugin.get_info() if plugin else None
    
    def cleanup_all(self) -> None:
        """Cleanup all plugins."""
        for plugin in self._plugins.values():
            plugin.cleanup()
        self._plugins.clear()
        logger.info("All plugins cleaned up")
