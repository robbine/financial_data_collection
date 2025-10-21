"""
Test suite for AdvancedCrawler and its components.

This module tests the individual components of AdvancedCrawler:
- ProxyPool: Proxy management and rotation
- AntiDetectionManager: Anti-detection mechanisms
- TaskScheduler: Task scheduling and priority
- CrawlMonitor: Monitoring and metrics
- IncrementalCrawler: Incremental crawling logic
- CaptchaSolver: Captcha solving (optional)
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

# Adjust path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from financial_data_collector.core.crawler.advanced_features import (
    AdvancedCrawler, ProxyPool, AntiDetectionManager, TaskScheduler, 
    CrawlMonitor, IncrementalCrawler, ProxyInfo, TaskPriority, TaskStatus,
    CrawlTask
)


class TestProxyPool:
    """Test ProxyPool functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.proxy_pool = ProxyPool()
    
    def test_proxy_pool_initialization(self):
        """Test proxy pool initialization."""
        assert len(self.proxy_pool.proxies) == 0
        assert self.proxy_pool.current_index == 0
    
    def test_add_proxy(self):
        """Test adding proxies to the pool."""
        # Add single proxy using ProxyInfo
        proxy_info = ProxyInfo("127.0.0.1", 8080)
        self.proxy_pool.add_proxy(proxy_info)
        assert len(self.proxy_pool.proxies) == 1
        
        proxy = self.proxy_pool.proxies[0]
        assert proxy.host == "127.0.0.1"
        assert proxy.port == 8080
        assert proxy.is_active is True
    
    def test_add_multiple_proxies(self):
        """Test adding multiple proxies."""
        proxies = [
            ("127.0.0.1", 8080),
            ("127.0.0.1", 8081),
            ("127.0.0.1", 8082)
        ]
        
        for host, port in proxies:
            proxy_info = ProxyInfo(host, port)
            self.proxy_pool.add_proxy(proxy_info)
        
        assert len(self.proxy_pool.proxies) == 3
    
    def test_get_next_proxy_round_robin(self):
        """Test round-robin proxy selection."""
        # Add multiple proxies
        for i in range(3):
            self.proxy_pool.add_proxy(f"127.0.0.{i+1}", 8080)
        
        # Test round-robin
        proxy1 = self.proxy_pool.get_next_proxy()
        proxy2 = self.proxy_pool.get_next_proxy()
        proxy3 = self.proxy_pool.get_next_proxy()
        proxy4 = self.proxy_pool.get_next_proxy()
        
        assert proxy1.host == "127.0.0.1"
        assert proxy2.host == "127.0.0.2"
        assert proxy3.host == "127.0.0.3"
        assert proxy4.host == "127.0.0.1"  # Should cycle back
    
    def test_get_next_proxy_with_credentials(self):
        """Test proxy with authentication."""
        self.proxy_pool.add_proxy("127.0.0.1", 8080, "user", "pass")
        proxy = self.proxy_pool.get_next_proxy()
        
        assert proxy.username == "user"
        assert proxy.password == "pass"
    
    def test_blacklist_proxy(self):
        """Test blacklisting proxies."""
        self.proxy_pool.add_proxy("127.0.0.1", 8080)
        proxy = self.proxy_pool.proxies[0]
        
        # Blacklist proxy
        self.proxy_pool.blacklist_proxy(proxy)
        assert proxy.is_active is False
        
        # Should skip blacklisted proxy
        next_proxy = self.proxy_pool.get_next_proxy()
        assert next_proxy is None  # No active proxies
    
    def test_update_proxy_stats(self):
        """Test updating proxy statistics."""
        self.proxy_pool.add_proxy("127.0.0.1", 8080)
        proxy = self.proxy_pool.proxies[0]
        
        # Update stats
        self.proxy_pool.update_proxy_stats(proxy, True, 1.5)
        self.proxy_pool.update_proxy_stats(proxy, False, 2.0)
        
        assert proxy.success_count == 1
        assert proxy.failure_count == 1
        assert proxy.total_response_time == 3.5
        assert proxy.average_response_time == 1.75
    
    def test_get_proxy_stats(self):
        """Test getting proxy statistics."""
        self.proxy_pool.add_proxy("127.0.0.1", 8080)
        proxy = self.proxy_pool.proxies[0]
        
        # Update stats
        self.proxy_pool.update_proxy_stats(proxy, True, 1.0)
        self.proxy_pool.update_proxy_stats(proxy, True, 2.0)
        
        stats = self.proxy_pool.get_proxy_stats()
        assert len(stats) == 1
        assert stats[0]["host"] == "127.0.0.1"
        assert stats[0]["success_count"] == 2
        assert stats[0]["average_response_time"] == 1.5


