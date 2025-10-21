"""
Dependency Injection module.

This module provides dependency injection capabilities for the financial data collector.
"""

from .container import DIContainer
from .providers import ServiceProvider, SingletonProvider, FactoryProvider

__all__ = [
    'DIContainer',
    'ServiceProvider',
    'SingletonProvider', 
    'FactoryProvider'
]
