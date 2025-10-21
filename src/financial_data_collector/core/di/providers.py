"""
Service Providers for Dependency Injection.

This module contains various service provider implementations for the DI container.
"""

from typing import Any, Type, Callable, Optional
import threading
from abc import ABC, abstractmethod


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


class TransientProvider(ServiceProvider):
    """Provider for transient services (new instance each time)."""
    
    def __init__(self, service_class: Type, *args, **kwargs):
        self._service_class = service_class
        self._args = args
        self._kwargs = kwargs
    
    def get_instance(self) -> Any:
        """Get new instance."""
        return self._service_class(*self._args, **self._kwargs)


class ScopedProvider(ServiceProvider):
    """Provider for scoped services (one instance per scope)."""
    
    def __init__(self, service_class: Type, *args, **kwargs):
        self._service_class = service_class
        self._args = args
        self._kwargs = kwargs
        self._scope_instances: dict = {}
        self._lock = threading.Lock()
    
    def get_instance(self, scope_id: str = "default") -> Any:
        """Get scoped instance."""
        if scope_id not in self._scope_instances:
            with self._lock:
                if scope_id not in self._scope_instances:
                    self._scope_instances[scope_id] = self._service_class(*self._args, **self._kwargs)
        return self._scope_instances[scope_id]
    
    def clear_scope(self, scope_id: str):
        """Clear a specific scope."""
        if scope_id in self._scope_instances:
            del self._scope_instances[scope_id]
    
    def clear_all_scopes(self):
        """Clear all scopes."""
        self._scope_instances.clear()