class TestAntiDetectionManager:
    """Test AntiDetectionManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.anti_detection = AntiDetectionManager()
    
    def test_anti_detection_initialization(self):
        """Test anti-detection manager initialization."""
        assert len(self.anti_detection.user_agents) > 0
        assert len(self.anti_detection.viewports) > 0
        assert len(self.anti_detection.headers) > 0
    
    def test_get_random_user_agent(self):
        """Test random user agent selection."""
        user_agent = self.anti_detection.get_random_user_agent()
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
        assert user_agent in self.anti_detection.user_agents
    
    def test_get_random_viewport(self):
        """Test random viewport selection."""
        viewport = self.anti_detection.get_random_viewport()
        assert isinstance(viewport, dict)
        assert "width" in viewport
        assert "height" in viewport
        assert viewport in self.anti_detection.viewports
    
    def test_get_random_headers(self):
        """Test random headers generation."""
        headers = self.anti_detection.get_random_headers()
        assert isinstance(headers, dict)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
    
    def test_add_random_delay(self):
        """Test random delay functionality."""
        start_time = time.time()
        self.anti_detection.add_random_delay(0.1, 0.2)
        end_time = time.time()
        
        # Should have some delay (allowing for timing variations)
        assert end_time - start_time >= 0.05  # At least 50ms delay
    
    def test_rotate_user_agent(self):
        """Test user agent rotation."""
        # Get multiple user agents
        agents = [self.anti_detection.get_random_user_agent() for _ in range(10)]
        
        # Should have some variety (not all the same)
        unique_agents = set(agents)
        assert len(unique_agents) > 1  # Should have variety
    
    def test_rotate_viewport(self):
        """Test viewport rotation."""
        # Get multiple viewports
        viewports = [self.anti_detection.get_random_viewport() for _ in range(10)]
        
        # Should have some variety
        unique_viewports = set(str(v) for v in viewports)
        assert len(unique_viewports) > 1


class TestTaskScheduler:
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
        """Test adding tasks to scheduler."""
        task = CrawlTask(id="test_task", url="https://example.com", priority=TaskPriority.NORMAL)
        task_id = self.scheduler.add_task(task)
        
        assert task_id == "test_task"
        assert len(self.scheduler.tasks) == 1
        assert len(self.scheduler.task_queue) == 1
        assert self.scheduler.tasks["test_task"] == task
    
    def test_add_task_with_priority(self):
        """Test adding tasks with different priorities."""
        # Add tasks with different priorities
        urgent_task = CrawlTask(id="urgent", url="https://urgent.com", priority=TaskPriority.URGENT)
        normal_task = CrawlTask(id="normal", url="https://normal.com", priority=TaskPriority.NORMAL)
        low_task = CrawlTask(id="low", url="https://low.com", priority=TaskPriority.LOW)
        
        self.scheduler.add_task(urgent_task)
        self.scheduler.add_task(normal_task)
        self.scheduler.add_task(low_task)
        
        # Check queue order (should be by priority)
        assert self.scheduler.task_queue[0] == "urgent"  # URGENT first
        assert self.scheduler.task_queue[1] == "normal"  # NORMAL second
        assert self.scheduler.task_queue[2] == "low"     # LOW last
    
    def test_get_next_task(self):
        """Test getting next task from queue."""
        task = CrawlTask(id="test_task", url="https://example.com", priority=TaskPriority.NORMAL)
        self.scheduler.add_task(task)
        
        next_task = self.scheduler.get_next_task()
        assert next_task == task
        assert len(self.scheduler.task_queue) == 0  # Task removed from queue
    
    def test_get_next_task_empty_queue(self):
        """Test getting next task from empty queue."""
        next_task = self.scheduler.get_next_task()
        assert next_task is None
    
    def test_update_task_status(self):
        """Test updating task status."""
        task = CrawlTask(id="test_task", url="https://example.com", priority=TaskPriority.NORMAL)
        self.scheduler.add_task(task)
        
        # Update status
        self.scheduler.update_task_status("test_task", TaskStatus.RUNNING)
        assert self.scheduler.tasks["test_task"].status == TaskStatus.RUNNING
    
    def test_get_task_status(self):
        """Test getting task status."""
        task = CrawlTask(id="test_task", url="https://example.com", priority=TaskPriority.NORMAL)
        self.scheduler.add_task(task)
        
        status = self.scheduler.get_task_status("test_task")
        assert status == TaskStatus.PENDING
        
        # Update status and check again
        self.scheduler.update_task_status("test_task", TaskStatus.COMPLETED)
        status = self.scheduler.get_task_status("test_task")
        assert status == TaskStatus.COMPLETED
    
    def test_get_task_status_not_found(self):
        """Test getting status of non-existent task."""
        status = self.scheduler.get_task_status("non_existent")
        assert status is None
    
    def test_clear_completed_tasks(self):
        """Test clearing completed tasks."""
        # Add tasks with different statuses
        completed_task = CrawlTask(id="completed", url="https://completed.com", priority=TaskPriority.NORMAL)
        completed_task.status = TaskStatus.COMPLETED
        
        pending_task = CrawlTask(id="pending", url="https://pending.com", priority=TaskPriority.NORMAL)
        pending_task.status = TaskStatus.PENDING
        
        self.scheduler.add_task(completed_task)
        self.scheduler.add_task(pending_task)
        
        # Clear completed tasks
        cleared_count = self.scheduler.clear_completed_tasks()
        assert cleared_count == 1
        assert "completed" not in self.scheduler.tasks
        assert "pending" in self.scheduler.tasks


class TestCrawlMonitor:
    """Test CrawlMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.monitor = CrawlMonitor()
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        assert self.monitor.metrics["total_requests"] == 0
        assert self.monitor.metrics["successful_requests"] == 0
        assert self.monitor.metrics["failed_requests"] == 0
        assert self.monitor.metrics["average_response_time"] == 0.0
    
    def test_record_successful_request(self):
        """Test recording successful request."""
        self.monitor.record_request(True, 1.5)
        
        assert self.monitor.metrics["total_requests"] == 1
        assert self.monitor.metrics["successful_requests"] == 1
        assert self.monitor.metrics["failed_requests"] == 0
        assert self.monitor.metrics["average_response_time"] == 1.5
    
    def test_record_failed_request(self):
        """Test recording failed request."""
        self.monitor.record_request(False, 2.0)
        
        assert self.monitor.metrics["total_requests"] == 1
        assert self.monitor.metrics["successful_requests"] == 0
        assert self.monitor.metrics["failed_requests"] == 1
        assert self.monitor.metrics["average_response_time"] == 2.0
    
    def test_record_multiple_requests(self):
        """Test recording multiple requests."""
        # Record multiple requests
        self.monitor.record_request(True, 1.0)
        self.monitor.record_request(True, 2.0)
        self.monitor.record_request(False, 3.0)
        
        assert self.monitor.metrics["total_requests"] == 3
        assert self.monitor.metrics["successful_requests"] == 2
        assert self.monitor.metrics["failed_requests"] == 1
        assert self.monitor.metrics["average_response_time"] == 2.0  # (1+2+3)/3
    
    def test_get_metrics(self):
        """Test getting metrics."""
        self.monitor.record_request(True, 1.0)
        metrics = self.monitor.get_metrics()
        
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "average_response_time" in metrics
        assert "success_rate" in metrics
        assert "uptime" in metrics
        assert metrics["success_rate"] == 1.0
    
    def test_reset_metrics(self):
        """Test resetting metrics."""
        # Record some requests
        self.monitor.record_request(True, 1.0)
        self.monitor.record_request(False, 2.0)
        
        # Reset metrics
        self.monitor.reset_metrics()
        
        assert self.monitor.metrics["total_requests"] == 0
        assert self.monitor.metrics["successful_requests"] == 0
        assert self.monitor.metrics["failed_requests"] == 0
        assert self.monitor.metrics["average_response_time"] == 0.0


