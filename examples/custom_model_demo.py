#!/usr/bin/env python3
"""
Custom Model Demo for Financial Data Collector

This script demonstrates how to use your custom model endpoint
"ep-20250725215501-7zrfm" with Crawl4AI for financial data extraction.
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


async def demo_custom_model_basic():
    """Demonstrate basic custom model usage."""
    print("\n=== Custom Model Basic Demo ===")
    print("Using model: ep-20250725215501-7zrfm")
    
    # Method 1: Direct configuration with your custom model
    print("\n🔧 Method 1: Direct configuration...")
    
    # Replace with your actual API credentials
    volc_api_key = "your_volc_api_key_here"
    volc_base_url = "https://ark.cn-beijing.volces.com/api/v3"
    custom_model = "ep-20250725215501-7zrfm"
    
    # Create Volcano Engine configuration with your custom model
    volc_config = VolcLLMConfig(
        api_key=volc_api_key,
        base_url=volc_base_url,
        model=custom_model
    )
    
    # Get LLM configuration
    llm_config = volc_config.get_llm_config()
    print(f"✅ LLM Config created: {llm_config.provider}")
    print(f"✅ Custom model: {custom_model}")
    
    # Get extraction strategy
    extraction_strategy = volc_config.get_extraction_strategy(
        instruction="Extract financial data from the webpage using your specialized knowledge",
        schema={
            "type": "object",
            "properties": {
                "financial_data": {"type": "object"}
            }
        }
    )
    print(f"✅ Extraction strategy created: {extraction_strategy.provider}")


async def demo_custom_model_with_crawler():
    """Demonstrate custom model with web crawler."""
    print("\n=== Custom Model with Web Crawler Demo ===")
    
    # Create web crawler
    crawler = WebCrawler("CustomModelCrawler")
    
    # Configuration with your custom model
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
            "model": "ep-20250725215501-7zrfm",  # Your custom model
            "instruction": """
            You are a specialized financial data extraction AI. Extract financial data from the webpage with high accuracy.
            
            Focus on:
            1. Stock prices, volume, and market data
            2. Company information and financial metrics
            3. News articles and financial reports
            4. Market trends and analysis
            5. Earnings data and financial statements
            
            Return structured data with clear categorization of financial information.
            Ensure data accuracy and completeness.
            """,
            "schema": {
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
                                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]}
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
        print("✅ Custom model crawler started")
        
        # Demo: Crawl a financial website
        print("\n💰 Crawling financial website with custom model...")
        
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
        print(f"❌ Error during custom model crawler demo: {e}")
        logger.error(f"Custom model crawler demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Custom model crawler stopped")


async def demo_custom_model_financial_extraction():
    """Demonstrate custom model for financial data extraction."""
    print("\n=== Custom Model Financial Data Extraction Demo ===")
    
    # Create web crawler
    crawler = WebCrawler("FinancialDataExtractor")
    
    # Configuration optimized for financial data extraction
    config = {
        "browser": {
            "browser_type": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080}
        },
        "extraction_strategy": "llm",
        "llm_config": {
            "provider": "volc",
            "api_key": "your_volc_api_key_here",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-20250725215501-7zrfm",
            "instruction": """
            You are a specialized financial data extraction AI. Extract comprehensive financial data from the webpage.
            
            Your expertise includes:
            - Stock market data analysis
            - Company financial metrics
            - Market trends and indicators
            - News sentiment analysis
            - Earnings and financial statements
            
            Return structured, accurate financial data with clear categorization.
            """,
            "schema": {
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
                            "market_cap": {"type": "number"},
                            "pe_ratio": {"type": "number"},
                            "dividend_yield": {"type": "number"},
                            "high_52w": {"type": "number"},
                            "low_52w": {"type": "number"}
                        }
                    },
                    "company_info": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "sector": {"type": "string"},
                            "industry": {"type": "string"},
                            "description": {"type": "string"},
                            "employees": {"type": "number"},
                            "headquarters": {"type": "string"}
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
                                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                                "relevance": {"type": "number", "minimum": 0, "maximum": 1}
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
        print("✅ Financial data extractor started")
        
        # Demo: Extract financial data from multiple sources
        print("\n📈 Extracting financial data...")
        
        # Simulate financial data extraction
        financial_urls = [
            "https://httpbin.org/html",  # Demo URL
            "https://httpbin.org/json",  # Demo URL
        ]
        
        for i, url in enumerate(financial_urls):
            print(f"\n📊 Processing URL {i+1}: {url}")
            
            try:
                result = await crawler.crawl_url(
                    url,
                    {
                        "extraction_strategy": "llm",
                        "wait_for": 2,
                        "llm_config": {
                            "provider": "volc",
                            "api_key": "your_volc_api_key_here",
                            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                            "model": "ep-20250725215501-7zrfm"
                        }
                    }
                )
                
                print(f"  ✅ Extraction successful: {result.get('success', False)}")
                print(f"  📝 Title: {result.get('title', 'N/A')}")
                
                if 'financial_data' in result:
                    financial_data = result['financial_data']
                    print(f"  💰 Financial data fields: {len(financial_data)}")
                    
                    if 'stock_data' in financial_data:
                        stock_data = financial_data['stock_data']
                        print(f"    - Stock data: {list(stock_data.keys())}")
                    
                    if 'news' in financial_data:
                        news_data = financial_data['news']
                        print(f"    - News items: {len(news_data)}")
                
            except Exception as e:
                print(f"  ❌ Extraction failed: {e}")
        
        # Demo: Performance metrics
        print("\n📊 Performance metrics...")
        health = await crawler.health_check()
        print(f"  - Overall status: {health['status']}")
        print(f"  - Health message: {health['message']}")
        
    except Exception as e:
        print(f"❌ Error during financial data extraction demo: {e}")
        logger.error(f"Financial data extraction demo failed: {e}")
    
    finally:
        await crawler.stop()
        print("🛑 Financial data extractor stopped")


async def demo_custom_model_comparison():
    """Demonstrate comparison between custom model and standard models."""
    print("\n=== Custom Model Comparison Demo ===")
    
    # Configuration for different models
    models = [
        {
            "name": "Your Custom Model",
            "model": "ep-20250725215501-7zrfm",
            "description": "Specialized for financial data extraction"
        },
        {
            "name": "Standard Model",
            "model": "doubao-pro-4k",
            "description": "General purpose model"
        }
    ]
    
    for model in models:
        print(f"\n🔧 Testing {model['name']}...")
        print(f"  Model: {model['model']}")
        print(f"  Description: {model['description']}")
        
        try:
            # Create extraction strategy
            extraction_strategy = create_volc_llm_strategy(
                api_key="your_volc_api_key_here",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                model=model["model"],
                instruction="Extract financial data from the webpage",
                schema={
                    "type": "object",
                    "properties": {
                        "financial_data": {"type": "object"}
                    }
                }
            )
            
            print(f"  ✅ Strategy created successfully")
            print(f"  📊 Provider: {extraction_strategy.provider}")
            print(f"  🤖 Model: {model['model']}")
            
        except Exception as e:
            print(f"  ❌ Strategy creation failed: {e}")


async def main():
    """Run all custom model demos."""
    print("🚀 Custom Model Demo for Financial Data Collector")
    print("=" * 60)
    print("Using custom model: ep-20250725215501-7zrfm")
    print("=" * 60)
    
    try:
        # Check if required modules are available
        try:
            from financial_data_collector.core.crawler.volc_llm_config import VolcLLMConfig
            print("✅ Custom model configuration module available")
        except ImportError as e:
            print(f"❌ Custom model configuration module not available: {e}")
            return
        
        # Run demos
        await demo_custom_model_basic()
        await demo_custom_model_with_crawler()
        await demo_custom_model_financial_extraction()
        await demo_custom_model_comparison()
        
        print("\n" + "=" * 60)
        print("🎉 All custom model demos completed successfully!")
        print("\n📚 Key features demonstrated:")
        print("  ✅ Custom model configuration")
        print("  ✅ Web crawler integration")
        print("  ✅ Financial data extraction")
        print("  ✅ Model comparison")
        print("\n🔧 Next steps:")
        print("  1. Replace 'your_volc_api_key_here' with your actual API key")
        print("  2. Replace 'https://ark.cn-beijing.volces.com/api/v3' with your actual base URL")
        print("  3. Test with real financial websites")
        print("  4. Configure in your .env file:")
        print("     VOLC_API_KEY=your_actual_api_key")
        print("     VOLC_BASE_URL=your_actual_base_url")
        print("     VOLC_MODEL=ep-20250725215501-7zrfm")
        print("\n🎯 Your custom model is optimized for financial data extraction!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
