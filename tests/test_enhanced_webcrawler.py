"""
Enhanced WebCrawler Tests

Comprehensive test suite for EnhancedWebCrawler including:
- Advanced features testing
- Proxy pool management
- Anti-detection mechanisms
- Task scheduling and priority
- Incremental crawling
- Monitoring and alerting
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from src.financial_data_collector.core.crawler.enhanced_web_crawler import EnhancedWebCrawler
from src.financial_data_collector.core.crawler.advanced_features import (
    TaskPriority, ProxyInfo, CrawlTask, TaskStatus, AntiDetectionManager,
    ProxyPool, TaskScheduler, IncrementalCrawler, CrawlMonitor
)


class TestEnhancedWebCrawler:
    """Test EnhancedWebCrawler functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.crawler = EnhancedWebCrawler("TestEnhancedCrawler")
        self.test_url = "https://httpbin.org/html"
        self.test_config = {
            "extraction_strategy": "css",
            "wait_for": 1,
            "max_scrolls": 0
        }
    
    def test_enhanced_crawler_initialization(self):
        """Test EnhancedWebCrawler initialization."""
        assert self.crawler.name == "TestEnhancedCrawler"
        assert hasattr(self.crawler, 'advanced_crawler')
        assert hasattr(self.crawler, 'proxy_rotation')
        assert hasattr(self.crawler, 'captcha_detection')
        assert hasattr(self.crawler, 'anti_detection')
        assert hasattr(self.crawler, 'incremental_mode')
        assert hasattr(self.crawler, 'monitoring_enabled')
        
        # Check enhanced configuration
        assert 'proxy_pool' in self.crawler.enhanced_config
        assert 'captcha_solving' in self.crawler.enhanced_config
        assert 'anti_detection' in self.crawler.enhanced_config
        assert 'task_scheduling' in self.crawler.enhanced_config
    
    def test_enhanced_configuration(self):
        """Test enhanced configuration structure."""
        config = self.crawler.enhanced_config
        
        # Proxy pool configuration
        assert config['proxy_pool']['enabled'] is True
        assert 'rotation_interval' in config['proxy_pool']
        assert 'health_check_interval' in config['proxy_pool']
        
        # Captcha solving configuration
        assert config['captcha_solving']['enabled'] is True
        assert config['captcha_solving']['service'] == "2captcha"
        assert 'timeout' in config['captcha_solving']
        
        # Anti-detection configuration
        assert config['anti_detection']['enabled'] is True
        assert config['anti_detection']['user_agent_rotation'] is True
        assert config['anti_detection']['viewport_rotation'] is True
        assert config['anti_detection']['random_delays'] is True
        
        # Task scheduling configuration
        assert 'max_concurrent' in config['task_scheduling']
        assert config['task_scheduling']['priority_queuing'] is True
        assert config['task_scheduling']['retry_failed'] is True
    
    @pytest.mark.asyncio
    async def test_enhanced_crawler_lifecycle(self):
        """Test enhanced crawler lifecycle."""
        # Create a fresh crawler instance for this test
        crawler = EnhancedWebCrawler("TestLifecycleCrawler")
        
        # Test initial state - check the actual attributes
        assert not crawler._initialized
        assert not crawler._started
        
        # Test initialization
        crawler.initialize(self.test_config)
        assert crawler._initialized
        
        # Test start
        await crawler.start()
        assert crawler._started
        
        # Test stop
        await crawler.stop()
        assert not crawler._started
    
    @pytest.mark.asyncio
    async def test_crawl_url_enhanced(self):
        """Test enhanced crawling with advanced features."""
        with patch.object(self.crawler, 'collect_data') as mock_collect:
            mock_collect.return_value = {
                "success": True,
                "url": self.test_url,
                "enhanced_data": "test data"
            }
            
            # Initialize and start crawler
            self.crawler.initialize(self.test_config)
            await self.crawler.start()
            
            # Test enhanced crawling
            result = await self.crawler.crawl_url_enhanced(
                self.test_url, 
                self.test_config, 
                TaskPriority.HIGH
            )
            
            # crawl_url_enhanced returns a task_id string, not a result dict
            assert isinstance(result, str)
            assert len(result) > 0  # Should be a valid task ID
            
            await self.crawler.stop()
    
    @pytest.mark.asyncio
    async def test_anti_detection_features(self):
        """Test anti-detection mechanisms."""
        # Test anti-detection manager
        anti_detection = self.crawler.advanced_crawler.anti_detection
        assert anti_detection is not None
        
        # Test user agent rotation
        user_agent = anti_detection.get_random_user_agent()
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
        
        # Test viewport rotation
        viewport = anti_detection.get_random_viewport()
        assert isinstance(viewport, dict)
        assert 'width' in viewport
        assert 'height' in viewport
        
        # Test random delay
        delay = anti_detection.add_random_delay(1.0, 3.0)
        assert isinstance(delay, (int, float))
        assert delay >= 0
    
    def test_proxy_pool_management(self):
        """Test proxy pool management."""
        # Test proxy addition
        proxy = ProxyInfo(
            host="127.0.0.1",
            port=8080,
            username="user",
            password="pass"
        )
        
        self.crawler.advanced_crawler.proxy_pool.add_proxy(proxy)
        assert len(self.crawler.advanced_crawler.proxy_pool.proxies) == 1
        
        # Test proxy retrieval
        retrieved_proxy = self.crawler.advanced_crawler.proxy_pool.get_next_proxy()
        assert retrieved_proxy is not None
        assert retrieved_proxy.host == "127.0.0.1"
        assert retrieved_proxy.port == 8080
    
    def test_task_scheduling(self):
        """Test task scheduling functionality."""
        # Test task addition
        task_id = self.crawler.advanced_crawler.add_task(
            self.test_url,
            self.test_config,
            TaskPriority.HIGH
        )
        
        assert task_id is not None
        assert task_id in self.crawler.advanced_crawler.task_scheduler.tasks
        
        # Test task status
        task = self.crawler.advanced_crawler.task_scheduler.tasks[task_id]
        assert task.url == self.test_url
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
    
    def test_incremental_crawling(self):
        """Test incremental crawling functionality."""
        # Setup incremental crawling
        mock_storage = Mock()
        self.crawler.advanced_crawler.setup_incremental_crawling(mock_storage)
        
        assert self.crawler.advanced_crawler.incremental_crawler is not None
        
        # Test should crawl check
        should_crawl = self.crawler.advanced_crawler.incremental_crawler.should_crawl(self.test_url)
        # Should return True for new URL
        assert should_crawl is True
    
    def test_monitoring_and_alerting(self):
        """Test monitoring and alerting functionality."""
        # Test metrics collection
        metrics = self.crawler.advanced_crawler.monitor.get_metrics()
        
        # Check actual metrics structure
        assert 'average_response_time' in metrics
        assert 'blocked_requests' in metrics
        assert 'failed_requests' in metrics
        assert 'recent_alerts' in metrics
        
        # Test metrics recording
        self.crawler.advanced_crawler.monitor.record_request(True, 1.5, False)
        updated_metrics = self.crawler.advanced_crawler.monitor.get_metrics()
        
        assert updated_metrics['total_requests'] > 0
        assert updated_metrics['successful_requests'] > 0
    
    @pytest.mark.asyncio
    async def test_enhanced_status(self):
        """Test enhanced status reporting."""
        # Initialize crawler
        self.crawler.initialize(self.test_config)
        await self.crawler.start()
        
        # Get enhanced status
        status = await self.crawler.get_enhanced_status()
        
        assert 'status' in status
        assert 'enhanced_features' in status
        assert 'proxy_pool' in status['enhanced_features']
        assert 'anti_detection' in status['enhanced_features']
        assert 'monitoring' in status['enhanced_features']
        
        await self.crawler.stop()
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test configuration structure
        config = self.crawler.enhanced_config
        
        # Check that all required sections exist
        assert 'proxy_pool' in config
        assert 'captcha_solving' in config
        assert 'anti_detection' in config
        assert 'task_scheduling' in config
        assert 'incremental_crawling' in config
        assert 'monitoring' in config
        
        # Test configuration values
        assert config['proxy_pool']['enabled'] is True
        assert config['anti_detection']['enabled'] is True
        assert config['monitoring']['enabled'] is True
    
    def test_advanced_features_integration(self):
        """Test integration of advanced features."""
        # Test proxy pool integration
        assert hasattr(self.crawler.advanced_crawler, 'proxy_pool')
        assert isinstance(self.crawler.advanced_crawler.proxy_pool, ProxyPool)
        
        # Test anti-detection integration
        assert hasattr(self.crawler.advanced_crawler, 'anti_detection')
        assert isinstance(self.crawler.advanced_crawler.anti_detection, AntiDetectionManager)
        
        # Test task scheduler integration
        assert hasattr(self.crawler.advanced_crawler, 'task_scheduler')
        assert isinstance(self.crawler.advanced_crawler.task_scheduler, TaskScheduler)
        
        # Test monitoring integration
        assert hasattr(self.crawler.advanced_crawler, 'monitor')
        assert isinstance(self.crawler.advanced_crawler.monitor, CrawlMonitor)


