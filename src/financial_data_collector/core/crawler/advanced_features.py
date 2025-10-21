"""
Advanced crawling features for Financial Data Collector.

This module implements additional features not provided by Crawl4AI:
- Proxy IP pool management
- Captcha solving integration
- Anti-detection mechanisms
- Task scheduling and priority
- Distributed crawling
- Incremental crawling
- Advanced monitoring
"""

import asyncio
import random
import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import requests
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class ProxyInfo:
    """Proxy server information."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    is_active: bool = True
    last_used: Optional[datetime] = None
    success_rate: float = 1.0
    response_time: float = 0.0


@dataclass
class CrawlTask:
    """Crawl task definition."""
    id: str
    url: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProxyPool:
    """Proxy IP pool management."""
    
    def __init__(self):
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.blacklisted: List[str] = []
    
    def add_proxy(self, proxy: ProxyInfo) -> None:
        """Add a proxy to the pool."""
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy.host}:{proxy.port}")
    
    def get_next_proxy(self) -> Optional[ProxyInfo]:
        """Get the next available proxy."""
        if not self.proxies:
            return None
        
        # Filter active proxies
        active_proxies = [p for p in self.proxies if p.is_active and p.host not in self.blacklisted]
        
        if not active_proxies:
            logger.warning("No active proxies available")
            return None
        
        # Select proxy based on success rate and response time
        best_proxy = max(active_proxies, key=lambda p: p.success_rate / (p.response_time + 1))
        
        # Update last used time
        best_proxy.last_used = datetime.now()
        
        return best_proxy
    
    def blacklist_proxy(self, proxy: ProxyInfo) -> None:
        """Blacklist a proxy due to failures."""
        self.blacklisted.append(proxy.host)
        proxy.is_active = False
        logger.warning(f"Blacklisted proxy: {proxy.host}:{proxy.port}")
    
    def update_proxy_stats(self, proxy: ProxyInfo, success: bool, response_time: float) -> None:
        """Update proxy statistics."""
        if success:
            proxy.success_rate = min(1.0, proxy.success_rate + 0.1)
        else:
            proxy.success_rate = max(0.0, proxy.success_rate - 0.2)
        
        proxy.response_time = response_time
        
        # Blacklist if success rate is too low
        if proxy.success_rate < 0.3:
            self.blacklist_proxy(proxy)


class CaptchaSolver:
    """Captcha solving integration."""
    
    def __init__(self, api_key: str, service: str = "2captcha"):
        self.api_key = api_key
        self.service = service
        self.supported_types = ["recaptcha", "hcaptcha", "image"]
    
    async def solve_captcha(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """Solve a captcha and return the solution."""
        try:
            if self.service == "2captcha":
                return await self._solve_2captcha(captcha_data)
            elif self.service == "anticaptcha":
                return await self._solve_anticaptcha(captcha_data)
            else:
                logger.error(f"Unsupported captcha service: {self.service}")
                return None
        except Exception as e:
            logger.error(f"Captcha solving failed: {e}")
            return None
    
    async def _solve_2captcha(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """Solve captcha using 2captcha service."""
        # Implementation for 2captcha API
        captcha_type = captcha_data.get("type", "recaptcha")
        
        if captcha_type == "recaptcha":
            # Submit captcha
            submit_data = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": captcha_data.get("site_key"),
                "pageurl": captcha_data.get("page_url")
            }
            
            response = requests.post("http://2captcha.com/in.php", data=submit_data)
            if response.text.startswith("OK|"):
                captcha_id = response.text.split("|")[1]
                
                # Wait for solution
                for _ in range(30):  # Wait up to 5 minutes
                    await asyncio.sleep(10)
                    
                    result_response = requests.get(
                        f"http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}"
                    )
                    
                    if result_response.text == "CAPCHA_NOT_READY":
                        continue
                    elif result_response.text.startswith("OK|"):
                        return result_response.text.split("|")[1]
                    else:
                        logger.error(f"2captcha error: {result_response.text}")
                        return None
        
        return None
    
    async def _solve_anticaptcha(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """Solve captcha using AntiCaptcha service."""
        # Implementation for AntiCaptcha API
        # Similar to 2captcha but with different API endpoints
        pass


class AntiDetectionManager:
    """Anti-detection mechanisms."""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        self.referers = [
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://www.yahoo.com/",
            "https://www.baidu.com/"
        ]
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864}
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent."""
        return random.choice(self.user_agents)
    
    def get_random_referer(self) -> str:
        """Get a random referer."""
        return random.choice(self.referers)
    
    def get_random_viewport(self) -> Dict[str, int]:
        """Get a random viewport."""
        return random.choice(self.viewports)
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers for anti-detection."""
        return {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def add_random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0) -> float:
        """Add random delay between requests."""
        delay = random.uniform(min_delay, max_delay)
        return delay


class TaskScheduler:
    """Task scheduling and priority management."""
    
    def __init__(self):
        self.tasks: Dict[str, CrawlTask] = {}
        self.task_queue: List[str] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent: int = 5
        self.rate_limiter: Dict[str, float] = {}
    
    def add_task(self, task: CrawlTask) -> None:
        """Add a task to the scheduler."""
        self.tasks[task.id] = task
        self._insert_task_by_priority(task.id)
        logger.info(f"Added task {task.id} with priority {task.priority.name}")
    
    def _insert_task_by_priority(self, task_id: str) -> None:
        """Insert task into queue based on priority."""
        task = self.tasks[task_id]
        
        # Find insertion point based on priority
        insert_index = 0
        for i, queued_task_id in enumerate(self.task_queue):
            queued_task = self.tasks[queued_task_id]
            if task.priority.value > queued_task.priority.value:
                insert_index = i
                break
            insert_index = i + 1
        
        self.task_queue.insert(insert_index, task_id)
    
    async def execute_tasks(self, crawler_func: Callable) -> None:
        """Execute tasks with concurrency control."""
        while self.task_queue or self.running_tasks:
            # Start new tasks if under concurrency limit
            while len(self.running_tasks) < self.max_concurrent and self.task_queue:
                task_id = self.task_queue.pop(0)
                task = self.tasks[task_id]
                
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now()
                    
                    # Create async task
                    async_task = asyncio.create_task(
                        self._execute_single_task(task, crawler_func)
                    )
                    self.running_tasks[task_id] = async_task
            
            # Wait for any task to complete
            if self.running_tasks:
                done, pending = await asyncio.wait(
                    self.running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    for task_id, running_task in self.running_tasks.items():
                        if running_task == task:
                            del self.running_tasks[task_id]
                            break
    
    async def _execute_single_task(self, task: CrawlTask, crawler_func: Callable) -> None:
        """Execute a single task."""
        try:
            # Apply rate limiting
            domain = urlparse(task.url).netloc
            if domain in self.rate_limiter:
                time_since_last = time.time() - self.rate_limiter[domain]
                if time_since_last < 1.0:  # 1 second between requests to same domain
                    await asyncio.sleep(1.0 - time_since_last)
            
            self.rate_limiter[domain] = time.time()
            
            # Execute crawling
            result = await crawler_func(task.url, task.config)
            
            # Update task
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                self._insert_task_by_priority(task.id)
                logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task.id} failed permanently: {e}")


class IncrementalCrawler:
    """Incremental crawling to avoid duplicates."""
    
    def __init__(self, storage_backend: Any):
        self.storage = storage_backend
        self.content_hashes: Dict[str, str] = {}
        self.last_crawl_times: Dict[str, datetime] = {}
    
    def get_content_hash(self, content: str) -> str:
        """Generate hash for content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_content_changed(self, url: str, content: str) -> bool:
        """Check if content has changed since last crawl."""
        current_hash = self.get_content_hash(content)
        stored_hash = self.content_hashes.get(url)
        
        if stored_hash != current_hash:
            self.content_hashes[url] = current_hash
            return True
        
        return False
    
    def should_crawl(self, url: str, min_interval: timedelta = timedelta(hours=1)) -> bool:
        """Check if URL should be crawled based on time interval."""
        last_crawl = self.last_crawl_times.get(url)
        
        if not last_crawl:
            return True
        
        return datetime.now() - last_crawl > min_interval
    
    def mark_crawled(self, url: str) -> None:
        """Mark URL as crawled."""
        self.last_crawl_times[url] = datetime.now()
    
    async def get_incremental_tasks(self, urls: List[str]) -> List[str]:
        """Get URLs that need incremental crawling."""
        tasks = []
        
        for url in urls:
            if self.should_crawl(url):
                tasks.append(url)
        
        return tasks


