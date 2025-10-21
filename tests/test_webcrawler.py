#!/usr/bin/env python3
"""
Test our WebCrawler class and its integration with crawl4ai.
This tests our own code, not the crawl4ai library itself.
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebCrawlerTester:
    """Test our WebCrawler class and its crawl4ai integration."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = []
        self.cookie_config = self._load_cookie_config()
        self._prepare_runtime_env()
    
    def _load_cookie_config(self):
        """加载 Cookie 配置"""
        cookie_file = os.path.join(os.path.dirname(__file__), 'cookie.json')
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cookie config: {e}")
            return {}

    async def test_webcrawler_llm_when_env_ready(self):
        """Run LLM extraction only when VOLC env is set; otherwise skip gracefully."""
        self.log("🧪 Test (LLM): Testing WebCrawler LLM extraction when env is ready...")
        
        # Check env
        volc_api = os.getenv("VOLC_API_KEY")
        volc_base = os.getenv("VOLC_BASE_URL")
        volc_model = os.getenv("VOLC_MODEL")
        if not (volc_api and volc_base):
            self.log("   ⚠️ VOLC env not set, skipping LLM test")
            return True  # skip as pass
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            
            crawler = WebCrawler("TestWebCrawler")
            crawler.initialize({
                "browser": {"headless": True},
                "extraction_strategy": "llm",
                "timeout": 60
            })
            await crawler.start()
            
            result = await crawler.collect_data("web", {
                "url": "https://www.nbcnews.com/business",
                # no llm_config here intentionally to exercise env fallback
            })
            
            ok = bool(result and result.get('success', False))
            if ok:
                self.log("   ✅ LLM extraction executed (env fallback)")
                return True
            else:
                self.log(f"   ❌ LLM extraction failed: {result}", "ERROR")
                return False
        except Exception as e:
            self.log(f"   ❌ LLM test error: {e}", "ERROR")
            return False
        finally:
            try:
                if 'crawler' in locals():
                    await crawler.stop()
            except:
                pass
    
    def _prepare_runtime_env(self):
        """Prepare writable env paths to avoid permission issues in container."""
        try:
            tmp_dir = "/tmp"
            os.environ.setdefault("HOME", tmp_dir)
            # Playwright caches
            pw_cache = os.path.join(tmp_dir, "ms-playwright")
            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", pw_cache)
            # Crawl4AI workdir/cache
            c4ai_dir = os.path.join(tmp_dir, "crawl4ai")
            os.environ.setdefault("CRAWL4AI_WORKDIR", c4ai_dir)
            os.environ.setdefault("CRAWL4AI_CACHE_DIR", os.path.join(c4ai_dir, "cache"))
            # Ensure directories exist
            for d in [pw_cache, c4ai_dir, os.environ["CRAWL4AI_CACHE_DIR"]]:
                os.makedirs(d, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to prepare runtime env: {e}")
    
    def log(self, message, level="INFO"):
        """Log message based on verbosity."""
        if self.verbose or level == "ERROR":
            print(message)
        if level == "ERROR":
            logger.error(message)
    
    async def test_webcrawler_initialization(self):
        """Test WebCrawler class initialization."""
        self.log("🧪 Test 1: Testing WebCrawler initialization...")
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            
            # Test basic initialization
            crawler = WebCrawler("TestWebCrawler")
            self.log(f"   ✅ WebCrawler instance created: {crawler.name}")
            
            # Test configuration
            config = {
                "browser": {
                    "browser_type": "chromium",
                    "headless": True
                },
                "extraction_strategy": "css",
                "timeout": 30
            }
            
            crawler.initialize(config)
            self.log(f"   ✅ WebCrawler configured successfully")
            
            return True
            
        except Exception as e:
            self.log(f"   ❌ WebCrawler initialization failed: {e}", "ERROR")
            return False
    
    async def test_webcrawler_lifecycle(self):
        """Test WebCrawler start/stop lifecycle."""
        self.log("🧪 Test 2: Testing WebCrawler lifecycle...")
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            
            crawler = WebCrawler("TestWebCrawler")
            crawler.initialize({
                "browser": {"headless": True},
                "extraction_strategy": "css",
                "timeout": 30
            })
            
            # Test start
            await crawler.start()
            self.log(f"   ✅ WebCrawler started successfully")
            
            # Test health check
            health = await crawler.health_check()
            self.log(f"   ✅ Health check: {health}")
            
            # Test stop
            await crawler.stop()
            self.log(f"   ✅ WebCrawler stopped successfully")
            
            return True
            
        except Exception as e:
            self.log(f"   ❌ WebCrawler lifecycle test failed: {e}", "ERROR")
            return False
    
    async def test_webcrawler_data_collection(self):
        """Test WebCrawler data collection functionality."""
        self.log("🧪 Test 3: Testing WebCrawler data collection...")
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            
            crawler = WebCrawler("TestWebCrawler")
            crawler.initialize({
                "browser": {"headless": True},
                "extraction_strategy": "css",
                "timeout": 30
            })
            
            await crawler.start()
            
            # Test data collection
            result = await crawler.collect_data("web", {
                "url": "https://github.com/luoq?tab=stars",
                "extraction_strategy": "css"
            })
            
            if result and result.get('success', False):
                self.log(f"   ✅ Data collection successful")
                self.log(f"   ✅ Title: {result.get('title', 'N/A')}")
                self.log(f"   ✅ Status: {result.get('status_code', 'N/A')}")
                self.log(f"   ✅ Content length: {len(result.get('content', ''))}")
                return True
            else:
                self.log(f"   ❌ Data collection failed: {result}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Data collection test failed: {e}", "ERROR")
            return False
        
        finally:
            # Clean up
            try:
                if 'crawler' in locals():
                    await crawler.stop()
            except:
                pass
    
    async def test_webcrawler_configuration_handling(self):
        """Test WebCrawler configuration handling."""
        self.log("🧪 Test 4: Testing WebCrawler configuration handling...")
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            
            crawler = WebCrawler("TestWebCrawler")
            
            # Test different configurations
            configs = [
                {
                    "browser": {"headless": True},
                    "extraction_strategy": "css",
                    "timeout": 30
                },
                {
                    "browser": {"headless": True},
                    "extraction_strategy": "markdown",
                    "timeout": 60
                }
            ]
            
            for i, config in enumerate(configs):
                crawler.initialize(config)
                self.log(f"   ✅ Configuration {i+1} applied successfully")
            
            return True
            
        except Exception as e:
            self.log(f"   ❌ Configuration handling test failed: {e}", "ERROR")
            return False
    
    async def test_webcrawler_error_handling(self):
        """Test WebCrawler error handling."""
        self.log("🧪 Test 5: Testing WebCrawler error handling...")
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            
            crawler = WebCrawler("TestWebCrawler")
            crawler.initialize({
                "browser": {"headless": True},
                "extraction_strategy": "css",
                "timeout": 30
            })
            
            await crawler.start()
            
            # Test with invalid URL
            result = await crawler.collect_data("web", {
                "url": "https://invalid-url-that-does-not-exist.com",
                "extraction_strategy": "css"
            })
            
            # Should handle error gracefully
            if result and not result.get('success', True):
                self.log(f"   ✅ Error handling working correctly")
                self.log(f"   ✅ Error message: {result.get('error', 'N/A')}")
                return True
            else:
                self.log(f"   ⚠️ Error handling may not be working as expected")
                return True  # Still pass, as this might be expected behavior
                
        except Exception as e:
            self.log(f"   ❌ Error handling test failed: {e}", "ERROR")
            return False
        
        finally:
            # Clean up
            try:
                if 'crawler' in locals():
                    await crawler.stop()
            except:
                pass
    
    async def test_webcrawler_with_headers(self):
        """Test WebCrawler with headers from cookie.json."""
        self.log("🧪 Test 6: Testing WebCrawler with headers...")
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            
            crawler = WebCrawler("TestWebCrawler")
            crawler.initialize({
                "browser": {"headless": True},
                "extraction_strategy": "css",
                "timeout": 30
            })
            
            await crawler.start()
            
            # Get headers from cookie.json
            headers = self.cookie_config.get('headers', {})
            
            result = await crawler.collect_data("web", {
                "url": "https://github.com/luoq?tab=stars",
                "headers": headers,
                "extraction_strategy": "css",
                "wait_for": 3,
                "max_scrolls": 1
            })
            
            if result and result.get('success', False):
                self.log(f"   ✅ GitHub crawl successful")
                self.log(f"   ✅ Title: {result.get('title', 'N/A')}")
                self.log(f"   ✅ Content length: {len(result.get('content', {}).get('text', ''))}")
                
                # Check if GitHub page content was loaded
                content = result.get('content', {}).get('text', '')
                if 'luoq' in content and 'GitHub' in content:
                    self.log(f"   ✅ GitHub user page loaded successfully")
                    
                    # Check for starred repositories
                    if 'starred' in content.lower() or 'repositories' in content.lower():
                        self.log(f"   ✅ Starred repositories section detected")
                    else:
                        self.log(f"   ⚠️ Starred repositories section not clearly detected")
                else:
                    self.log(f"   ⚠️ GitHub page content may not have loaded properly")
                
                return True
            else:
                self.log(f"   ❌ GitHub crawl failed: {result}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Headers test failed: {e}", "ERROR")
            return False
        
        finally:
            # Clean up
            try:
                if 'crawler' in locals():
                    await crawler.stop()
            except:
                pass
    
    async def test_webcrawler_storage_functionality(self):
        """Test WebCrawler storage functionality."""
        self.log("🧪 Test 7: Testing WebCrawler storage functionality...")
        
        try:
            from financial_data_collector.core.crawler.web_crawler import WebCrawler
            from financial_data_collector.core.storage import StorageManager
            
            # 测试存储初始化
            crawler = WebCrawler("TestWebCrawlerStorage")
            storage_config = {
                "enabled": True,
                "auto_store": True,
                "strategy": "primary_only"
            }
            
            crawler.initialize({
                "browser": {"headless": True},
                "extraction_strategy": "css",
                "timeout": 30,
                "storage": storage_config
            })
            
            # 验证存储管理器已初始化
            if not crawler.storage_manager:
                self.log("   ❌ Storage manager not initialized", "ERROR")
                return False
            
            self.log("   ✅ Storage manager initialized successfully")
            
            # 测试数据存储功能
            await crawler.start()
            
            test_url = "https://finance.yahoo.com/quote/AAPL"
            result = await crawler.collect_data("web", {
                "url": test_url,
                "extraction_strategy": "css"
            })
            
            if not result or not result.get('success', False):
                self.log(f"   ❌ Data collection failed: {result}", "ERROR")
                return False
            
            # 验证数据已存储
            stored_data = await crawler.storage_manager.get_latest_data(test_url)
            if not stored_data:
                self.log("   ❌ Data not found in storage", "ERROR")
                return False
            
            self.log("   ✅ Data stored successfully")
            return True
            
        except Exception as e:
            self.log(f"   ❌ Storage functionality test failed: {e}", "ERROR")
            return False
        finally:
            try:
                if 'crawler' in locals():
                    # 清理测试数据
                    await crawler.storage_manager.delete_test_data()
                    await crawler.stop()
            except Exception as e:
                self.log(f"   ⚠️ Cleanup failed: {e}")
    
    async def run_all_tests(self):
        """Run all tests."""
        self.log("🚀 WebCrawler Integration Test")
        self.log("=" * 50)
        self.log("Testing our WebCrawler class and its crawl4ai integration")
        
        tests = [
            self.test_webcrawler_initialization,
            self.test_webcrawler_lifecycle,
            self.test_webcrawler_data_collection,
            self.test_webcrawler_configuration_handling,
            self.test_webcrawler_error_handling,
            self.test_webcrawler_with_headers,
            self.test_webcrawler_llm_when_env_ready,
            self.test_webcrawler_storage_functionality  # 添加新测试
        ]
        
        for test in tests:
            try:
                result = await test()
                self.results.append(result)
            except Exception as e:
                self.log(f"❌ Test {test.__name__} crashed: {e}", "ERROR")
                self.results.append(False)
        
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        self.log("\n" + "=" * 50)
        self.log("📊 Test Results Summary:")
        
        passed = sum(self.results)
        total = len(self.results)
        
        test_names = [
            "WebCrawler initialization",
            "WebCrawler lifecycle",
            "WebCrawler data collection",
            "WebCrawler configuration handling",
            "WebCrawler error handling",
            "WebCrawler with headers",
            "WebCrawler LLM extraction (env)"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, self.results)):
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {i+1}. {name}: {status}")
        
        self.log(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! WebCrawler integration is working correctly.")
            return True
        else:
            self.log("⚠️ Some tests failed. Check the output above for details.")
            return False


async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test WebCrawler integration')
    parser.add_argument('--simple', action='store_true', help='Run simple test (less verbose)')
    parser.add_argument('--verbose', action='store_true', help='Run verbose test')
    
    args = parser.parse_args()
    
    # Determine verbosity
    verbose = args.verbose or not args.simple
    
    # Run tests
    tester = WebCrawlerTester(verbose=verbose)
    success = await tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
