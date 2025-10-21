#!/usr/bin/env python3
"""
Enhanced Crawler Demo Script

This script demonstrates all advanced features of the Financial Data Collector
enhanced web crawler system.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from financial_data_collector.core.crawler.enhanced_web_crawler import EnhancedWebCrawler
from financial_data_collector.core.crawler.advanced_features import (
    TaskPriority, ProxyInfo, CrawlTask, TaskStatus
)
from financial_data_collector.core.events import EventBus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_enhanced_crawling():
    """Demonstrate basic enhanced crawling functionality."""
    print("\n=== Basic Enhanced Crawling Demo ===")
    
    # Create enhanced crawler
    crawler = EnhancedWebCrawler("DemoEnhancedCrawler")
    
    # Basic configuration
    config = {
        "browser": {
            "browser_type": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080}
        },
        "extraction_strategy": "llm",
        "request_delay": 1.0,
        "timeout": 30,
        "enhanced": {
            "proxy_pool": {"enabled": False},  # Disable for demo
            "captcha_solving": {"enabled": False},  # Disable for demo
            "anti_detection": {"enabled": True},
            "task_scheduling": {"enabled": False},  # Execute immediately
            "incremental_crawling": {"enabled": False},
            "monitoring": {"enabled": True}
        }
    }
    
    crawler.initialize(config)
    
    try:
        await crawler.start()
        print("✅ Enhanced crawler started successfully")
        
        # Demo: Basic enhanced crawling
        print("\n🕷️  Enhanced crawling demo...")
        result = await crawler.crawl_url_enhanced(
            "https://httpbin.org/get",
            {
                "extraction_strategy": "css",
                "wait_for": 2
            },
            priority=TaskPriority.NORMAL
        )
        
        print(f"📊 Enhanced crawl results:")
        print(f"  - URL: {result.get('url', 'N/A')}")
        print(f"  - Success: {result.get('success', False)}")
        print(f"  - Timestamp: {result.get('timestamp', 'N/A')}")
        
        # Demo: Anti-detection features
        print("\n🛡️  Anti-detection demo...")
        anti_detection_result = await crawler.crawl_url_enhanced(
            "https://httpbin.org/headers",
            {
                "extraction_strategy": "css",
                "wait_for": 2
            },
            priority=TaskPriority.HIGH
        )
        
        print(f"📊 Anti-detection results:")
        print(f"  - Headers extracted: {len(anti_detection_result.get('content', {}).get('text', ''))}")
        
        # Demo: Status monitoring
        print("\n📊 Status monitoring...")
        status = crawler.get_enhanced_status()
        print(f"  - Base status: {status['status']}")
        print(f"  - Enhanced features: {len(status.get('enhanced_features', {}))}")
        
    except Exception as e:
        print(f"❌ Error during enhanced crawling demo: {e}")
        logger.error(f"Enhanced crawling demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Enhanced crawler stopped")


async def demo_proxy_pool_management():
    """Demonstrate proxy pool management."""
    print("\n=== Proxy Pool Management Demo ===")
    
    # Create enhanced crawler with proxy pool
    crawler = EnhancedWebCrawler("ProxyDemoCrawler")
    
    config = {
        "browser": {"headless": True},
        "extraction_strategy": "css",
        "enhanced": {
            "proxy_pool": {
                "enabled": True,
                "proxies": [
                    {
                        "host": "proxy1.example.com",
                        "port": 8080,
                        "username": "user1",
                        "password": "pass1",
                        "protocol": "http"
                    },
                    {
                        "host": "proxy2.example.com",
                        "port": 8080,
                        "username": "user2",
                        "password": "pass2",
                        "protocol": "http"
                    }
                ]
            },
            "anti_detection": {"enabled": True},
            "monitoring": {"enabled": True}
        }
    }
    
    crawler.initialize(config)
    
    try:
        await crawler.start()
        print("✅ Proxy pool crawler started")
        
        # Demo: Proxy rotation
        print("\n🔄 Proxy rotation demo...")
        for i in range(3):
            result = await crawler.crawl_url_enhanced(
                "https://httpbin.org/ip",
                {"extraction_strategy": "css", "wait_for": 1},
                priority=TaskPriority.NORMAL
            )
            print(f"  Request {i+1}: {result.get('success', False)}")
        
        # Demo: Proxy health check
        print("\n🏥 Proxy health check...")
        status = crawler.get_enhanced_status()
        proxy_info = status.get('enhanced_features', {}).get('proxy_pool', {})
        print(f"  - Proxy count: {proxy_info.get('proxy_count', 0)}")
        print(f"  - Active proxies: {proxy_info.get('active_proxies', 0)}")
        
    except Exception as e:
        print(f"❌ Error during proxy pool demo: {e}")
        logger.error(f"Proxy pool demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Proxy pool crawler stopped")


async def demo_task_scheduling():
    """Demonstrate task scheduling and priority management."""
    print("\n=== Task Scheduling Demo ===")
    
    # Create enhanced crawler with task scheduling
    crawler = EnhancedWebCrawler("TaskSchedulerDemo")
    
    config = {
        "browser": {"headless": True},
        "extraction_strategy": "css",
        "enhanced": {
            "task_scheduling": {
                "enabled": True,
                "max_concurrent": 3,
                "priority_queuing": True,
                "retry_failed": True,
                "max_retries": 2
            },
            "monitoring": {"enabled": True}
        }
    }
    
    crawler.initialize(config)
    
    try:
        await crawler.start()
        print("✅ Task scheduler crawler started")
        
        # Demo: Add tasks with different priorities
        print("\n📋 Adding tasks with different priorities...")
        
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/2",
            "https://httpbin.org/delay/3",
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404"
        ]
        
        priorities = [
            TaskPriority.URGENT,
            TaskPriority.HIGH,
            TaskPriority.NORMAL,
            TaskPriority.LOW,
            TaskPriority.NORMAL
        ]
        
        task_ids = []
        for url, priority in zip(urls, priorities):
            task_id = await crawler.crawl_url_enhanced(
                url,
                {"extraction_strategy": "css", "wait_for": 1},
                priority=priority
            )
            task_ids.append(task_id)
            print(f"  Added task {task_id} with priority {priority.name}")
        
        # Demo: Task execution
        print("\n⚡ Executing tasks...")
        await asyncio.sleep(2)  # Let tasks execute
        
        # Demo: Task status monitoring
        print("\n📊 Task status monitoring...")
        status = crawler.get_enhanced_status()
        task_info = status.get('enhanced_features', {}).get('task_scheduling', {})
        print(f"  - Active tasks: {task_info.get('active_tasks', 0)}")
        print(f"  - Queued tasks: {task_info.get('queued_tasks', 0)}")
        
    except Exception as e:
        print(f"❌ Error during task scheduling demo: {e}")
        logger.error(f"Task scheduling demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Task scheduler crawler stopped")


async def demo_incremental_crawling():
    """Demonstrate incremental crawling functionality."""
    print("\n=== Incremental Crawling Demo ===")
    
    # Create enhanced crawler with incremental crawling
    crawler = EnhancedWebCrawler("IncrementalDemo")
    
    config = {
        "browser": {"headless": True},
        "extraction_strategy": "css",
        "enhanced": {
            "incremental_crawling": {
                "enabled": True,
                "min_interval": 5,  # 5 seconds for demo
                "content_hash_check": True
            },
            "monitoring": {"enabled": True}
        }
    }
    
    crawler.initialize(config)
    
    try:
        await crawler.start()
        print("✅ Incremental crawler started")
        
        # Demo: First crawl
        print("\n🔄 First crawl...")
        result1 = await crawler.crawl_url_enhanced(
            "https://httpbin.org/get",
            {"extraction_strategy": "css", "wait_for": 1},
            priority=TaskPriority.NORMAL
        )
        print(f"  First crawl: {result1.get('success', False)}")
        
        # Demo: Immediate second crawl (should be skipped)
        print("\n⏭️  Immediate second crawl (should be skipped)...")
        result2 = await crawler.crawl_url_enhanced(
            "https://httpbin.org/get",
            {"extraction_strategy": "css", "wait_for": 1},
            priority=TaskPriority.NORMAL
        )
        print(f"  Second crawl: {result2.get('skipped', False)}")
        
        # Demo: Wait and crawl again
        print("\n⏰ Waiting 6 seconds for next crawl...")
        await asyncio.sleep(6)
        
        result3 = await crawler.crawl_url_enhanced(
            "https://httpbin.org/get",
            {"extraction_strategy": "css", "wait_for": 1},
            priority=TaskPriority.NORMAL
        )
        print(f"  Third crawl: {result3.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Error during incremental crawling demo: {e}")
        logger.error(f"Incremental crawling demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Incremental crawler stopped")


async def demo_monitoring_and_alerting():
    """Demonstrate monitoring and alerting functionality."""
    print("\n=== Monitoring and Alerting Demo ===")
    
    # Create enhanced crawler with monitoring
    crawler = EnhancedWebCrawler("MonitoringDemo")
    
    config = {
        "browser": {"headless": True},
        "extraction_strategy": "css",
        "enhanced": {
            "monitoring": {
                "enabled": True,
                "alert_thresholds": {
                    "success_rate": 0.5,
                    "response_time": 10.0,
                    "block_rate": 0.1
                }
            }
        }
    }
    
    crawler.initialize(config)
    
    try:
        await crawler.start()
        print("✅ Monitoring crawler started")
        
        # Demo: Generate some traffic
        print("\n📊 Generating traffic for monitoring...")
        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404",  # This will fail
            "https://httpbin.org/delay/2",
            "https://httpbin.org/get"
        ]
        
        for i, url in enumerate(urls):
            try:
                result = await crawler.crawl_url_enhanced(
                    url,
                    {"extraction_strategy": "css", "wait_for": 1},
                    priority=TaskPriority.NORMAL
                )
                print(f"  Request {i+1}: {result.get('success', False)}")
            except Exception as e:
                print(f"  Request {i+1}: Failed - {e}")
        
        # Demo: Get monitoring metrics
        print("\n📈 Monitoring metrics...")
        status = crawler.get_enhanced_status()
        monitoring_info = status.get('enhanced_features', {}).get('monitoring', {})
        metrics = monitoring_info.get('metrics', {})
        
        print(f"  - Total requests: {metrics.get('total_requests', 0)}")
        print(f"  - Successful requests: {metrics.get('successful_requests', 0)}")
        print(f"  - Failed requests: {metrics.get('failed_requests', 0)}")
        print(f"  - Success rate: {metrics.get('success_rate', 0):.2%}")
        print(f"  - Average response time: {metrics.get('average_response_time', 0):.2f}s")
        print(f"  - Requests per minute: {metrics.get('requests_per_minute', 0):.2f}")
        
    except Exception as e:
        print(f"❌ Error during monitoring demo: {e}")
        logger.error(f"Monitoring demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Monitoring crawler stopped")


async def demo_financial_data_crawling():
    """Demonstrate financial data crawling with all features."""
    print("\n=== Financial Data Crawling Demo ===")
    
    # Create enhanced crawler for financial data
    crawler = EnhancedWebCrawler("FinancialDataDemo")
    
    config = {
        "browser": {
            "browser_type": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080}
        },
        "extraction_strategy": "llm",
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4",
            "api_token": "demo-key",  # Replace with real key
            "instruction": "Extract financial data from the webpage"
        },
        "enhanced": {
            "anti_detection": {
                "enabled": True,
                "user_agent_rotation": True,
                "random_delays": True,
                "min_delay": 2.0,
                "max_delay": 5.0
            },
            "task_scheduling": {
                "enabled": True,
                "max_concurrent": 2,
                "priority_queuing": True
            },
            "monitoring": {"enabled": True}
        }
    }
    
    crawler.initialize(config)
    
    try:
        await crawler.start()
        print("✅ Financial data crawler started")
        
        # Demo: Financial data crawling
        print("\n💰 Financial data crawling demo...")
        
        financial_urls = [
            "https://finance.yahoo.com/quote/AAPL",
            "https://finance.yahoo.com/quote/MSFT",
            "https://finance.yahoo.com/quote/GOOGL"
        ]
        
        results = await crawler.crawl_multiple_urls_enhanced(
            financial_urls,
            {
                "extraction_strategy": "css",
                "wait_for": 3,
                "css_selectors": {
                    "price": "[data-field='regularMarketPrice']",
                    "volume": "[data-field='regularMarketVolume']",
                    "change": "[data-field='regularMarketChange']"
                }
            },
            priority=TaskPriority.HIGH
        )
        
        print(f"📊 Financial data results:")
        for i, result in enumerate(results):
            if result.get('success', True):
                print(f"  Stock {i+1}: {result.get('title', 'N/A')}")
                if 'financial_data' in result:
                    print(f"    Financial data extracted: {len(result['financial_data'])} fields")
            else:
                print(f"  Stock {i+1}: Failed - {result.get('error', 'Unknown error')}")
        
        # Demo: Final status
        print("\n📊 Final status...")
        status = crawler.get_enhanced_status()
        print(f"  - Overall status: {status['status']}")
        print(f"  - Enhanced features: {len(status.get('enhanced_features', {}))}")
        
    except Exception as e:
        print(f"❌ Error during financial data crawling demo: {e}")
        logger.error(f"Financial data crawling demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Financial data crawler stopped")


async def main():
    """Run all enhanced crawler demos."""
    print("🚀 Enhanced Web Crawler Demo")
    print("=" * 50)
    
    try:
        # Check if enhanced crawler is available
        try:
            from financial_data_collector.core.crawler.enhanced_web_crawler import EnhancedWebCrawler
            print("✅ Enhanced Web Crawler available")
        except ImportError as e:
            print(f"❌ Enhanced Web Crawler not available: {e}")
            return
        
        # Run demos
        await demo_basic_enhanced_crawling()
        await demo_proxy_pool_management()
        await demo_task_scheduling()
        await demo_incremental_crawling()
        await demo_monitoring_and_alerting()
        await demo_financial_data_crawling()
        
        print("\n" + "=" * 50)
        print("🎉 All enhanced crawler demos completed successfully!")
        print("\n📚 Advanced features demonstrated:")
        print("  ✅ Enhanced web crawling")
        print("  ✅ Proxy pool management")
        print("  ✅ Task scheduling and priority")
        print("  ✅ Incremental crawling")
        print("  ✅ Monitoring and alerting")
        print("  ✅ Financial data crawling")
        print("\n🔧 Next steps:")
        print("  1. Configure real API keys in .env file")
        print("  2. Set up proxy servers for production use")
        print("  3. Configure monitoring and alerting")
        print("  4. Deploy with Docker: make dev")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
