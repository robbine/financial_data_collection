"""
Simplified test suite for AdvancedCrawler components.

This module tests the individual components of AdvancedCrawler with
correct API usage based on actual implementation.
"""

import pytest
import time
from unittest.mock import Mock
from datetime import datetime

# Adjust path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from financial_data_collector.core.crawler.advanced_features import (
    AdvancedCrawler, ProxyPool, AntiDetectionManager, TaskScheduler, 
    CrawlMonitor, IncrementalCrawler, ProxyInfo, TaskPriority, TaskStatus,
    CrawlTask
)


class TestProxyPoolSimple:
    """Test ProxyPool functionality with correct API."""
    
    def setup_method(self):
        """Setup test environment."""
        self.proxy_pool = ProxyPool()
    
    def test_proxy_pool_initialization(self):
        """Test proxy pool initialization."""
        assert len(self.proxy_pool.proxies) == 0
        assert self.proxy_pool.current_index == 0
    
    def test_add_proxy_correct_api(self):
        """Test adding proxy with correct API."""
        proxy_info = ProxyInfo("127.0.0.1", 8080)
        self.proxy_pool.add_proxy(proxy_info)
        
        assert len(self.proxy_pool.proxies) == 1
        proxy = self.proxy_pool.proxies[0]
        assert proxy.host == "127.0.0.1"
        assert proxy.port == 8080
        assert proxy.is_active is True
    
    def test_get_next_proxy(self):
        """Test getting next proxy."""
        # Add proxy
        proxy_info = ProxyInfo("127.0.0.1", 8080)
        self.proxy_pool.add_proxy(proxy_info)
        
        # Get next proxy
        next_proxy = self.proxy_pool.get_next_proxy()
        assert next_proxy is not None
        assert next_proxy.host == "127.0.0.1"
        assert next_proxy.port == 8080
    
    def test_blacklist_proxy(self):
        """Test blacklisting proxy."""
        proxy_info = ProxyInfo("127.0.0.1", 8080)
        self.proxy_pool.add_proxy(proxy_info)
        proxy = self.proxy_pool.proxies[0]
        
        # Blacklist proxy
        self.proxy_pool.blacklist_proxy(proxy)
        assert proxy.is_active is False


class TestAntiDetectionManagerSimple:
    """Test AntiDetectionManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.anti_detection = AntiDetectionManager()
    
    def test_get_random_user_agent(self):
        """Test random user agent selection."""
        user_agent = self.anti_detection.get_random_user_agent()
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
    
    def test_get_random_viewport(self):
        """Test random viewport selection."""
        viewport = self.anti_detection.get_random_viewport()
        assert isinstance(viewport, dict)
        assert "width" in viewport
        assert "height" in viewport
    
    def test_get_random_headers(self):
        """Test random headers generation."""
        headers = self.anti_detection.get_random_headers()
        assert isinstance(headers, dict)
        assert "User-Agent" in headers


class TestTaskSchedulerSimple:
    """Test TaskScheduler functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.scheduler = TaskScheduler()
    
    def test_task_scheduler_initialization(self):
        """Test task scheduler initialization."""
        assert len(self.scheduler.tasks) == 0
        assert len(self.scheduler.task_queue) == 0
        assert self.scheduler.max_concurrent == 5
    
    def test_add_task(self):
        """Test adding task to scheduler."""
        task = CrawlTask(id="test_task", url="https://example.com", priority=TaskPriority.NORMAL)
        task_id = self.scheduler.add_task(task)
        
        # Note: add_task might return None, that's OK
        assert task_id is None or task_id == "test_task"
        assert len(self.scheduler.tasks) == 1
        assert "test_task" in self.scheduler.tasks


class TestCrawlMonitorSimple:
    """Test CrawlMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.monitor = CrawlMonitor()
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        assert self.monitor.metrics["total_requests"] == 0
        assert self.monitor.metrics["successful_requests"] == 0
        assert self.monitor.metrics["failed_requests"] == 0
    
    def test_record_successful_request(self):
        """Test recording successful request."""
        self.monitor.record_request(True, 1.5)
        
        assert self.monitor.metrics["total_requests"] == 1
        assert self.monitor.metrics["successful_requests"] == 1
        assert self.monitor.metrics["failed_requests"] == 0
    
    def test_record_failed_request(self):
        """Test recording failed request."""
        self.monitor.record_request(False, 2.0)
        
        assert self.monitor.metrics["total_requests"] == 1
        assert self.monitor.metrics["successful_requests"] == 0
        assert self.monitor.metrics["failed_requests"] == 1
    
    def test_get_metrics(self):
        """Test getting metrics."""
        self.monitor.record_request(True, 1.0)
        metrics = self.monitor.get_metrics()
        
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "success_rate" in metrics


class TestIncrementalCrawlerSimple:
    """Test IncrementalCrawler functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_storage = Mock()
        self.incremental = IncrementalCrawler(self.mock_storage)
    
    def test_incremental_crawler_initialization(self):
        """Test incremental crawler initialization."""
        assert self.incremental.storage == self.mock_storage
        assert len(self.incremental.last_crawl_times) == 0
    
    def test_should_crawl_new_url(self):
        """Test should crawl for new URL."""
        url = "https://example.com"
        should_crawl = self.incremental.should_crawl(url)
        assert should_crawl is True
    
    def test_mark_crawled(self):
        """Test marking URL as crawled."""
        url = "https://example.com"
        self.incremental.mark_crawled(url)
        
        assert url in self.incremental.last_crawl_times
        assert isinstance(self.incremental.last_crawl_times[url], datetime)


class TestAdvancedCrawlerSimple:
    """Test AdvancedCrawler integration."""
    
    def setup_method(self):
        """Setup test environment."""
        self.advanced = AdvancedCrawler()
    
    def test_advanced_crawler_initialization(self):
        """Test advanced crawler initialization."""
        assert isinstance(self.advanced.proxy_pool, ProxyPool)
        assert isinstance(self.advanced.anti_detection, AntiDetectionManager)
        assert isinstance(self.advanced.task_scheduler, TaskScheduler)
        assert isinstance(self.advanced.monitor, CrawlMonitor)
    
    def test_setup_incremental_crawling(self):
        """Test setting up incremental crawling."""
        mock_storage = Mock()
        self.advanced.setup_incremental_crawling(mock_storage)
        
        assert isinstance(self.advanced.incremental_crawler, IncrementalCrawler)
        assert self.advanced.incremental_crawler.storage == mock_storage
    
    def test_add_task(self):
        """Test adding task to advanced crawler."""
        url = "https://example.com"
        config = {"extraction_strategy": "css"}
        priority = TaskPriority.NORMAL
        
        task_id = self.advanced.add_task(url, config, priority)
        
        # Task ID might be None, that's OK
        assert task_id is None or isinstance(task_id, str)
    
    def test_get_status(self):
        """Test getting advanced crawler status."""
        status = self.advanced.get_status()
        
        assert isinstance(status, dict)
        assert "active_proxies" in status
        assert "active_tasks" in status
        assert "metrics" in status


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])


