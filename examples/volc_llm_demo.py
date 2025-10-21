#!/usr/bin/env python3
"""
Volcano Engine LLM Demo for Financial Data Collector

This script demonstrates how to use Volcano Engine API with Crawl4AI
for financial data extraction.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from financial_data_collector.core.crawler.web_crawler import WebCrawler
from financial_data_collector.core.crawler.volc_llm_config import (
    create_volc_llm_strategy, 
    get_volc_llm_config_from_env,
    VolcLLMConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_volc_llm_basic():
    """Demonstrate basic Volcano Engine LLM usage."""
    print("\n=== Volcano Engine LLM Basic Demo ===")
    
    # Method 1: Direct configuration
    print("\n🔧 Method 1: Direct configuration...")
    
    # Replace with your actual API credentials
    volc_api_key = "your_volc_api_key_here"
    volc_base_url = "https://ark.cn-beijing.volces.com/api/v3"
    
    # Create Volcano Engine configuration
    volc_config = VolcLLMConfig(
        api_key=volc_api_key,
        base_url=volc_base_url,
        model="ep-20250725215501-7zrfm"
    )
    
    # Get LLM configuration
    llm_config = volc_config.get_llm_config()
    print(f"✅ LLM Config created: {llm_config.provider}")
    
    # Get extraction strategy
    extraction_strategy = volc_config.get_extraction_strategy(
        instruction="Extract financial data from the webpage",
        schema={
            "type": "object",
            "properties": {
                "financial_data": {"type": "object"}
            }
        }
    )
    print(f"✅ Extraction strategy created: {extraction_strategy.provider}")


async def demo_volc_llm_with_crawler():
    """Demonstrate Volcano Engine LLM with web crawler."""
    print("\n=== Volcano Engine LLM with Web Crawler Demo ===")
    
    # Create web crawler
    crawler = WebCrawler("VolcLLMCrawler")
    
    # Configuration with Volcano Engine
    config = {
        "browser": {
            "browser_type": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080}
        },
        "extraction_strategy": "llm",
        "llm_config": {
            "provider": "volc",  # Use Volcano Engine
            "api_key": "your_volc_api_key_here",  # Replace with your API key
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",  # Replace with your base URL
            "model": "ep-20250725215501-7zrfm",
            "instruction": "Extract financial data from the webpage. Focus on stock prices, volume, and market data.",
            "schema": {
                "type": "object",
                "properties": {
                    "stock_data": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "price": {"type": "number"},
                            "volume": {"type": "number"},
                            "change": {"type": "number"}
                        }
                    },
                    "news": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "summary": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        "request_delay": 2.0,
        "timeout": 30
    }
    
    crawler.initialize(config)
    
    try:
        await crawler.start()
        print("✅ Volcano Engine crawler started")
        
        # Demo: Crawl a financial website
        print("\n💰 Crawling financial website with Volcano Engine LLM...")
        
        # Note: This is a demo URL - replace with actual financial websites
        result = await crawler.crawl_url(
            "https://httpbin.org/html",  # Demo URL
            {
                "extraction_strategy": "llm",
                "wait_for": 3,
                "llm_config": {
                    "provider": "volc",
                    "api_key": "your_volc_api_key_here",
                    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                    "model": "ep-20250725215501-7zrfm"
                }
            }
        )
        
        print(f"📊 Crawl results:")
        print(f"  - URL: {result.get('url', 'N/A')}")
        print(f"  - Success: {result.get('success', False)}")
        print(f"  - Title: {result.get('title', 'N/A')}")
        
        if 'financial_data' in result:
            print(f"  - Financial data extracted: {len(result['financial_data'])} fields")
            print(f"  - Data: {result['financial_data']}")
        
        # Demo: Health check
        print("\n🏥 Health check...")
        health = await crawler.health_check()
        print(f"  - Status: {health['status']}")
        print(f"  - Message: {health['message']}")
        
    except Exception as e:
        print(f"❌ Error during Volcano Engine crawler demo: {e}")
        logger.error(f"Volcano Engine crawler demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Volcano Engine crawler stopped")


async def demo_volc_llm_extraction_strategies():
    """Demonstrate different Volcano Engine LLM extraction strategies."""
    print("\n=== Volcano Engine LLM Extraction Strategies Demo ===")
    
    # Different extraction strategies
    strategies = [
        {
            "name": "Financial Data Extraction",
            "instruction": "Extract stock prices, volume, and market data from the webpage",
            "schema": {
                "type": "object",
                "properties": {
                    "stock_data": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "price": {"type": "number"},
                            "volume": {"type": "number"}
                        }
                    }
                }
            }
        },
        {
            "name": "News Extraction",
            "instruction": "Extract financial news headlines and summaries from the webpage",
            "schema": {
                "type": "object",
                "properties": {
                    "news": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "summary": {"type": "string"},
                                "sentiment": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        {
            "name": "Company Information Extraction",
            "instruction": "Extract company information and financial metrics from the webpage",
            "schema": {
                "type": "object",
                "properties": {
                    "company_info": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "sector": {"type": "string"},
                            "market_cap": {"type": "number"}
                        }
                    }
                }
            }
        }
    ]
    
    for strategy in strategies:
        print(f"\n📋 Testing strategy: {strategy['name']}")
        
        try:
            # Create extraction strategy
            extraction_strategy = create_volc_llm_strategy(
                api_key="your_volc_api_key_here",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                model="ep-20250725215501-7zrfm",
                instruction=strategy["instruction"],
                schema=strategy["schema"]
            )
            
            print(f"  ✅ Strategy created: {extraction_strategy.provider}")
            print(f"  📝 Instruction: {strategy['instruction'][:50]}...")
            print(f"  🏗️  Schema: {strategy['schema']['type']} with {len(strategy['schema']['properties'])} properties")
            
        except Exception as e:
            print(f"  ❌ Strategy creation failed: {e}")


async def demo_volc_llm_environment_config():
    """Demonstrate Volcano Engine LLM configuration from environment variables."""
    print("\n=== Environment Configuration Demo ===")
    
    # Set environment variables (in real usage, these would be set externally)
    os.environ["VOLC_API_KEY"] = "your_volc_api_key_here"
    os.environ["VOLC_BASE_URL"] = "https://ark.cn-beijing.volces.com/api/v3"
    
    try:
        # Get configuration from environment
        volc_config = get_volc_llm_config_from_env()
        
        if volc_config:
            print("✅ Environment configuration loaded successfully")
            print(f"  - API Key: {volc_config.api_key[:10]}...")
            print(f"  - Base URL: {volc_config.base_url}")
            print(f"  - Model: {volc_config.model}")
            
            # Create LLM config
            llm_config = volc_config.get_llm_config()
            print(f"  - LLM Config: {llm_config.provider}")
            
        else:
            print("❌ Environment configuration not found")
            print("  Please set VOLC_API_KEY and VOLC_BASE_URL environment variables")
            
    except Exception as e:
        print(f"❌ Environment configuration failed: {e}")
    
    finally:
        # Clean up environment variables
        if "VOLC_API_KEY" in os.environ:
            del os.environ["VOLC_API_KEY"]
        if "VOLC_BASE_URL" in os.environ:
            del os.environ["VOLC_BASE_URL"]


async def demo_volc_llm_comparison():
    """Demonstrate comparison between different LLM providers."""
    print("\n=== LLM Provider Comparison Demo ===")
    
    # Configuration for different providers
    providers = [
        {
            "name": "Volcano Engine",
            "provider": "volc",
            "api_key": "your_volc_api_key_here",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-20250725215501-7zrfm"
        },
        {
            "name": "OpenAI",
            "provider": "openai",
            "api_key": "your_openai_api_key_here",
            "base_url": None,
            "model": "gpt-4"
        },
        {
            "name": "Anthropic",
            "provider": "anthropic",
            "api_key": "your_anthropic_api_key_here",
            "base_url": None,
            "model": "claude-3-sonnet"
        }
    ]
    
    for provider in providers:
        print(f"\n🔧 Testing {provider['name']}...")
        
        try:
            if provider["provider"] == "volc":
                # Use Volcano Engine configuration
                extraction_strategy = create_volc_llm_strategy(
                    api_key=provider["api_key"],
                    base_url=provider["base_url"],
                    model=provider["model"],
                    instruction="Extract financial data from the webpage"
                )
            else:
                # Use standard configuration
                from crawl4ai.extraction_strategy import LLMExtractionStrategy
                extraction_strategy = LLMExtractionStrategy(
                    provider=provider["provider"],
                    api_token=provider["api_key"],
                    model=provider["model"],
                    instruction="Extract financial data from the webpage"
                )
            
            print(f"  ✅ {provider['name']} strategy created successfully")
            print(f"  📊 Provider: {extraction_strategy.provider}")
            print(f"  🤖 Model: {provider['model']}")
            
        except Exception as e:
            print(f"  ❌ {provider['name']} strategy creation failed: {e}")


async def main():
    """Run all Volcano Engine LLM demos."""
    print("🚀 Volcano Engine LLM Demo for Financial Data Collector")
    print("=" * 60)
    
    try:
        # Check if required modules are available
        try:
            from financial_data_collector.core.crawler.volc_llm_config import VolcLLMConfig
            print("✅ Volcano Engine LLM configuration module available")
        except ImportError as e:
            print(f"❌ Volcano Engine LLM configuration module not available: {e}")
            return
        
        # Run demos
        await demo_volc_llm_basic()
        await demo_volc_llm_with_crawler()
        await demo_volc_llm_extraction_strategies()
        await demo_volc_llm_environment_config()
        await demo_volc_llm_comparison()
        
        print("\n" + "=" * 60)
        print("🎉 All Volcano Engine LLM demos completed successfully!")
        print("\n📚 Key features demonstrated:")
        print("  ✅ Volcano Engine LLM configuration")
        print("  ✅ Web crawler integration")
        print("  ✅ Multiple extraction strategies")
        print("  ✅ Environment variable configuration")
        print("  ✅ Provider comparison")
        print("\n🔧 Next steps:")
        print("  1. Replace 'your_volc_api_key_here' with your actual API key")
        print("  2. Replace 'https://ark.cn-beijing.volces.com/api/v3' with your actual base URL")
        print("  3. Test with real financial websites")
        print("  4. Configure in your .env file:")
        print("     VOLC_API_KEY=your_actual_api_key")
        print("     VOLC_BASE_URL=your_actual_base_url")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
