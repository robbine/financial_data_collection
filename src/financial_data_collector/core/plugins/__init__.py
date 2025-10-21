"""
Plugin System module.

This module provides plugin capabilities for extending the financial data collector including:
- Plugin registry and management
- Base plugin classes
- Built-in plugins for common functionality
"""

from .registry import PluginRegistry
from .base import Plugin, DataProcessorPlugin, DataCollectorPlugin, DataTransformerPlugin
from .builtins.sentiment import SentimentAnalysisPlugin
from .builtins.entity_extraction import EntityExtractionPlugin
from .builtins.data_classification import DataClassificationPlugin

__all__ = [
    'PluginRegistry',
    'Plugin',
    'DataProcessorPlugin',
    'DataCollectorPlugin', 
    'DataTransformerPlugin',
    'SentimentAnalysisPlugin',
    'EntityExtractionPlugin',
    'DataClassificationPlugin'
]
