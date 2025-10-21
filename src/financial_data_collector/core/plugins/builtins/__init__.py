"""
Built-in plugins for the financial data collector.
"""

from .sentiment import SentimentAnalysisPlugin
from .entity_extraction import EntityExtractionPlugin
from .data_classification import DataClassificationPlugin

__all__ = [
    'SentimentAnalysisPlugin',
    'EntityExtractionPlugin',
    'DataClassificationPlugin'
]