class CrawlMonitor:
    """Advanced monitoring and alerting."""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "blocked_requests": 0,
            "average_response_time": 0.0,
            "requests_per_minute": 0.0
        }
        self.alerts: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def record_request(self, success: bool, response_time: float, blocked: bool = False) -> None:
        """Record request metrics."""
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        elif blocked:
            self.metrics["blocked_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # Update average response time
        total_time = self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1)
        self.metrics["average_response_time"] = (total_time + response_time) / self.metrics["total_requests"]
        
        # Calculate requests per minute
        elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        self.metrics["requests_per_minute"] = self.metrics["total_requests"] / max(elapsed_minutes, 1)
        
        # Check for alerts
        self._check_alerts()
    
    def _check_alerts(self) -> None:
        """Check for alert conditions."""
        success_rate = self.metrics["successful_requests"] / max(self.metrics["total_requests"], 1)
        
        if success_rate < 0.5:
            self._trigger_alert("LOW_SUCCESS_RATE", f"Success rate is {success_rate:.2%}")
        
        if self.metrics["blocked_requests"] > 10:
            self._trigger_alert("HIGH_BLOCK_RATE", f"Blocked requests: {self.metrics['blocked_requests']}")
        
        if self.metrics["average_response_time"] > 30:
            self._trigger_alert("SLOW_RESPONSE", f"Average response time: {self.metrics['average_response_time']:.2f}s")
    
    def _trigger_alert(self, alert_type: str, message: str) -> None:
        """Trigger an alert."""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now(),
            "metrics": self.metrics.copy()
        }
        
        self.alerts.append(alert)
        logger.warning(f"ALERT [{alert_type}]: {message}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            **self.metrics,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "success_rate": self.metrics["successful_requests"] / max(self.metrics["total_requests"], 1),
            "recent_alerts": self.alerts[-10:]  # Last 10 alerts
        }