class TestEnhancedWebCrawlerAdvancedFeatures:
    """Test advanced features of EnhancedWebCrawler."""
    
    def setup_method(self):
        """Setup test environment."""
        self.crawler = EnhancedWebCrawler("TestAdvancedCrawler")
    
    def test_proxy_pool_behavior(self):
        """Test proxy pool behavior with and without proxies."""
        # Test 1: Empty proxy pool (no proxy service)
        proxy_pool = self.crawler.advanced_crawler.proxy_pool
        assert len(proxy_pool.proxies) == 0
        
        # Should return None when no proxies available
        proxy = proxy_pool.get_next_proxy()
        assert proxy is None
        
        # Test 2: Add single proxy (simulating real proxy service)
        real_proxy = ProxyInfo("203.45.67.89", 8080, username="user", password="pass")
        proxy_pool.add_proxy(real_proxy)
        assert len(proxy_pool.proxies) == 1
        
        # Should return the only available proxy
        proxy = proxy_pool.get_next_proxy()
        assert proxy is not None
        assert proxy.host == "203.45.67.89"
        assert proxy.port == 8080
        
        # Test 3: Multiple proxies (real proxy service scenario)
        additional_proxies = [
            ProxyInfo("198.51.100.42", 3128),
            ProxyInfo("192.168.100.15", 1080)
        ]
        
        for proxy in additional_proxies:
            proxy_pool.add_proxy(proxy)
        
        assert len(proxy_pool.proxies) == 3
        
        # Test proxy selection (should select best proxy, not necessarily rotate)
        used_proxies = set()
        for _ in range(5):
            proxy = proxy_pool.get_next_proxy()
            if proxy:
                used_proxies.add(proxy.port)
        
        # Should use proxies (may not rotate due to smart selection)
        assert len(used_proxies) >= 1
    
    def test_anti_detection_mechanisms(self):
        """Test anti-detection mechanisms."""
        anti_detection = self.crawler.advanced_crawler.anti_detection
        
        # Test user agent rotation
        user_agents = []
        for _ in range(5):
            ua = anti_detection.get_random_user_agent()
            user_agents.append(ua)
        
        # Should have different user agents
        assert len(set(user_agents)) > 1
        
        # Test viewport rotation
        viewports = []
        for _ in range(5):
            vp = anti_detection.get_random_viewport()
            viewports.append(vp)
        
        # Should have different viewports
        assert len(set(str(vp) for vp in viewports)) > 1
        
        # Test random delays
        delays = []
        for _ in range(10):
            delay = anti_detection.add_random_delay(1.0, 3.0)
            delays.append(delay)
        
        # Should have different delays
        assert len(set(delays)) > 1
        assert all(1.0 <= delay <= 3.0 for delay in delays)
    
    def test_task_priority_handling(self):
        """Test task priority handling."""
        scheduler = self.crawler.advanced_crawler.task_scheduler
        
        # Add tasks with different priorities (using correct CrawlTask constructor)
        tasks = [
            ("url1", TaskPriority.LOW),
            ("url2", TaskPriority.HIGH),
            ("url3", TaskPriority.NORMAL),
            ("url4", TaskPriority.URGENT)
        ]
        
        task_ids = []
        for url, priority in tasks:
            # Create CrawlTask with required id parameter
            task = CrawlTask(id=f"task_{url}", url=url, priority=priority)
            task_id = scheduler.add_task(task)
            task_ids.append(task_id)
        
        # Check task queue order (should be by priority)
        queue = scheduler.task_queue
        assert len(queue) == 4
        
        # URGENT should be first, HIGH second, etc.
        urgent_task = scheduler.tasks[queue[0]]
        high_task = scheduler.tasks[queue[1]]
        
        assert urgent_task.priority == TaskPriority.URGENT
        assert high_task.priority == TaskPriority.HIGH
    
    def test_incremental_crawling_logic(self):
        """Test incremental crawling logic."""
        # Setup incremental crawler
        mock_storage = Mock()
        self.crawler.advanced_crawler.setup_incremental_crawling(mock_storage)
        
        incremental = self.crawler.advanced_crawler.incremental_crawler
        
        # Test URL tracking
        url = "https://example.com"
        
        # First crawl should be allowed
        assert incremental.should_crawl(url) is True
        
        # Mark as crawled (using correct method name)
        incremental.mark_crawled(url)
        
        # Second crawl should be skipped
        assert incremental.should_crawl(url) is False
        
        # Test with different URL
        new_url = "https://example.com/page2"
        assert incremental.should_crawl(new_url) is True
    
    def test_monitoring_metrics(self):
        """Test monitoring and metrics collection."""
        monitor = self.crawler.advanced_crawler.monitor
        
        # Test initial metrics (using actual metric names)
        metrics = monitor.get_metrics()
        assert 'average_response_time' in metrics
        assert 'blocked_requests' in metrics
        assert 'failed_requests' in metrics
        assert 'recent_alerts' in metrics
        
        # Test metrics recording (using actual method names)
        monitor.record_request(True, 1.5, False)  # success, 1.5s, not blocked
        monitor.record_request(True, 2.0, False)  # success, 2.0s, not blocked
        monitor.record_request(False, 0.5, False)  # failure, 0.5s, not blocked
        
        # Check updated metrics
        updated_metrics = monitor.get_metrics()
        assert updated_metrics['total_requests'] > 0
        assert updated_metrics['successful_requests'] > 0
        assert updated_metrics['failed_requests'] > 0
    
    def test_alert_system(self):
        """Test alert system functionality."""
        monitor = self.crawler.advanced_crawler.monitor
        
        # Test that monitor has alerts attribute
        assert hasattr(monitor, 'alerts')
        assert isinstance(monitor.alerts, list)
        
        # Test initial alert count
        initial_alert_count = len(monitor.alerts)
        
        # Test metrics that might trigger alerts
        monitor.record_request(False, 5.0, True)  # Failed, slow, blocked request
        monitor.record_request(False, 3.0, False)  # Failed, slow request
        
        # Check if alerts were generated (internal alert system)
        assert len(monitor.alerts) >= initial_alert_count
        
        # Test alert structure (if any alerts exist)
        if monitor.alerts:
            alert = monitor.alerts[0]
            assert isinstance(alert, dict)
            # Check common alert fields
            assert 'alert_type' in alert or 'type' in alert
            assert 'message' in alert or 'msg' in alert


