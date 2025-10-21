"""
Web crawler implementation using crawl4ai.

This module provides advanced web crawling capabilities for financial data collection
using crawl4ai, which is specifically designed for AI applications and LLM integration.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
import re

from crawl4ai import AsyncWebCrawler, CrawlResult
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
from crawl4ai.chunking_strategy import RegexChunking
# Note: Some crawl4ai versions don't expose cache module; avoid hard dependency

from .volc_llm_config import create_volc_llm_strategy, get_volc_llm_config_from_env
from .data_classifier import DataClassifier
from src.financial_data_collector.core.events import EventBus, DataCollectedEvent
from ..interfaces import BaseDataCollector, WebCrawlerInterface

from ..storage import StorageManager, FinancialData, NewsData, CrawlTask, TaskStatus

logger = logging.getLogger(__name__)


class WebCrawler(BaseDataCollector, WebCrawlerInterface):
    """
    Advanced web crawler using crawl4ai for financial data collection.
    
    Features:
    - Async crawling with high performance
    - LLM-based content extraction
    - JavaScript rendering support
    - Smart content chunking
    - Built-in caching
    - Proxy support
    """
    
    def __init__(self, name: str = "WebCrawler"):
        super().__init__(name)
        self.supported_sources = ["web", "news", "financial_sites"]
        self.crawler: Optional[AsyncWebCrawler] = None
        self.event_bus: Optional[EventBus] = None
        self.config: Dict[str, Any] = {}
        
        # Storage configuration (默认启用)
        self.storage_manager: Optional[StorageManager] = None
        self.auto_store_data = True
        self.storage_config = {}
        self.data_classifier = DataClassifier()
        
        # Crawl4AI specific settings
        self.browser_config = {
            "browser_type": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        self.extraction_strategies = {
            "llm": LLMExtractionStrategy,
            "css": JsonCssExtractionStrategy
        }
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the web crawler with configuration."""
        # Mark as initialized via base class
        super().initialize(config)
        self.config = config
        
        # Browser configuration
        browser_config = config.get("browser", {})
        self.browser_config.update(browser_config)
        
        # Crawling settings
        self.max_concurrent_requests = config.get("max_concurrent_requests", 10)
        self.request_delay = config.get("request_delay", 1.0)
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        
        # Content extraction settings
        self.extraction_strategy = config.get("extraction_strategy", "llm")
        self.chunk_size = config.get("chunk_size", 1000)
        self.overlap_size = config.get("overlap_size", 200)
        
        # Financial data specific selectors
        self.financial_selectors = config.get("financial_selectors", {
            "price": [".price", ".quote-price", "[data-testid*='price']"],
            "volume": [".volume", ".quote-volume", "[data-testid*='volume']"],
            "change": [".change", ".quote-change", "[data-testid*='change']"],
            "market_cap": [".market-cap", ".market-value", "[data-testid*='market-cap']"],
            "news": [".news-item", ".article", ".story"],
            "financial_data": [".financial-data", ".market-data", ".quote-data"]
        })
        
        # Storage setup (默认启用，可禁用)
        self._setup_storage(config)
        
        logger.info(f"WebCrawler initialized with {self.extraction_strategy} extraction strategy")
    
    async def start(self) -> None:
        """Start the web crawler."""
        if not self._initialized:
            raise RuntimeError("WebCrawler not initialized")
        
        try:
            # Initialize crawl4ai crawler
            self.crawler = AsyncWebCrawler(
                browser_type=self.browser_config["browser_type"],
                headless=self.browser_config["headless"],
                viewport=self.browser_config["viewport"],
                user_agent=self.browser_config["user_agent"]
            )
            
            # Start the crawler
            await self.crawler.start()
            
            # Start storage manager if configured
            if self.storage_manager:
                try:
                    await self.storage_manager.initialize(self.storage_config)
                    await self.storage_manager.start()
                    logger.info("Storage manager started successfully")
                except Exception as e:
                    logger.error(f"Failed to start storage manager: {e}")
                    self.storage_manager = None
                    self.auto_store_data = False
            
            self._started = True
            logger.info("WebCrawler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start WebCrawler: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the web crawler."""
        if self.crawler:
            await self.crawler.close()
            self.crawler = None
        
        # Stop storage manager if configured
        if self.storage_manager:
            try:
                await self.storage_manager.stop()
                logger.info("Storage manager stopped")
            except Exception as e:
                logger.error(f"Error stopping storage manager: {e}")
        
        self._started = False
        logger.info("WebCrawler stopped")
    
    def get_supported_sources(self) -> List[str]:
        """Get supported data source types."""
        return self.supported_sources
    
    async def collect_data(self, source: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data from a web source."""
        if not self.crawler:
            raise RuntimeError("WebCrawler not started")
        
        url = config.get("url")
        if not url:
            raise ValueError("URL is required for web crawling")
        
        # Extract crawling parameters
        extraction_strategy = config.get("extraction_strategy", self.extraction_strategy)
        wait_for = config.get("wait_for", 2)
        max_scrolls = config.get("max_scrolls", 0)
        word_count_threshold = config.get("word_count_threshold", 10)
        
        try:
            # Prepare extraction strategy
            strategy = self._prepare_extraction_strategy(extraction_strategy, config)
            
            # Optional per-request options propagated to crawl4ai
            arun_kwargs: Dict[str, Any] = {}
            if "headers" in config:
                arun_kwargs["headers"] = config["headers"]
            if "proxy" in config:
                arun_kwargs["proxy"] = config["proxy"]
            if "proxy_auth" in config:
                arun_kwargs["proxy_auth"] = config["proxy_auth"]
            if "cookies" in config:
                arun_kwargs["cookies"] = config["cookies"]
            if "screenshot" in config:
                arun_kwargs["screenshot"] = config["screenshot"]
            if "screenshot_path" in config:
                arun_kwargs["screenshot_path"] = config["screenshot_path"]

            # Crawl the URL
            result = await self.crawler.arun(
                url=url,
                extraction_strategy=strategy,
                wait_for=wait_for,
                max_scrolls=max_scrolls,
                word_count_threshold=word_count_threshold,
                timeout=self.timeout,
                **arun_kwargs
            )
            
            # Process the result
            processed_data = await self._process_crawl_result(result, config)
            
            # Store data if auto-store is enabled
            if self.auto_store_data and self.storage_manager and processed_data.get("success"):
                await self._store_crawled_data(url, processed_data, config)
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish_async(
                    DataCollectedEvent(
                        data=processed_data,
                        source=f"web_crawler:{url}",
                        metadata={"url": url, "extraction_strategy": extraction_strategy}
                    )
                )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            raise
    
    async def crawl_url(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl a specific URL."""
        return await self.collect_data("web", {"url": url, **config})
    
    async def crawl_multiple_urls(self, urls: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawl multiple URLs concurrently."""
        if not self.crawler:
            raise RuntimeError("WebCrawler not started")
        
        # Limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def crawl_single_url(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.crawl_url(url, config)
                except Exception as e:
                    logger.error(f"Failed to crawl {url}: {e}")
                    return {"url": url, "error": str(e), "success": False}
        
        # Execute crawls concurrently
        tasks = [crawl_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for result in results:
            if isinstance(result, dict) and result.get("success", True):
                successful_results.append(result)
        
        logger.info(f"Crawled {len(successful_results)}/{len(urls)} URLs successfully")
        return successful_results
    
    def get_crawl_delay(self) -> float:
        """Get delay between requests."""
        return self.request_delay
    
    def validate_source(self, source: str) -> bool:
        """Validate if a source is supported."""
        return source in self.supported_sources
    
    def _prepare_extraction_strategy(self, strategy_name: str, config: Dict[str, Any]):
        """Prepare extraction strategy based on configuration."""
        if strategy_name == "llm":
            # LLM-based extraction for financial content
            llm_config = config.get("llm_config", {})
            # Fallback: load from environment if not provided explicitly
            if not llm_config:
                volc_env = get_volc_llm_config_from_env()
                if volc_env:
                    llm_config = {
                        "provider": "volc",
                        "api_token": volc_env.api_key,
                        "base_url": volc_env.base_url,
                        "model": volc_env.model,
                    }
            provider = llm_config.get("provider", "openai")
            
            # Check if using Volcano Engine API
            if provider == "volc" or llm_config.get("base_url"):
                return create_volc_llm_strategy(
                    api_key=llm_config.get("api_token") or llm_config.get("api_key"),
                    base_url=llm_config.get("base_url"),
                    model=llm_config.get("model", "ep-20250725215501-7zrfm"),
                    instruction=self._get_financial_extraction_instruction(),
                    schema=self._get_financial_data_schema()
                )
            else:
                # Standard OpenAI/Anthropic configuration using new LLMConfig format
                from crawl4ai import LLMConfig
                model_name = llm_config.get("model", "gpt-4")
                llm_config_obj = LLMConfig(
                    provider=f"{provider}/{model_name}",
                    api_token=llm_config.get("api_token"),
                    base_url=llm_config.get("base_url")
                )
                return LLMExtractionStrategy(
                    llm_config=llm_config_obj,
                    instruction=self._get_financial_extraction_instruction(),
                    schema=self._get_financial_data_schema()
                )
        
        elif strategy_name == "css":
            # CSS-based extraction
            css_selectors = config.get("css_selectors", self.financial_selectors)
            return JsonCssExtractionStrategy(
                css_selectors=css_selectors,
                schema=self._get_financial_data_schema()
            )
        
        else:
            # Default to CSS extraction
            return JsonCssExtractionStrategy(
                css_selectors=self.financial_selectors,
                schema=self._get_financial_data_schema()
            )
    
    def _get_financial_extraction_instruction(self) -> str:
        """Get LLM instruction for financial data extraction."""
        return """
        Extract financial data from the webpage. Focus on:
        1. Stock prices, volume, and market data
        2. Company information and financial metrics
        3. News articles and financial reports
        4. Market trends and analysis
        
        Return structured data with clear categorization of financial information.
        """
    
    def _get_financial_data_schema(self) -> Dict[str, Any]:
        """Get schema for financial data extraction."""
        return {
            "type": "object",
            "properties": {
                "stock_data": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "price": {"type": "number"},
                        "volume": {"type": "number"},
                        "change": {"type": "number"},
                        "change_percent": {"type": "number"},
                        "market_cap": {"type": "number"}
                    }
                },
                "news": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "url": {"type": "string"}
                        }
                    }
                },
                "company_info": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "sector": {"type": "string"},
                        "industry": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
        }
    
    async def _process_crawl_result(self, result: CrawlResult, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process crawl result and extract relevant data (version-tolerant)."""
        # Version-tolerant attribute access
        get = lambda obj, name, default=None: getattr(obj, name, default)
        url_value = get(result, "url", config.get("url"))
        title_value = get(result, "title", "")
        markdown_value = get(result, "markdown", None) or get(result, "md", "")
        html_value = get(result, "html", "")
        text_value = get(result, "cleaned_html", None) or get(result, "text", "")
        word_count_value = get(result, "word_count", 0)
        links_value = get(result, "links", []) or []
        images_value = get(result, "images", []) or []

        processed_data = {
            "url": url_value,
            "title": title_value,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "content": {
                "markdown": markdown_value,
                "html": html_value,
                "text": text_value,
            },
            "metadata": {
                "word_count": word_count_value if isinstance(word_count_value, int) else 0,
                "links_count": len(links_value) if isinstance(links_value, (list, tuple)) else 0,
                "images_count": len(images_value) if isinstance(images_value, (list, tuple)) else 0,
                "extraction_strategy": config.get("extraction_strategy", self.extraction_strategy),
            },
        }
        
        # Extract financial data if available
        if hasattr(result, 'extracted_content') and result.extracted_content:
            try:
                extracted_data = json.loads(result.extracted_content)
                processed_data["financial_data"] = extracted_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse extracted content as JSON")
        
        # Extract links for further crawling
        if isinstance(links_value, (list, tuple)) and links_value:
            safe_links = []
            for link in links_value[:10]:
                link_url = getattr(link, "url", None) or (link if isinstance(link, str) else None)
                link_text = getattr(link, "link_text", "")
                if link_url:
                    safe_links.append({
                        "url": link_url,
                        "text": link_text,
                        "is_internal": self._is_internal_link(link_url, url_value or ""),
                    })
            if safe_links:
                processed_data["links"] = safe_links
        
        # Extract financial keywords
        processed_data["keywords"] = self._extract_financial_keywords(text_value or "")
        
        return processed_data
    
    def _is_internal_link(self, link_url: str, base_url: str) -> bool:
        """Check if a link is internal to the same domain."""
        try:
            link_domain = urlparse(link_url).netloc
            base_domain = urlparse(base_url).netloc
            return link_domain == base_domain
        except:
            return False
    
    def _extract_financial_keywords(self, text: str) -> List[str]:
        """Extract financial keywords from text."""
        financial_keywords = [
            "stock", "share", "price", "volume", "market", "trading", "investment",
            "portfolio", "dividend", "earnings", "revenue", "profit", "loss",
            "bull", "bear", "rally", "crash", "volatility", "liquidity"
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in financial_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self.crawler:
            return {
                "status": "unhealthy",
                "message": "Crawler not initialized",
                "details": {"crawler_initialized": False}
            }
        
        try:
            # Test crawler with a simple URL
            test_url = "https://httpbin.org/get"
            result = await self.crawler.arun(url=test_url, wait_for=1)
            
            return {
                "status": "healthy",
                "message": "WebCrawler is working",
                "details": {
                    "crawler_initialized": True,
                    "test_url_successful": True,
                    "browser_type": self.browser_config["browser_type"],
                    "headless": self.browser_config["headless"]
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "details": {
                    "crawler_initialized": True,
                    "test_url_successful": False,
                    "error": str(e)
                }
            }
    
    def _setup_storage(self, config: Dict[str, Any]) -> None:
        """Setup storage manager based on configuration."""
        storage_config = config.get("storage", {})
        
        # Default to enabled if not explicitly disabled
        if storage_config.get("enabled", True):
            try:
                self.storage_manager = StorageManager(name=f"{self.name}Storage", config=storage_config)
                self.storage_config = storage_config
                self.auto_store_data = storage_config.get("auto_store", True)
                
                # Set storage strategy if available
                strategy = storage_config.get("strategy", "primary_only")
                if hasattr(self.storage_manager, 'set_storage_strategy'):
                    from ..storage import StorageStrategy
                    strategy_map = {
                        "primary_only": StorageStrategy.PRIMARY_ONLY,
                        "replica": StorageStrategy.REPLICA,
                        "shard": StorageStrategy.SHARD,
                        "failover": StorageStrategy.FAILOVER
                    }
                    self.storage_manager.set_storage_strategy(strategy_map.get(strategy, StorageStrategy.PRIMARY_ONLY))
                
                logger.info(f"Storage manager configured with strategy: {strategy}")
            except Exception as e:
                logger.error(f"Failed to setup storage manager: {e}")
                self.storage_manager = None
                self.auto_store_data = False
        else:
            self.auto_store_data = False
            logger.info("Storage integration disabled")
    
    async def _store_crawled_data(self, url: str, result: Dict[str, Any], config: Dict[str, Any]) -> None:
        """Store crawled data using storage manager."""
        try:
            if not self.storage_manager:
                return
            
            # Extract data from result
            data = result.get("data", {})
            if not data:
                logger.warning(f"No data to store for URL: {url}")
                return
            
            # Determine data type and create appropriate model
            data_type = self.data_classifier.determine_data_type(url, data)
            
            if data_type == "financial":
                await self._store_financial_data(url, data, config)
            elif data_type == "news":
                await self._store_news_data(url, data, config)
            else:
                # Store as generic crawl task
                await self._store_crawl_task(url, result, config)
            
            logger.info(f"Data stored successfully for URL: {url}")
            
        except Exception as e:
            logger.error(f"Failed to store data for URL {url}: {e}")
    
    async def _store_financial_data(self, url: str, data: Dict[str, Any], config: Dict[str, Any]) -> None:
        """Store financial data."""
        try:
            # Extract financial data fields using classifier
            financial_fields = self.data_classifier.extract_financial_data_fields(data, url)
            
            financial_data = FinancialData(
                symbol=financial_fields["symbol"],
                data_type="stock",
                price=financial_fields["price"],
                open_price=financial_fields["open_price"],
                high_price=financial_fields["high_price"],
                low_price=financial_fields["low_price"],
                close_price=financial_fields["close_price"],
                volume=financial_fields["volume"],
                change=financial_fields["change"],
                change_percent=financial_fields["change_percent"],
                market_cap=financial_fields["market_cap"],
                source=config.get("source", "web_crawler"),
                metadata={
                    "url": url,
                    "crawled_at": datetime.now().isoformat(),
                    "config": config
                }
            )
            
            await self.storage_manager.store_financial_data(financial_data)
            
        except Exception as e:
            logger.error(f"Failed to store financial data for {url}: {e}")
    
    async def _store_news_data(self, url: str, data: Dict[str, Any], config: Dict[str, Any]) -> None:
        """Store news data."""
        try:
            # Extract news data fields using classifier
            news_fields = self.data_classifier.extract_news_data_fields(data, url)
            
            news_data = NewsData(
                title=news_fields["title"],
                content=news_fields["content"],
                url=url,
                symbols=news_fields["symbols"],
                sentiment=news_fields["sentiment"],
                category=news_fields["category"],
                source=config.get("source", "web_crawler"),
                author=news_fields["author"],
                published_at=news_fields["published_at"],
                metadata={
                    "crawled_at": datetime.now().isoformat(),
                    "config": config
                }
            )
            
            await self.storage_manager.store_news_data(news_data)
            
        except Exception as e:
            logger.error(f"Failed to store news data for {url}: {e}")
    
    async def _store_crawl_task(self, url: str, result: Dict[str, Any], config: Dict[str, Any]) -> None:
        """Store crawl task information."""
        try:
            task = CrawlTask(
                task_id=f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(url) % 10000}",
                url=url,
                status=TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED,
                crawler_type="web",
                priority=2,  # Normal priority
                config=config,
                result=result,
                error=result.get("error")
            )
            
            await self.storage_manager.store_crawl_task(task)
            
        except Exception as e:
            logger.error(f"Failed to store crawl task for {url}: {e}")