class AdvancedCrawler:
    """Advanced crawler with all enhanced features."""
    
    def __init__(self):
        self.proxy_pool = ProxyPool()
        self.captcha_solver = None
        self.anti_detection = AntiDetectionManager()
        self.task_scheduler = TaskScheduler()
        self.incremental_crawler = None
        self.monitor = CrawlMonitor()
        self.crawler_func: Optional[Callable] = None
    
    def setup_captcha_solver(self, api_key: str, service: str = "2captcha") -> None:
        """Setup captcha solving service."""
        self.captcha_solver = CaptchaSolver(api_key, service)
        logger.info(f"Captcha solver configured: {service}")
    
    def setup_incremental_crawling(self, storage_backend: Any) -> None:
        """Setup incremental crawling."""
        self.incremental_crawler = IncrementalCrawler(storage_backend)
        logger.info("Incremental crawling configured")
    
    def add_proxy(self, host: str, port: int, username: str = None, password: str = None) -> None:
        """Add a proxy to the pool."""
        proxy = ProxyInfo(host=host, port=port, username=username, password=password)
        self.proxy_pool.add_proxy(proxy)
    
    def add_task(self, url: str, config: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Add a crawling task."""
        task_id = hashlib.md5(f"{url}_{datetime.now()}".encode()).hexdigest()[:8]
        task = CrawlTask(id=task_id, url=url, config=config, priority=priority)
        self.task_scheduler.add_task(task)
        return task_id
    
    async def start_crawling(self) -> None:
        """Start the advanced crawling process."""
        if not self.crawler_func:
            raise ValueError("Crawler function not set")
        
        logger.info("Starting advanced crawling...")
        await self.task_scheduler.execute_tasks(self.crawler_func)
    
    def get_status(self) -> Dict[str, Any]:
        """Get crawler status."""
        return {
            "metrics": self.monitor.get_metrics(),
            "active_tasks": len(self.task_scheduler.running_tasks),
            "queued_tasks": len(self.task_scheduler.task_queue),
            "proxy_count": len(self.proxy_pool.proxies),
            "active_proxies": len([p for p in self.proxy_pool.proxies if p.is_active])
        }
