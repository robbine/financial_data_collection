"""
Web crawler module for financial data collection.

This module provides web crawling capabilities using crawl4ai for:
- Financial news scraping
- Market data collection
- Company information extraction
- Real-time data monitoring
"""

from .web_crawler import WebCrawler
from .api_crawler import APICollector
from .database_crawler import DatabaseCollector
from .enhanced_web_crawler import EnhancedWebCrawler
from .advanced_features import AdvancedCrawler
from .data_classifier import DataClassifier

__all__ = [
    'WebCrawler',
    'APICollector', 
    'DatabaseCollector',
    'EnhancedWebCrawler',
    'AdvancedCrawler',
    'DataClassifier'
]
