"""
Pytest configuration and fixtures for the test suite.
"""

import pytest
import asyncio
import os
import tempfile
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

# Configure asyncio for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing."""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis_instance = Mock()
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture
def mock_celery_app():
    """Mock Celery app for testing."""
    with patch('src.financial_data_collector.core.tasks.celery_app.celery_app') as mock_app:
        mock_app.AsyncResult.return_value = Mock()
        yield mock_app


@pytest.fixture
def test_config():
    """Test configuration for crawlers."""
    return {
        "extraction_strategy": "css",
        "wait_for": 1,
        "max_scrolls": 0,
        "timeout": 30,
        "browser": {
            "headless": True
        }
    }


@pytest.fixture
def test_urls():
    """Test URLs for crawling."""
    return [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/xml",
        "https://httpbin.org/robots.txt"
    ]


@pytest.fixture
def mock_crawl_result():
    """Mock crawl result for testing."""
    return {
        "success": True,
        "url": "https://httpbin.org/html",
        "title": "Test Page",
        "content": {
            "markdown": "# Test Page\nThis is a test page.",
            "html": "<html><body><h1>Test Page</h1></body></html>",
            "text": "Test Page This is a test page."
        },
        "metadata": {
            "word_count": 10,
            "links_count": 5,
            "images_count": 2,
            "extraction_strategy": "css"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_llm_config():
    """Mock LLM configuration for testing."""
    return {
        "provider": "volc",
        "api_token": "test_api_key",
        "base_url": "https://test.volces.com/api/v3",
        "model": "ep-20250725215501-7zrfm"
    }


@pytest.fixture
def mock_volc_env():
    """Mock Volcano Engine environment variables."""
    env_vars = {
        "VOLC_API_KEY": "test_volc_api_key",
        "VOLC_BASE_URL": "https://test.volces.com/api/v3",
        "VOLC_MODEL": "ep-20250725215501-7zrfm"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_webcrawler():
    """Mock WebCrawler for testing."""
    with patch('src.financial_data_collector.core.crawler.web_crawler.WebCrawler') as mock_crawler:
        mock_instance = Mock()
        mock_crawler.return_value = mock_instance
        mock_instance.initialize = Mock()
        mock_instance.start = Mock()
        mock_instance.stop = Mock()
        mock_instance.collect_data = Mock(return_value={"success": True, "data": "test"})
        yield mock_instance


@pytest.fixture
def mock_enhanced_webcrawler():
    """Mock EnhancedWebCrawler for testing."""
    with patch('src.financial_data_collector.core.crawler.enhanced_web_crawler.EnhancedWebCrawler') as mock_crawler:
        mock_instance = Mock()
        mock_crawler.return_value = mock_instance
        mock_instance.initialize = Mock()
        mock_instance.start = Mock()
        mock_instance.stop = Mock()
        mock_instance.crawl_url_enhanced = Mock(return_value={"success": True, "enhanced_data": "test"})
        yield mock_instance


@pytest.fixture
def mock_task_manager():
    """Mock TaskManager for testing."""
    with patch('src.financial_data_collector.core.tasks.task_manager.TaskManager') as mock_manager:
        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        mock_instance.submit_crawl_task = Mock(return_value="test-task-123")
        mock_instance.submit_batch_crawl_task = Mock(return_value="test-batch-456")
        mock_instance.get_task_status = Mock(return_value={
            "task_id": "test-task-123",
            "status": "SUCCESS",
            "result": {"success": True}
        })
        mock_instance.cancel_task = Mock(return_value=True)
        mock_instance.get_active_tasks = Mock(return_value=[])
        mock_instance.cleanup_completed_tasks = Mock(return_value=0)
        mock_instance.get_queue_info = Mock(return_value={
            "active_tasks": {},
            "registered_tasks": ["crawl_task", "crawl_url_batch"]
        })
        yield mock_instance


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to E2E tests
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker to stress tests
        if "stress" in item.nodeid or "load" in item.nodeid:
            item.add_marker(pytest.mark.slow)


# Test reporting (commented out to avoid plugin conflicts)
# def pytest_html_report_title(report):
#     """Set HTML report title."""
#     report.title = "Financial Data Collector Test Report"


# def pytest_html_results_table_header(cells):
#     """Customize HTML report table header."""
#     cells.insert(1, html.th('Description'))
#     cells.pop()


# def pytest_html_results_table_row(report, cells):
#     """Customize HTML report table rows."""
#     cells.insert(1, html.td(report.description))
#     cells.pop()


# Test data fixtures
@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing."""
    return {
        "company_name": "Test Corp",
        "stock_price": 100.50,
        "market_cap": 1000000000,
        "pe_ratio": 15.5,
        "dividend_yield": 2.5,
        "revenue": 500000000,
        "profit": 50000000,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_crawl_configs():
    """Sample crawl configurations for testing."""
    return {
        "basic": {
            "extraction_strategy": "css",
            "wait_for": 1,
            "max_scrolls": 0
        },
        "enhanced": {
            "extraction_strategy": "css",
            "wait_for": 2,
            "max_scrolls": 1,
            "proxy_pool": {"enabled": True},
            "anti_detection": {"enabled": True}
        },
        "llm": {
            "extraction_strategy": "llm",
            "llm_config": {
                "provider": "volc",
                "model": "ep-20250725215501-7zrfm"
            },
            "wait_for": 3,
            "max_scrolls": 2
        }
    }


@pytest.fixture
def sample_task_priorities():
    """Sample task priorities for testing."""
    from src.financial_data_collector.core.tasks.task_manager import TaskPriority
    
    return {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT
    }


# Performance test fixtures
@pytest.fixture
def performance_metrics():
    """Performance metrics for testing."""
    return {
        "max_response_time": 5.0,  # seconds
        "max_memory_usage": 500,   # MB
        "min_throughput": 10,      # requests/second
        "max_cpu_usage": 80        # percentage
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    # Add any cleanup logic here
    pass


# Skip conditions
def pytest_runtest_setup(item):
    """Skip tests based on conditions."""
    # Skip E2E tests if not in integration mode
    if "e2e" in item.nodeid and not os.getenv("RUN_E2E_TESTS"):
        pytest.skip("E2E tests require RUN_E2E_TESTS environment variable")
    
    # Skip performance tests if not in performance mode
    if "performance" in item.nodeid and not os.getenv("RUN_PERFORMANCE_TESTS"):
        pytest.skip("Performance tests require RUN_PERFORMANCE_TESTS environment variable")
