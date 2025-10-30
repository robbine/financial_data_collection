"""
Dependency Injection Container.

Provides a simple but powerful dependency injection container for managing
service dependencies and lifecycle.
"""

from typing import Dict, Type, Any, Callable, Optional, Union, TypeVar
import inspect
import threading
from abc import ABC, abstractmethod

T = TypeVar('T')


from dependency_injector import containers, providers
from ..events.event_bus import EventBus
from ..storage.storage_adapter import PrimaryFallbackAdapter
from ..handlers.kline_data_handler import KlineDataPersistenceHandler
from ..crawler.web_crawler import WebCrawler
from ..plugin_registry import PluginRegistry

class CoreContainer(containers.DeclarativeContainer):
    event_bus = providers.Singleton(EventBus)
    storage_adapter = providers.Singleton(PrimaryFallbackAdapter)

    # 事件处理器注册
    kline_handler = providers.Singleton(
        KlineDataPersistenceHandler,
        storage_adapter=storage_adapter
    )

    # 爬虫实例化
    web_crawler = providers.Factory(
        WebCrawler,
        event_bus=event_bus
    )

    def wire(self):
        # 注册事件订阅关系
        self.event_bus().subscribe(
            KlineDataCollectedEvent,
            self.kline_handler().handle
        )

class ServiceProvider(ABC):
    """Abstract base class for service providers."""
    
    @abstractmethod
    def get_instance(self) -> Any:
        """Get service instance."""
        pass


class SingletonProvider(ServiceProvider):
    """Provider for singleton services."""
    
    def __init__(self, service_class: Type, *args, **kwargs):
        self._service_class = service_class
        self._args = args
        self._kwargs = kwargs
        self._instance: Optional[Any] = None
        self._lock = threading.Lock()
    
    def get_instance(self) -> Any:
        """Get singleton instance."""
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = self._service_class(*self._args, **self._kwargs)
        return self._instance


class FactoryProvider(ServiceProvider):
    """Provider for factory-based services."""
    
    def __init__(self, factory: Callable):
        self._factory = factory
    
    def get_instance(self) -> Any:
        """Get instance from factory."""
        return self._factory()


class DIContainer:
    """
    Dependency Injection Container.
    
    Manages service registration and resolution with support for:
    - Singleton services
    - Factory services
    - Interface-based registration
    - Dependency resolution
    """
    
    def __init__(self, config):
        if config.get('features', {}).get('plugin_registry_wedge', False):
            self.plugin_registry = providers.Singleton(PluginRegistry)
        else:
            self.plugin_registry = providers.Object(None)
        self._services: Dict[Type, ServiceProvider] = {}
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.Lock()
    
    def register_singleton(self, interface: Type[T], implementation: Type[T], *args, **kwargs) -> 'DIContainer':
        """
        Register a singleton service.
        
        Args:
            interface: The interface/type to register
            implementation: The implementation class
            *args: Constructor arguments
            **kwargs: Constructor keyword arguments
            
        Returns:
            Self for method chaining
        """
        provider = SingletonProvider(implementation, *args, **kwargs)
        self._services[interface] = provider
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """
        Register a factory service.
        
        Args:
            interface: The interface/type to register
            factory: Factory function that creates the service
            
        Returns:
            Self for method chaining
        """
        provider = FactoryProvider(factory)
        self._services[interface] = provider
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """
        Register a pre-created instance.
        
        Args:
            interface: The interface/type to register
            instance: The pre-created instance
            
        Returns:
            Self for method chaining
        """
        self._instances[interface] = instance
        return self
    
    def get(self, interface: Type[T]) -> T:
        """
        Get a service instance.
        
        Args:
            interface: The interface/type to resolve
            
        Returns:
            The service instance
            
        Raises:
            ValueError: If service is not registered
        """
        # Check for pre-registered instances
        if interface in self._instances:
            return self._instances[interface]
        
        # Check for registered services
        if interface in self._services:
            with self._lock:
                if interface not in self._instances:
                    self._instances[interface] = self._services[interface].get_instance()
                return self._instances[interface]
        
        # Try to auto-resolve if it's a concrete class
        if inspect.isclass(interface) and not inspect.isabstract(interface):
            try:
                return self._auto_resolve(interface)
            except Exception as e:
                raise ValueError(f"Cannot auto-resolve {interface}: {e}")
        
        raise ValueError(f"Service {interface} not registered")
    
    def _auto_resolve(self, service_class: Type[T]) -> T:
        """
        Auto-resolve dependencies for a service class.
        
        Args:
            service_class: The service class to resolve
            
        Returns:
            The resolved service instance
        """
        signature = inspect.signature(service_class.__init__)
        kwargs = {}
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                raise ValueError(f"Parameter {param_name} has no type annotation")
            
            try:
                kwargs[param_name] = self.get(param_type)
            except ValueError:
                if param.default != inspect.Parameter.empty:
                    continue
                raise ValueError(f"Cannot resolve dependency {param_type} for {service_class}")
        
        return service_class(**kwargs)
    
    def is_registered(self, interface: Type) -> bool:
        """
        Check if a service is registered.
        
        Args:
            interface: The interface/type to check
            
        Returns:
            True if registered, False otherwise
        """
        return interface in self._services or interface in self._instances
    
    def clear(self):
        """Clear all registered services and instances."""
        with self._lock:
            self._services.clear()
            self._instances.clear()
    
    def get_all_registered(self) -> Dict[Type, Any]:
        """
        Get all registered service types.
        
        Returns:
            Dictionary of registered service types
        """
        return {**self._services, **self._instances}
    
    def has_dependency(self, name: str) -> bool:
        """
        Check if a dependency is registered by name.
        
        Args:
            name: The dependency name to check
            
        Returns:
            True if dependency exists, False otherwise
        """
        # Check if any registered service has this name as a parameter
        for service_type, provider in self._services.items():
            if hasattr(service_type, '__init__'):
                sig = inspect.signature(service_type.__init__)
                if name in sig.parameters:
                    return True
        
        # Check instances
        for service_type, instance in self._instances.items():
            if hasattr(service_type, '__init__'):
                sig = inspect.signature(service_type.__init__)
                if name in sig.parameters:
                    return True
        
        return False
    
    async def get_dependency(self, name: str) -> Any:
        """
        Get a dependency by name.
        
        Args:
            name: The dependency name
            
        Returns:
            The dependency instance
            
        Raises:
            ValueError: If dependency is not found
        """
        # Try to find a service that has this parameter
        for service_type, provider in self._services.items():
            if hasattr(service_type, '__init__'):
                sig = inspect.signature(service_type.__init__)
                if name in sig.parameters:
                    return self.get(service_type)
        
        # Check instances
        for service_type, instance in self._instances.items():
            if hasattr(service_type, '__init__'):
                sig = inspect.signature(service_type.__init__)
                if name in sig.parameters:
                    return instance
        
        raise ValueError(f"Dependency '{name}' not found")