#!/usr/bin/env python3
"""
Crawl4AI Demo Script for Financial Data Collection

This script demonstrates how to use crawl4ai for financial data collection
with the Financial Data Collector system.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from financial_data_collector.core.crawler.web_crawler import WebCrawler
from financial_data_collector.core.crawler.api_crawler import APICollector
from financial_data_collector.core.events import EventBus
from financial_data_collector.core.di import DIContainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_crawl4ai_web_crawler():
    """Demonstrate crawl4ai web crawler functionality."""
    print("\n=== Crawl4AI Web Crawler Demo ===")
    
    # Create event bus
    event_bus = EventBus()
    
    # Create web crawler
    crawler = WebCrawler("DemoWebCrawler")
    
    # Initialize with configuration
    config = {
        "browser": {
            "browser_type": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080}
        },
        "extraction_strategy": "llm",  # Use LLM-based extraction
        "max_concurrent_requests": 5,
        "request_delay": 1.0,
        "timeout": 30,
        "financial_selectors": {
            "price": [".price", ".quote-price", "[data-testid*='price']"],
            "volume": [".volume", ".quote-volume", "[data-testid*='volume']"],
            "news": [".news-item", ".article", ".story"]
        }
    }
    
    crawler.initialize(config)
    crawler.event_bus = event_bus
    
    try:
        # Start crawler
        await crawler.start()
        print("✅ Web crawler started successfully")
        
        # Demo 1: Crawl financial news
        print("\n📰 Crawling financial news...")
        news_result = await crawler.crawl_url(
            "https://finance.yahoo.com/news/",
            {
                "extraction_strategy": "llm",
                "wait_for": 3,
                "max_scrolls": 2,
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "instruction": "Extract financial news headlines and summaries"
                }
            }
        )
        
        print(f"📊 News crawl results:")
        print(f"  - Title: {news_result.get('title', 'N/A')}")
        print(f"  - Word count: {news_result.get('metadata', {}).get('word_count', 0)}")
        print(f"  - Links found: {news_result.get('metadata', {}).get('links_count', 0)}")
        print(f"  - Keywords: {', '.join(news_result.get('keywords', [])[:5])}")
        
        # Demo 2: Crawl stock data
        print("\n📈 Crawling stock data...")
        stock_result = await crawler.crawl_url(
            "https://finance.yahoo.com/quote/AAPL",
            {
                "extraction_strategy": "css",
                "wait_for": 2,
                "css_selectors": {
                    "price": "[data-field='regularMarketPrice']",
                    "volume": "[data-field='regularMarketVolume']",
                    "change": "[data-field='regularMarketChange']",
                    "market_cap": "[data-field='marketCap']"
                }
            }
        )
        
        print(f"📊 Stock crawl results:")
        print(f"  - Title: {stock_result.get('title', 'N/A')}")
        if 'financial_data' in stock_result:
            financial_data = stock_result['financial_data']
            print(f"  - Stock data extracted: {len(financial_data)} fields")
        
        # Demo 3: Multiple URLs crawling
        print("\n🔄 Crawling multiple URLs...")
        urls = [
            "https://finance.yahoo.com/quote/MSFT",
            "https://finance.yahoo.com/quote/GOOGL",
            "https://finance.yahoo.com/quote/TSLA"
        ]
        
        multiple_results = await crawler.crawl_multiple_urls(
            urls,
            {
                "extraction_strategy": "css",
                "wait_for": 2,
                "css_selectors": {
                    "price": "[data-field='regularMarketPrice']",
                    "symbol": "[data-field='symbol']"
                }
            }
        )
        
        print(f"📊 Multiple crawl results:")
        for i, result in enumerate(multiple_results):
            if result.get('success', True):
                print(f"  - URL {i+1}: {result.get('title', 'N/A')}")
            else:
                print(f"  - URL {i+1}: Failed - {result.get('error', 'Unknown error')}")
        
        # Demo 4: Health check
        print("\n🏥 Health check...")
        health = await crawler.health_check()
        print(f"  - Status: {health['status']}")
        print(f"  - Message: {health['message']}")
        
    except Exception as e:
        print(f"❌ Error during web crawler demo: {e}")
        logger.error(f"Web crawler demo failed: {e}")
    
    finally:
        # Stop crawler
        await crawler.stop()
        print("🛑 Web crawler stopped")


async def demo_api_collector():
    """Demonstrate API collector functionality."""
    print("\n=== API Collector Demo ===")
    
    # Create API collector
    collector = APICollector("DemoAPICollector")
    
    # Initialize with configuration
    config = {
        "api_keys": {
            "alpha_vantage": "demo_key",  # Replace with real API key
            "quandl": "demo_key"  # Replace with real API key
        },
        "timeout": 30,
        "max_retries": 3,
        "rate_limits": {
            "alpha_vantage": {"requests_per_minute": 5, "requests_per_hour": 500},
            "quandl": {"requests_per_minute": 10, "requests_per_hour": 2000}
        }
    }
    
    collector.initialize(config)
    
    try:
        # Start collector
        await collector.start()
        print("✅ API collector started successfully")
        
        # Demo 1: Test API connectivity
        print("\n🔗 Testing API connectivity...")
        test_result = await collector.make_request(
            "https://httpbin.org/get",
            {"test": "financial_data_collector"}
        )
        print(f"  - Status: {test_result['status_code']}")
        print(f"  - URL: {test_result['url']}")
        
        # Demo 2: Simulate financial API call
        print("\n📊 Simulating financial API call...")
        # Note: This would require real API keys and endpoints
        print("  - Would call Alpha Vantage API for stock data")
        print("  - Would call Quandl API for economic data")
        print("  - Would call SEC EDGAR API for filings")
        
        # Demo 3: Health check
        print("\n🏥 Health check...")
        health = await collector.health_check()
        print(f"  - Status: {health['status']}")
        print(f"  - Message: {health['message']}")
        
    except Exception as e:
        print(f"❌ Error during API collector demo: {e}")
        logger.error(f"API collector demo failed: {e}")
    
    finally:
        # Stop collector
        await collector.stop()
        print("🛑 API collector stopped")


async def demo_integrated_workflow():
    """Demonstrate integrated workflow with crawl4ai."""
    print("\n=== Integrated Workflow Demo ===")
    
    # Create DI container
    container = DIContainer()
    
    # Create event bus
    event_bus = EventBus()
    
    # Register services
    container.register_instance(EventBus, event_bus)
    
    # Create web crawler
    web_crawler = WebCrawler("IntegratedWebCrawler")
    web_crawler.initialize({
        "browser": {"headless": True},
        "extraction_strategy": "llm",
        "request_delay": 1.0
    })
    web_crawler.event_bus = event_bus
    
    # Create API collector
    api_collector = APICollector("IntegratedAPICollector")
    api_collector.initialize({
        "timeout": 30,
        "max_retries": 3
    })
    api_collector.event_bus = event_bus
    
    try:
        # Start services
        await web_crawler.start()
        await api_collector.start()
        print("✅ All services started successfully")
        
        # Demo: Combined data collection
        print("\n🔄 Combined data collection workflow...")
        
        # Step 1: Crawl financial news
        print("  Step 1: Crawling financial news...")
        news_data = await web_crawler.crawl_url(
            "https://finance.yahoo.com/news/",
            {"extraction_strategy": "llm", "wait_for": 2}
        )
        print(f"    - News crawled: {news_data.get('title', 'N/A')}")
        
        # Step 2: Collect API data
        print("  Step 2: Collecting API data...")
        api_data = await api_collector.make_request(
            "https://httpbin.org/json",
            {"source": "financial_data_collector"}
        )
        print(f"    - API data collected: Status {api_data['status_code']}")
        
        # Step 3: Process combined data
        print("  Step 3: Processing combined data...")
        combined_data = {
            "timestamp": datetime.now().isoformat(),
            "news_data": news_data,
            "api_data": api_data,
            "processing_notes": "Combined web crawling and API collection"
        }
        print(f"    - Combined data created with {len(combined_data)} fields")
        
        # Step 4: Health checks
        print("  Step 4: Health checks...")
        web_health = await web_crawler.health_check()
        api_health = await api_collector.health_check()
        print(f"    - Web crawler: {web_health['status']}")
        print(f"    - API collector: {api_health['status']}")
        
        print("✅ Integrated workflow completed successfully")
        
    except Exception as e:
        print(f"❌ Error during integrated workflow: {e}")
        logger.error(f"Integrated workflow failed: {e}")
    
    finally:
        # Stop services
        await web_crawler.stop()
        await api_collector.stop()
        print("🛑 All services stopped")


async def main():
    """Run all demos."""
    print("🚀 Crawl4AI Financial Data Collection Demo")
    print("=" * 50)
    
    try:
        # Check if crawl4ai is available
        try:
            import crawl4ai
            print(f"✅ Crawl4AI version: {crawl4ai.__version__}")
        except ImportError:
            print("❌ Crawl4AI not installed. Please install it first:")
            print("   pip install crawl4ai")
            return
        
        # Run demos
        await demo_crawl4ai_web_crawler()
        await demo_api_collector()
        await demo_integrated_workflow()
        
        print("\n" + "=" * 50)
        print("🎉 All demos completed successfully!")
        print("\n📚 Next steps:")
        print("  1. Install crawl4ai: pip install crawl4ai")
        print("  2. Run setup: crawl4ai-setup")
        print("  3. Configure API keys in your .env file")
        print("  4. Start the full system: make dev")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
