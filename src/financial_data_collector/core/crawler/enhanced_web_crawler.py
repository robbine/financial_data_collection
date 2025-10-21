"""
Enhanced Web Crawler with advanced features.

This module extends the basic WebCrawler with advanced features:
- Proxy IP pool management
- Captcha solving
- Anti-detection mechanisms
- Task scheduling and priority
- Incremental crawling
- Advanced monitoring
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta

from .web_crawler import WebCrawler
from .advanced_features import (
    AdvancedCrawler, ProxyInfo, CrawlTask, TaskPriority, TaskStatus,
    ProxyPool, CaptchaSolver, AntiDetectionManager, TaskScheduler,
    IncrementalCrawler, CrawlMonitor
)
from ..events import EventBus, DataCollectedEvent

logger = logging.getLogger(__name__)


class EnhancedWebCrawler(WebCrawler):
    """
    Enhanced web crawler with advanced features.
    
    Features:
    - Proxy IP pool management
    - Captcha solving integration
    - Anti-detection mechanisms
    - Task scheduling and priority
    - Incremental crawling
    - Advanced monitoring and alerting
    - Distributed crawling support
    """
    
    def __init__(self, name: str = "EnhancedWebCrawler"):
        super().__init__(name)
        self.advanced_crawler = AdvancedCrawler()
        self.proxy_rotation = True
        self.captcha_detection = True
        self.anti_detection = True
        self.incremental_mode = False
        self.monitoring_enabled = True
        
        # Enhanced configuration
        self.enhanced_config = {
            "proxy_pool": {
                "enabled": True,
                "rotation_interval": 10,  # requests
                "health_check_interval": 300  # seconds
            },
            "captcha_solving": {
                "enabled": True,
                "service": "2captcha",
                "api_key": None,
                "timeout": 300  # seconds
            },
            "anti_detection": {
                "enabled": True,
                "user_agent_rotation": True,
                "viewport_rotation": True,
                "random_delays": True,
                "min_delay": 1.0,
                "max_delay": 3.0
            },
            "task_scheduling": {
                "max_concurrent": 5,
                "priority_queuing": True,
                "retry_failed": True,
                "max_retries": 3
            },
            "incremental_crawling": {
                "enabled": False,
                "min_interval": 3600,  # seconds
                "content_hash_check": True
            },
            "monitoring": {
                "enabled": True,
                "alert_thresholds": {
                    "success_rate": 0.5,
                    "response_time": 30.0,
                    "block_rate": 0.1
                }
            }
        }
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the enhanced web crawler."""
        super().initialize(config)
        
        # Enhanced configuration
        enhanced_config = config.get("enhanced", {})
        self.enhanced_config.update(enhanced_config)
        
        # Setup advanced features
        self._setup_proxy_pool(config)
        self._setup_captcha_solving(config)
        self._setup_anti_detection(config)
        self._setup_task_scheduling(config)
        self._setup_incremental_crawling(config)
        self._setup_monitoring(config)
        
        logger.info("Enhanced WebCrawler initialized with advanced features")
    
    def _setup_proxy_pool(self, config: Dict[str, Any]) -> None:
        """Setup proxy pool management."""
        proxy_config = self.enhanced_config["proxy_pool"]
        
        if proxy_config["enabled"]:
            # Add proxies from configuration
            proxies = config.get("proxies", [])
            for proxy_info in proxies:
                proxy = ProxyInfo(
                    host=proxy_info["host"],
                    port=proxy_info["port"],
                    username=proxy_info.get("username"),
                    password=proxy_info.get("password"),
                    protocol=proxy_info.get("protocol", "http")
                )
                self.advanced_crawler.add_proxy(proxy.host, proxy.port, proxy.username, proxy.password)
            
            logger.info(f"Proxy pool configured with {len(proxies)} proxies")
    
    def _setup_captcha_solving(self, config: Dict[str, Any]) -> None:
        """Setup captcha solving."""
        captcha_config = self.enhanced_config["captcha_solving"]
        
        if captcha_config["enabled"]:
            api_key = captcha_config.get("api_key") or config.get("captcha_api_key")
            if api_key:
                self.advanced_crawler.setup_captcha_solver(
                    api_key, 
                    captcha_config.get("service", "2captcha")
                )
                logger.info("Captcha solving configured")
            else:
                logger.warning("Captcha solving enabled but no API key provided")
    
    def _setup_anti_detection(self, config: Dict[str, Any]) -> None:
        """Setup anti-detection mechanisms."""
        anti_detection_config = self.enhanced_config["anti_detection"]
        
        if anti_detection_config["enabled"]:
            # Configure anti-detection settings
            self.anti_detection = True
            logger.info("Anti-detection mechanisms configured")
    
    def _setup_task_scheduling(self, config: Dict[str, Any]) -> None:
        """Setup task scheduling."""
        task_config = self.enhanced_config["task_scheduling"]
        
        # Configure task scheduler
        self.advanced_crawler.task_scheduler.max_concurrent = task_config["max_concurrent"]
        logger.info(f"Task scheduling configured: max_concurrent={task_config['max_concurrent']}")
    
    def _setup_incremental_crawling(self, config: Dict[str, Any]) -> None:
        """Setup incremental crawling."""
        incremental_config = self.enhanced_config["incremental_crawling"]
        
        if incremental_config["enabled"]:
            # Setup incremental crawling with storage backend
            storage_backend = config.get("storage_backend")
            if storage_backend:
                self.advanced_crawler.setup_incremental_crawling(storage_backend)
                self.incremental_mode = True
                logger.info("Incremental crawling configured")
            else:
                logger.warning("Incremental crawling enabled but no storage backend provided")
    
    def _setup_monitoring(self, config: Dict[str, Any]) -> None:
        """Setup monitoring and alerting."""
        monitoring_config = self.enhanced_config["monitoring"]
        
        if monitoring_config["enabled"]:
            self.monitoring_enabled = True
            logger.info("Advanced monitoring configured")
    
    
    async def start(self) -> None:
        """Start the enhanced web crawler."""
        await super().start()
        
        # Start advanced features
        if self.enhanced_config["proxy_pool"]["enabled"]:
            await self._start_proxy_health_check()
        
        if self.enhanced_config["monitoring"]["enabled"]:
            await self._start_monitoring()
        
        logger.info("Enhanced WebCrawler started with all features")
    
    async def stop(self) -> None:
        """Stop the enhanced web crawler."""
        await super().stop()
        
        # Stop advanced features
        if hasattr(self, '_proxy_health_task'):
            self._proxy_health_task.cancel()
        
        if hasattr(self, '_monitoring_task'):
            self._monitoring_task.cancel()
        
        logger.info("Enhanced WebCrawler stopped")
    
    async def crawl_url_enhanced(self, url: str, config: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Crawl a URL with enhanced features."""
        # Add task to scheduler
        task_id = self.advanced_crawler.add_task(url, config, priority)
        
        # Execute immediately if not using task scheduler
        if not self.enhanced_config["task_scheduling"]["priority_queuing"]:
            await self._execute_enhanced_crawl(url, config)
        
        return task_id
    
    async def _execute_enhanced_crawl(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute enhanced crawling with all features."""
        start_time = datetime.now()
        
        try:
            # Apply anti-detection measures
            if self.anti_detection:
                config = self._apply_anti_detection(url, config)
            
            # Get proxy if enabled
            if self.enhanced_config["proxy_pool"]["enabled"]:
                proxy = self.advanced_crawler.proxy_pool.get_next_proxy()
                if proxy:
                    config["proxy"] = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
                    if proxy.username:
                        config["proxy_auth"] = f"{proxy.username}:{proxy.password}"
            
            # Check for incremental crawling
            if self.incremental_mode:
                if not self.advanced_crawler.incremental_crawler.should_crawl(url):
                    return {"skipped": True, "reason": "incremental_crawling"}
            
            # Execute base crawling
            result = await self.crawl_url(url, config)
            
            # Handle captcha if detected
            if self.captcha_detection and self._detect_captcha(result):
                captcha_solution = await self._solve_captcha(result)
                if captcha_solution:
                    # Retry with captcha solution
                    config["captcha_solution"] = captcha_solution
                    result = await self.crawl_url(url, config)
            
            
            # Update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self.advanced_crawler.monitor.record_request(True, response_time)
            
            # Update proxy stats
            if self.enhanced_config["proxy_pool"]["enabled"] and proxy:
                self.advanced_crawler.proxy_pool.update_proxy_stats(proxy, True, response_time)
            
            # Mark as crawled for incremental mode
            if self.incremental_mode:
                self.advanced_crawler.incremental_crawler.mark_crawled(url)
            
            return result
            
        except Exception as e:
            # Update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self.advanced_crawler.monitor.record_request(False, response_time)
            
            # Update proxy stats
            if self.enhanced_config["proxy_pool"]["enabled"] and 'proxy' in locals():
                self.advanced_crawler.proxy_pool.update_proxy_stats(proxy, False, response_time)
            
            logger.error(f"Enhanced crawl failed for {url}: {e}")
            raise
    
    def _apply_anti_detection(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply anti-detection measures."""
        anti_detection_config = self.enhanced_config["anti_detection"]
        
        # Random user agent
        if anti_detection_config["user_agent_rotation"]:
            config["user_agent"] = self.advanced_crawler.anti_detection.get_random_user_agent()
        
        # Random viewport
        if anti_detection_config["viewport_rotation"]:
            config["viewport"] = self.advanced_crawler.anti_detection.get_random_viewport()
        
        # Random headers
        config["headers"] = self.advanced_crawler.anti_detection.get_random_headers()
        
        # Random delay
        if anti_detection_config["random_delays"]:
            delay = self.advanced_crawler.anti_detection.add_random_delay(
                anti_detection_config["min_delay"],
                anti_detection_config["max_delay"]
            )
            config["delay"] = delay
        
        return config
    
    def _detect_captcha(self, result: Dict[str, Any]) -> bool:
        """Detect if captcha is present in the result."""
        if not self.captcha_detection:
            return False
        
        # Check for common captcha indicators
        content = result.get("content", {}).get("text", "")
        captcha_indicators = [
            "captcha", "recaptcha", "hcaptcha", "verify you are human",
            "security check", "robot verification"
        ]
        
        return any(indicator in content.lower() for indicator in captcha_indicators)
    
    async def _solve_captcha(self, result: Dict[str, Any]) -> Optional[str]:
        """Solve captcha if present."""
        if not self.advanced_crawler.captcha_solver:
            return None
        
        # Extract captcha data from result
        captcha_data = {
            "type": "recaptcha",  # Default type
            "site_key": self._extract_site_key(result),
            "page_url": result.get("url")
        }
        
        return await self.advanced_crawler.captcha_solver.solve_captcha(captcha_data)
    
    def _extract_site_key(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract reCAPTCHA site key from result."""
        # This would need to be implemented based on the specific captcha type
        # For now, return None as placeholder
        return None
    
    async def _start_proxy_health_check(self) -> None:
        """Start proxy health checking."""
        async def health_check_loop():
            while True:
                try:
                    await asyncio.sleep(self.enhanced_config["proxy_pool"]["health_check_interval"])
                    await self._check_proxy_health()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Proxy health check failed: {e}")
        
        self._proxy_health_task = asyncio.create_task(health_check_loop())
    
    async def _check_proxy_health(self) -> None:
        """Check health of all proxies."""
        for proxy in self.advanced_crawler.proxy_pool.proxies:
            if proxy.is_active:
                try:
                    # Test proxy with a simple request
                    test_url = "https://httpbin.org/ip"
                    # This would need actual implementation
                    # For now, just log the check
                    logger.debug(f"Health checking proxy: {proxy.host}:{proxy.port}")
                except Exception as e:
                    logger.warning(f"Proxy {proxy.host}:{proxy.port} health check failed: {e}")
                    self.advanced_crawler.proxy_pool.blacklist_proxy(proxy)
    
    async def _start_monitoring(self) -> None:
        """Start monitoring and alerting."""
        async def monitoring_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute
                    self._check_alerts()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Monitoring failed: {e}")
        
        self._monitoring_task = asyncio.create_task(monitoring_loop())
    
    def _check_alerts(self) -> None:
        """Check for alert conditions."""
        metrics = self.advanced_crawler.monitor.get_metrics()
        thresholds = self.enhanced_config["monitoring"]["alert_thresholds"]
        
        # Check success rate
        if metrics["success_rate"] < thresholds["success_rate"]:
            logger.warning(f"Low success rate: {metrics['success_rate']:.2%}")
        
        # Check response time
        if metrics["average_response_time"] > thresholds["response_time"]:
            logger.warning(f"High response time: {metrics['average_response_time']:.2f}s")
        
        # Check block rate
        block_rate = metrics["blocked_requests"] / max(metrics["total_requests"], 1)
        if block_rate > thresholds["block_rate"]:
            logger.warning(f"High block rate: {block_rate:.2%}")
    
    async def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced crawler status (aggregates crawl4ai health and advanced stats)."""
        base_status = await self.health_check()
        enhanced_status = self.advanced_crawler.get_status()
        
        return {
            **base_status,
            "enhanced_features": {
                "proxy_pool": {
                    "enabled": self.enhanced_config["proxy_pool"]["enabled"],
                    "proxy_count": enhanced_status["proxy_count"],
                    "active_proxies": enhanced_status["active_proxies"]
                },
                "captcha_solving": {
                    "enabled": self.enhanced_config["captcha_solving"]["enabled"],
                    "service": self.enhanced_config["captcha_solving"]["service"]
                },
                "anti_detection": {
                    "enabled": self.enhanced_config["anti_detection"]["enabled"]
                },
                "task_scheduling": {
                    "enabled": self.enhanced_config["task_scheduling"]["priority_queuing"],
                    "active_tasks": enhanced_status["active_tasks"],
                    "queued_tasks": enhanced_status["queued_tasks"]
                },
                "incremental_crawling": {
                    "enabled": self.enhanced_config["incremental_crawling"]["enabled"]
                },
                "monitoring": {
                    "enabled": self.enhanced_config["monitoring"]["enabled"],
                    "metrics": enhanced_status["metrics"]
                }
            }
        }
    
    async def crawl_multiple_urls_enhanced(self, urls: List[str], config: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL) -> List[Dict[str, Any]]:
        """Crawl multiple URLs with enhanced features."""
        if self.enhanced_config["task_scheduling"]["priority_queuing"]:
            # Add all tasks to scheduler
            task_ids = []
            for url in urls:
                task_id = self.advanced_crawler.add_task(url, config, priority)
                task_ids.append(task_id)
            
            # Execute tasks
            await self.advanced_crawler.start_crawling()
            
            # Collect results
            results = []
            for task_id in task_ids:
                task = self.advanced_crawler.task_scheduler.tasks.get(task_id)
                if task and task.result:
                    results.append(task.result)
            
            return results
        else:
            # Execute immediately
            results = []
            for url in urls:
                try:
                    result = await self._execute_enhanced_crawl(url, config)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to crawl {url}: {e}")
                    results.append({"url": url, "error": str(e), "success": False})
            
            return results
    
