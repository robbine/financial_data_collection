"""
Plugin registry for managing and discovering plugins.
"""

from typing import Dict, List, Optional, Type, Any, Callable
import importlib
import pkgutil
import os
import logging
from pathlib import Path
from .base import Plugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing plugin discovery, loading, and lifecycle."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[Plugin]] = {}
        self._plugin_instances: Dict[str, Plugin] = {}
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self._plugin_dependencies: Dict[str, List[str]] = {}
        self._discovery_paths: List[str] = []
    
    def register_plugin(self, name: str, plugin_class: Type[Plugin], metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a plugin class.
        
        Args:
            name: Plugin name
            plugin_class: Plugin class
            metadata: Optional plugin metadata
        """
        if name in self._plugins:
            logger.warning(f"Plugin {name} is already registered, replacing...")
        
        self._plugins[name] = plugin_class
        self._plugin_metadata[name] = metadata or {}
        logger.info(f"Plugin {name} registered")
    
    def unregister_plugin(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self._plugins:
            # Cleanup instance if exists
            if name in self._plugin_instances:
                self._plugin_instances[name].cleanup()
                del self._plugin_instances[name]
            
            del self._plugins[name]
            del self._plugin_metadata[name]
            logger.info(f"Plugin {name} unregistered")
    
    def get_plugin_class(self, name: str) -> Optional[Type[Plugin]]:
        """Get plugin class by name."""
        return self._plugins.get(name)
    
    def create_plugin_instance(self, name: str, *args, **kwargs) -> Optional[Plugin]:
        """
        Create a plugin instance.
        
        Args:
            name: Plugin name
            *args: Plugin constructor arguments
            **kwargs: Plugin constructor keyword arguments
            
        Returns:
            Plugin instance or None if not found
        """
        plugin_class = self.get_plugin_class(name)
        if plugin_class:
            instance = plugin_class(*args, **kwargs)
            self._plugin_instances[name] = instance
            return instance
        return None
    
    def get_plugin_instance(self, name: str) -> Optional[Plugin]:
        """Get existing plugin instance."""
        return self._plugin_instances.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())
    
    def get_plugin_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get plugin metadata."""
        return self._plugin_metadata.get(name)
    
    def set_plugin_dependencies(self, name: str, dependencies: List[str]) -> None:
        """Set plugin dependencies."""
        self._plugin_dependencies[name] = dependencies
    
    def get_plugin_dependencies(self, name: str) -> List[str]:
        """Get plugin dependencies."""
        return self._plugin_dependencies.get(name, [])
    
    def add_discovery_path(self, path: str) -> None:
        """Add a path for plugin discovery."""
        if path not in self._discovery_paths:
            self._discovery_paths.append(path)
            logger.info(f"Added discovery path: {path}")
    
    def discover_plugins(self, package_name: str = None) -> List[str]:
        """
        Discover plugins in the specified package.
        
        Args:
            package_name: Package name to search in
            
        Returns:
            List of discovered plugin names
        """
        discovered = []
        
        if package_name:
            try:
                package = importlib.import_module(package_name)
                discovered.extend(self._discover_in_package(package))
            except ImportError as e:
                logger.error(f"Could not import package {package_name}: {e}")
        else:
            # Discover in all registered paths
            for path in self._discovery_paths:
                discovered.extend(self._discover_in_path(path))
        
        return discovered
    
    def _discover_in_package(self, package) -> List[str]:
        """Discover plugins in a package."""
        discovered = []
        
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            try:
                module = importlib.import_module(modname)
                discovered.extend(self._discover_in_module(module))
            except ImportError as e:
                logger.warning(f"Could not import module {modname}: {e}")
        
        return discovered
    
    def _discover_in_path(self, path: str) -> List[str]:
        """Discover plugins in a file path."""
        discovered = []
        path_obj = Path(path)
        
        if not path_obj.exists():
            logger.warning(f"Discovery path does not exist: {path}")
            return discovered
        
        for py_file in path_obj.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                # Convert file path to module name
                relative_path = py_file.relative_to(path_obj)
                module_name = str(relative_path).replace("/", ".").replace("\\", ".").replace(".py", "")
                
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    discovered.extend(self._discover_in_module(module))
            except Exception as e:
                logger.warning(f"Could not process file {py_file}: {e}")
        
        return discovered
    
    def _discover_in_module(self, module) -> List[str]:
        """Discover plugins in a module."""
        discovered = []
        
        for name, obj in vars(module).items():
            if (isinstance(obj, type) and 
                issubclass(obj, Plugin) and 
                obj != Plugin):
                
                plugin_name = getattr(obj, 'name', name)
                self.register_plugin(plugin_name, obj)
                discovered.append(plugin_name)
                logger.info(f"Discovered plugin: {plugin_name} in {module.__name__}")
        
        return discovered
    
    def load_plugin_from_file(self, file_path: str, plugin_name: str = None) -> Optional[str]:
        """
        Load a plugin from a file.
        
        Args:
            file_path: Path to the plugin file
            plugin_name: Optional plugin name override
            
        Returns:
            Plugin name if successful, None otherwise
        """
        try:
            spec = importlib.util.spec_from_file_location("plugin", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin class in module
                for name, obj in vars(module).items():
                    if (isinstance(obj, type) and 
                        issubclass(obj, Plugin) and 
                        obj != Plugin):
                        
                        plugin_name = plugin_name or getattr(obj, 'name', name)
                        self.register_plugin(plugin_name, obj)
                        return plugin_name
        except Exception as e:
            logger.error(f"Could not load plugin from {file_path}: {e}")
        
        return None
    
    def get_plugins_by_type(self, plugin_type: Type[Plugin]) -> List[str]:
        """Get plugins of a specific type."""
        return [
            name for name, plugin_class in self._plugins.items()
            if issubclass(plugin_class, plugin_type)
        ]
    
    def validate_plugin_dependencies(self, plugin_name: str) -> bool:
        """Validate that all plugin dependencies are available."""
        dependencies = self.get_plugin_dependencies(plugin_name)
        for dep in dependencies:
            if dep not in self._plugins:
                logger.error(f"Plugin {plugin_name} dependency {dep} not found")
                return False
        return True
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive plugin information."""
        if plugin_name not in self._plugins:
            return None
        
        info = {
            "name": plugin_name,
            "class": self._plugins[plugin_name].__name__,
            "metadata": self._plugin_metadata.get(plugin_name, {}),
            "dependencies": self.get_plugin_dependencies(plugin_name),
            "has_instance": plugin_name in self._plugin_instances
        }
        
        if plugin_name in self._plugin_instances:
            instance = self._plugin_instances[plugin_name]
            info["instance_info"] = instance.get_info()
        
        return info
    
    def cleanup(self) -> None:
        """Cleanup all plugin instances."""
        for instance in self._plugin_instances.values():
            instance.cleanup()
        self._plugin_instances.clear()
        logger.info("All plugin instances cleaned up")