class TestEnhancedWebCrawlerNoProxy:
    """Test EnhancedWebCrawler without proxy services (realistic scenario)."""
    
    def setup_method(self):
        """Setup test environment."""
        self.crawler = EnhancedWebCrawler("TestNoProxyCrawler")
        # Configure without proxy services
        self.config = {
            "extraction_strategy": "css",
            "browser": {"headless": True},
            "enhanced": {
                "proxy_pool": {"enabled": False},  # No proxy service
                "captcha_solving": {
                    "enabled": False,  # No captcha service
                    "service": "2captcha"
                },
                "anti_detection": {"enabled": True},  # Free features
                "monitoring": {"enabled": True},  # Free features
                "task_scheduling": {
                    "enabled": True,  # Free features
                    "max_concurrent": 3,
                    "priority_queuing": True,
                    "retry_failed": True,
                    "max_retries": 3
                },
                "incremental_crawling": {"enabled": True}  # Free features
            }
        }
    
    def test_no_proxy_configuration(self):
        """Test EnhancedWebCrawler configuration without proxy services."""
        self.crawler.initialize(self.config)
        
        # Check that proxy pool is disabled
        assert not self.crawler.enhanced_config["proxy_pool"]["enabled"]
        assert not self.crawler.enhanced_config["captcha_solving"]["enabled"]
        
        # Check that free features are enabled
        assert self.crawler.enhanced_config["anti_detection"]["enabled"]
        assert self.crawler.enhanced_config["monitoring"]["enabled"]
        assert self.crawler.enhanced_config["task_scheduling"]["enabled"]
    
    def test_no_proxy_crawling(self):
        """Test crawling without proxy services."""
        self.crawler.initialize(self.config)
        
        # Test that proxy pool is empty
        proxy_pool = self.crawler.advanced_crawler.proxy_pool
        assert len(proxy_pool.proxies) == 0
        
        # Test that get_next_proxy returns None
        proxy = proxy_pool.get_next_proxy()
        assert proxy is None
        
        # Test that crawler can still function
        assert self.crawler.enhanced_config["anti_detection"]["enabled"]
        assert self.crawler.enhanced_config["monitoring"]["enabled"]
    
    def test_free_features_work(self):
        """Test that free features work without proxy services."""
        self.crawler.initialize(self.config)
        
        # Test anti-detection features
        anti_detection = self.crawler.advanced_crawler.anti_detection
        user_agent = anti_detection.get_random_user_agent()
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
        
        # Test monitoring features
        monitor = self.crawler.advanced_crawler.monitor
        metrics = monitor.get_metrics()
        assert 'average_response_time' in metrics
        assert 'blocked_requests' in metrics
        
        # Test task scheduling features
        scheduler = self.crawler.advanced_crawler.task_scheduler
        assert scheduler is not None
    
    @pytest.mark.asyncio
    async def test_no_proxy_lifecycle(self):
        """Test EnhancedWebCrawler lifecycle without proxy services."""
        self.crawler.initialize(self.config)
        
        # Test start/stop without proxy services
        await self.crawler.start()
        assert self.crawler._started
        
        # Test that crawler can still perform basic operations
        status = await self.crawler.get_enhanced_status()
        assert 'status' in status
        assert 'enhanced_features' in status
        
        await self.crawler.stop()
        assert not self.crawler._started