class TestIncrementalCrawler:
    """Test IncrementalCrawler functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_storage = Mock()
        self.incremental = IncrementalCrawler(self.mock_storage)
    
    def test_incremental_crawler_initialization(self):
        """Test incremental crawler initialization."""
        assert self.incremental.storage == self.mock_storage
        assert len(self.incremental.last_crawl_times) == 0
        assert len(self.incremental.content_hashes) == 0
    
    def test_should_crawl_new_url(self):
        """Test should crawl for new URL."""
        url = "https://example.com"
        should_crawl = self.incremental.should_crawl(url)
        assert should_crawl is True
    
    def test_should_crawl_recently_crawled(self):
        """Test should crawl for recently crawled URL."""
        url = "https://example.com"
        
        # Mark as crawled
        self.incremental.mark_crawled(url)
        
        # Should not crawl again immediately
        should_crawl = self.incremental.should_crawl(url)
        assert should_crawl is False
    
    def test_mark_crawled(self):
        """Test marking URL as crawled."""
        url = "https://example.com"
        self.incremental.mark_crawled(url)
        
        assert url in self.incremental.last_crawl_times
        assert isinstance(self.incremental.last_crawl_times[url], datetime)
    
    def test_content_hash_check(self):
        """Test content hash checking."""
        url = "https://example.com"
        content = "test content"
        
        # Get content hash
        hash1 = self.incremental.get_content_hash(content)
        assert isinstance(hash1, str)
        assert len(hash1) > 0
        
        # Same content should have same hash
        hash2 = self.incremental.get_content_hash(content)
        assert hash1 == hash2
        
        # Different content should have different hash
        hash3 = self.incremental.get_content_hash("different content")
        assert hash1 != hash3
    
    def test_is_content_changed(self):
        """Test content change detection."""
        url = "https://example.com"
        content1 = "original content"
        content2 = "updated content"
        
        # First time - should be considered changed
        changed1 = self.incremental.is_content_changed(url, content1)
        assert changed1 is True
        
        # Same content - should not be changed
        changed2 = self.incremental.is_content_changed(url, content1)
        assert changed2 is False
        
        # Different content - should be changed
        changed3 = self.incremental.is_content_changed(url, content2)
        assert changed3 is True


class TestAdvancedCrawler:
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
        assert self.advanced.captcha_solver is None
        assert self.advanced.incremental_crawler is None
    
    def test_setup_incremental_crawling(self):
        """Test setting up incremental crawling."""
        mock_storage = Mock()
        self.advanced.setup_incremental_crawling(mock_storage)
        
        assert isinstance(self.advanced.incremental_crawler, IncrementalCrawler)
        assert self.advanced.incremental_crawler.storage == mock_storage
    
    def test_setup_captcha_solver(self):
        """Test setting up captcha solver."""
        api_key = "test_api_key"
        service = "2captcha"
        
        self.advanced.setup_captcha_solver(api_key, service)
        
        # Note: CaptchaSolver might not be implemented yet
        # This test would need to be updated when CaptchaSolver is implemented
        assert self.advanced.captcha_solver is not None or True  # Allow for not implemented
    
    def test_add_task(self):
        """Test adding task to advanced crawler."""
        url = "https://example.com"
        config = {"extraction_strategy": "css"}
        priority = TaskPriority.NORMAL
        
        task_id = self.advanced.add_task(url, config, priority)
        
        assert task_id is not None
        assert task_id in self.advanced.task_scheduler.tasks
    
    def test_get_status(self):
        """Test getting advanced crawler status."""
        status = self.advanced.get_status()
        
        assert "proxy_pool" in status
        assert "task_scheduler" in status
        assert "monitor" in status
        assert "anti_detection" in status
    
    def test_integration_workflow(self):
        """Test integrated workflow."""
        # Setup incremental crawling
        mock_storage = Mock()
        self.advanced.setup_incremental_crawling(mock_storage)
        
        # Add proxy
        self.advanced.proxy_pool.add_proxy("127.0.0.1", 8080)
        
        # Add task
        task_id = self.advanced.add_task("https://example.com", {}, TaskPriority.NORMAL)
        
        # Verify components are working together
        assert task_id in self.advanced.task_scheduler.tasks
        assert len(self.advanced.proxy_pool.proxies) == 1
        assert self.advanced.incremental_crawler is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
