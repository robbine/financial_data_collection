"""
API Integration Tests

Test suite for REST API endpoints including:
- Task submission and management
- Direct crawling operations
- Error handling and validation
- Authentication and authorization
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from src.financial_data_collector.api.task_api import router as task_router
from src.financial_data_collector.api.crawler_api import router as crawler_router
from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority


class TestTaskAPI:
    """Test Task API endpoints."""
    
    def setup_method(self):
        """Setup test environment."""
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(task_router)
        self.client = TestClient(self.app)
    
    def test_submit_crawl_task_success(self):
        """Test successful crawl task submission."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.submit_crawl_task.return_value = "test-task-123"
            
            response = self.client.post("/api/tasks/crawl", json={
                "url": "https://httpbin.org/html",
                "config": {"extraction_strategy": "css"},
                "crawler_type": "web",
                "priority": "normal"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert "submitted successfully" in data["message"]
            assert "submitted_at" in data
            
            mock_manager.submit_crawl_task.assert_called_once()
    
    def test_submit_crawl_task_invalid_priority(self):
        """Test crawl task submission with invalid priority."""
        response = self.client.post("/api/tasks/crawl", json={
            "url": "https://httpbin.org/html",
            "config": {"extraction_strategy": "css"},
            "crawler_type": "web",
            "priority": "invalid_priority"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid priority" in data["detail"]
    
    def test_submit_crawl_task_missing_url(self):
        """Test crawl task submission with missing URL."""
        response = self.client.post("/api/tasks/crawl", json={
            "config": {"extraction_strategy": "css"},
            "crawler_type": "web",
            "priority": "normal"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_crawl_task_with_eta(self):
        """Test crawl task submission with ETA."""
        eta = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.submit_crawl_task.return_value = "delayed-task-456"
            
            response = self.client.post("/api/tasks/crawl", json={
                "url": "https://httpbin.org/html",
                "config": {"extraction_strategy": "css"},
                "crawler_type": "web",
                "priority": "normal",
                "eta": eta
            })
            
            assert response.status_code == 200
            mock_manager.submit_crawl_task.assert_called_once()
            # Verify ETA was passed
            call_kwargs = mock_manager.submit_crawl_task.call_args[1]
            assert 'eta' in call_kwargs
    
    def test_submit_batch_crawl_task_success(self):
        """Test successful batch crawl task submission."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.submit_batch_crawl_task.return_value = "batch-task-789"
            
            response = self.client.post("/api/tasks/batch-crawl", json={
                "urls": [
                    "https://httpbin.org/html",
                    "https://httpbin.org/json"
                ],
                "config": {"extraction_strategy": "css", "max_concurrent": 2},
                "crawler_type": "web",
                "priority": "high"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "batch-task-789"
            assert "2 URLs" in data["message"]
            
            mock_manager.submit_batch_crawl_task.assert_called_once()
    
    def test_submit_batch_crawl_task_empty_urls(self):
        """Test batch crawl task submission with empty URLs."""
        response = self.client.post("/api/tasks/batch-crawl", json={
            "urls": [],
            "config": {"extraction_strategy": "css"},
            "crawler_type": "web",
            "priority": "normal"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_get_task_status_success(self):
        """Test successful task status retrieval."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.get_task_status.return_value = {
                "task_id": "test-task-123",
                "status": "SUCCESS",
                "result": {"success": True, "data": "test data"},
                "progress": {"status": "completed"},
                "checked_at": datetime.now().isoformat()
            }
            
            response = self.client.get("/api/tasks/status/test-task-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "SUCCESS"
            assert data["result"]["success"] is True
    
    def test_get_task_status_not_found(self):
        """Test task status retrieval for non-existent task."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.get_task_status.return_value = {
                "task_id": "non-existent-task",
                "status": "UNKNOWN",
                "error": "Task not found",
                "checked_at": datetime.now().isoformat()
            }
            
            response = self.client.get("/api/tasks/status/non-existent-task")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "UNKNOWN"
            assert "error" in data
    
    def test_cancel_task_success(self):
        """Test successful task cancellation."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.cancel_task.return_value = True
            
            response = self.client.delete("/api/tasks/cancel/test-task-123")
            
            assert response.status_code == 200
            data = response.json()
            assert "cancelled successfully" in data["message"]
            
            mock_manager.cancel_task.assert_called_once_with("test-task-123")
    
    def test_cancel_task_not_found(self):
        """Test task cancellation for non-existent task."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.cancel_task.return_value = False
            
            response = self.client.delete("/api/tasks/cancel/non-existent-task")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_get_active_tasks(self):
        """Test getting active tasks."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.get_active_tasks.return_value = [
                {
                    "task_id": "task-1",
                    "status": "PROGRESS",
                    "checked_at": datetime.now().isoformat()
                },
                {
                    "task_id": "task-2",
                    "status": "SUCCESS",
                    "checked_at": datetime.now().isoformat()
                }
            ]
            
            response = self.client.get("/api/tasks/active")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all("task_id" in task for task in data)
    
    def test_cleanup_completed_tasks(self):
        """Test cleanup of completed tasks."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.cleanup_completed_tasks.return_value = 5
            
            response = self.client.post("/api/tasks/cleanup?max_age_hours=24")
            
            assert response.status_code == 200
            data = response.json()
            assert data["cleaned_count"] == 5
            assert "Cleaned up 5 completed tasks" in data["message"]
    
    def test_get_queue_info(self):
        """Test getting queue information."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.get_queue_info.return_value = {
                "active_tasks": {"worker1": []},
                "scheduled_tasks": {"worker1": []},
                "reserved_tasks": {"worker1": []},
                "stats": {"worker1": {"total": 0}},
                "registered_tasks": ["crawl_task", "crawl_url_batch"],
                "checked_at": datetime.now().isoformat()
            }
            
            response = self.client.get("/api/tasks/queue-info")
            
            assert response.status_code == 200
            data = response.json()
            assert "active_tasks" in data
            assert "registered_tasks" in data
            assert len(data["registered_tasks"]) == 2
    
    def test_health_check_healthy(self):
        """Test health check when system is healthy."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.get_queue_info.return_value = {
                "active_tasks": {"worker1": []},
                "checked_at": datetime.now().isoformat()
            }
            
            response = self.client.get("/api/tasks/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["queue_accessible"] is True
    
    def test_health_check_unhealthy(self):
        """Test health check when system is unhealthy."""
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.get_queue_info.side_effect = Exception("Redis connection failed")
            
            response = self.client.get("/api/tasks/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "health check failed" in data["message"]


class TestCrawlerAPI:
    """Test Crawler API endpoints."""
    
    def setup_method(self):
        """Setup test environment."""
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(crawler_router)
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_direct_crawl_success(self):
        """Test successful direct crawling."""
        with patch('src.financial_data_collector.api.crawler_api.WebCrawler') as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler_class.return_value = mock_crawler
            mock_crawler.collect_data.return_value = {
                "success": True,
                "title": "Test Page",
                "content": "Test content"
            }
            
            response = self.client.post("/api/crawler/crawl", json={
                "url": "https://httpbin.org/html",
                "config": {"extraction_strategy": "css"},
                "crawler_type": "web",
                "timeout": 60
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["url"] == "https://httpbin.org/html"
            assert data["crawler_type"] == "web"
            assert "execution_time_seconds" in data
            assert "completed_at" in data
            
            # Verify crawler was used correctly
            mock_crawler.initialize.assert_called_once()
            mock_crawler.start.assert_called_once()
            mock_crawler.collect_data.assert_called_once()
            mock_crawler.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_direct_crawl_enhanced(self):
        """Test direct crawling with enhanced crawler."""
        with patch('src.financial_data_collector.api.crawler_api.EnhancedWebCrawler') as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler_class.return_value = mock_crawler
            mock_crawler.crawl_url_enhanced.return_value = {
                "success": True,
                "enhanced_data": "Enhanced content"
            }
            
            response = self.client.post("/api/crawler/crawl", json={
                "url": "https://httpbin.org/html",
                "config": {"extraction_strategy": "llm"},
                "crawler_type": "enhanced",
                "timeout": 120
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["crawler_type"] == "enhanced"
            
            # Verify enhanced crawler was used
            mock_crawler.crawl_url_enhanced.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_direct_crawl_failure(self):
        """Test direct crawling failure."""
        with patch('src.financial_data_collector.api.crawler_api.WebCrawler') as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler_class.return_value = mock_crawler
            mock_crawler.collect_data.side_effect = Exception("Network timeout")
            
            response = self.client.post("/api/crawler/crawl", json={
                "url": "https://invalid-url-that-fails.com",
                "config": {"extraction_strategy": "css"},
                "crawler_type": "web",
                "timeout": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Network timeout" in data["error"]
            assert data["url"] == "https://invalid-url-that-fails.com"
            assert "execution_time_seconds" in data
    
    def test_direct_crawl_missing_url(self):
        """Test direct crawling with missing URL."""
        response = self.client.post("/api/crawler/crawl", json={
            "config": {"extraction_strategy": "css"},
            "crawler_type": "web"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_direct_crawl_invalid_crawler_type(self):
        """Test direct crawling with invalid crawler type."""
        response = self.client.post("/api/crawler/crawl", json={
            "url": "https://httpbin.org/html",
            "config": {"extraction_strategy": "css"},
            "crawler_type": "invalid_type"
        })
        
        # Should still work as it falls back to WebCrawler
        assert response.status_code == 200
    
    def test_crawler_health_check_healthy(self):
        """Test crawler health check when healthy."""
        with patch('src.financial_data_collector.api.crawler_api.WebCrawler') as mock_crawler_class:
            mock_crawler = Mock()
            mock_crawler_class.return_value = mock_crawler
            
            response = self.client.get("/api/crawler/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "Crawler API is operational" in data["message"]
            assert "crawler_types" in data
            assert "web" in data["crawler_types"]
            assert "enhanced" in data["crawler_types"]
    
    def test_crawler_health_check_unhealthy(self):
        """Test crawler health check when unhealthy."""
        with patch('src.financial_data_collector.api.crawler_api.WebCrawler') as mock_crawler_class:
            mock_crawler_class.side_effect = Exception("Crawler initialization failed")
            
            response = self.client.get("/api/crawler/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "health check failed" in data["message"]


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""
    
    def setup_method(self):
        """Setup test environment."""
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(task_router)
        self.app.include_router(crawler_router)
        self.client = TestClient(self.app)
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON requests."""
        response = self.client.post(
            "/api/tasks/crawl",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self):
        """Test handling of requests without content type."""
        response = self.client.post("/api/tasks/crawl", json={
            "url": "https://httpbin.org/html"
        })
        
        # Should still work as FastAPI handles JSON automatically
        assert response.status_code in [200, 400, 422]
    
    def test_very_large_request(self):
        """Test handling of very large requests."""
        large_urls = [f"https://httpbin.org/html?test={i}" for i in range(1000)]
        
        response = self.client.post("/api/tasks/batch-crawl", json={
            "urls": large_urls,
            "config": {"extraction_strategy": "css"},
            "crawler_type": "web",
            "priority": "normal"
        })
        
        # Should handle large requests gracefully
        assert response.status_code in [200, 400, 422, 413]
    
    def test_malformed_url(self):
        """Test handling of malformed URLs."""
        response = self.client.post("/api/tasks/crawl", json={
            "url": "not-a-valid-url",
            "config": {"extraction_strategy": "css"},
            "crawler_type": "web",
            "priority": "normal"
        })
        
        # Should accept the request (validation happens in crawler)
        assert response.status_code == 200
    
    def test_unicode_url(self):
        """Test handling of Unicode URLs."""
        response = self.client.post("/api/tasks/crawl", json={
            "url": "https://example.com/测试",
            "config": {"extraction_strategy": "css"},
            "crawler_type": "web",
            "priority": "normal"
        })
        
        assert response.status_code == 200


class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def setup_method(self):
        """Setup test environment."""
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(task_router)
        self.app.include_router(crawler_router)
        self.client = TestClient(self.app)
    
    def test_task_submission_performance(self):
        """Test task submission API performance."""
        import time
        
        with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
            mock_manager.submit_crawl_task.return_value = "perf-test-123"
            
            start_time = time.time()
            
            # Submit multiple tasks
            for i in range(10):
                response = self.client.post("/api/tasks/crawl", json={
                    "url": f"https://httpbin.org/html?test={i}",
                    "config": {"extraction_strategy": "css"},
                    "crawler_type": "web",
                    "priority": "normal"
                })
                assert response.status_code == 200
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should be fast (under 2 seconds for 10 requests)
            assert total_time < 2.0
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            with patch('src.financial_data_collector.api.task_api.task_manager') as mock_manager:
                mock_manager.submit_crawl_task.return_value = f"concurrent-test-{threading.current_thread().ident}"
                
                response = self.client.post("/api/tasks/crawl", json={
                    "url": "https://httpbin.org/html",
                    "config": {"extraction_strategy": "css"},
                    "crawler_type": "web",
                    "priority": "normal"
                })
                
                results.append(response.status_code)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])