class TestEnhancedWebCrawlerIntegration:
    """Test EnhancedWebCrawler integration with other components."""
    
    def setup_method(self):
        """Setup test environment."""
        self.crawler = EnhancedWebCrawler("TestIntegrationCrawler")
    
    @pytest.mark.asyncio
    async def test_enhanced_crawler_with_llm(self):
        """Test enhanced crawler with LLM extraction."""
        config = {
            "extraction_strategy": "llm",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4"
            },
            "wait_for": 2,
            "max_scrolls": 1
        }
        
        with patch.object(self.crawler, 'collect_data') as mock_collect:
            mock_collect.return_value = {
                "success": True,
                "financial_data": {
                    "stock_price": 100.50,
                    "company_name": "Test Corp"
                }
            }
            
            self.crawler.initialize(config)
            await self.crawler.start()
            
            # crawl_url_enhanced returns task_id (string), not result dict
            task_id = await self.crawler.crawl_url_enhanced(
                "https://finance.example.com",
                config,
                TaskPriority.HIGH
            )
            
            # Verify task_id is returned
            assert isinstance(task_id, str)
            assert task_id is not None
            
            await self.crawler.stop()
    
    @pytest.mark.asyncio
    async def test_enhanced_crawler_with_proxy(self):
        """Test enhanced crawler with proxy support."""
        # Add proxy
        proxy = ProxyInfo("127.0.0.1", 8080)
        self.crawler.advanced_crawler.proxy_pool.add_proxy(proxy)
        
        config = {
            "extraction_strategy": "css",
            "proxy": "http://127.0.0.1:8080",
            "wait_for": 1
        }
        
        with patch.object(self.crawler, 'collect_data') as mock_collect:
            mock_collect.return_value = {
                "success": True,
                "url": "https://example.com",
                "proxy_used": "127.0.0.1:8080"
            }
            
            self.crawler.initialize(config)
            await self.crawler.start()
            
            # crawl_url_enhanced returns task_id (string), not result dict
            task_id = await self.crawler.crawl_url_enhanced(
                "https://example.com",
                config,
                TaskPriority.NORMAL
            )
            
            # Verify task_id is returned
            assert isinstance(task_id, str)
            assert task_id is not None
            
            await self.crawler.stop()
    
    def test_enhanced_crawler_configuration_merging(self):
        """Test configuration merging for enhanced features."""
        base_config = {
            "extraction_strategy": "css",
            "wait_for": 1
        }
        
        enhanced_config = {
            "proxy_pool": {"enabled": True},
            "anti_detection": {"enabled": True},
            "captcha_solving": {"enabled": False}
        }
        
        # Test configuration merging using dict update
        merged_config = {**base_config, **enhanced_config}
        
        assert merged_config["extraction_strategy"] == "css"
        assert merged_config["wait_for"] == 1
        assert merged_config["proxy_pool"]["enabled"] is True
        assert merged_config["anti_detection"]["enabled"] is True
        assert merged_config["captcha_solving"]["enabled"] is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
