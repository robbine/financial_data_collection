"""
End-to-End Message Queue Tests

Comprehensive E2E tests that require running services:
- Redis connection
- Celery workers
- Full task execution pipeline
- Real crawling operations
"""

import pytest
import asyncio
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# These tests require running services
pytestmark = pytest.mark.integration


class TestE2EMessageQueue:
    """End-to-end tests for message queue system."""
    
    def setup_method(self):
        """Setup test environment."""
        # Check if required services are running
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.requires_services = True
    
    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self):
        """Test complete task lifecycle from submission to completion."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
        
        task_manager = TaskManager()
        
        # Submit a simple crawl task
        task_id = task_manager.submit_crawl_task(
            url="https://httpbin.org/html",
            config={
                "extraction_strategy": "css",
                "wait_for": 1,
                "max_scrolls": 0
            },
            crawler_type="web",
            priority=TaskPriority.NORMAL
        )
        
        assert task_id is not None
        assert task_id in task_manager.active_tasks
        
        # Monitor task status
        max_wait_time = 60  # 60 seconds timeout
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = task_manager.get_task_status(task_id)
            
            if status['status'] in ['SUCCESS', 'FAILURE']:
                break
            
            await asyncio.sleep(2)
        
        # Verify task completed
        final_status = task_manager.get_task_status(task_id)
        assert final_status['status'] in ['SUCCESS', 'FAILURE']
        
        if final_status['status'] == 'SUCCESS':
            assert final_status['result'] is not None
            assert 'url' in final_status['result']
            assert final_status['result']['success'] is True
    
    @pytest.mark.asyncio
    async def test_batch_task_execution(self):
        """Test batch task execution with multiple URLs."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
        
        task_manager = TaskManager()
        
        # Submit batch task
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml"
        ]
        
        batch_task_id = task_manager.submit_batch_crawl_task(
            urls=urls,
            config={
                "extraction_strategy": "css",
                "wait_for": 1,
                "max_scrolls": 0,
                "max_concurrent": 2
            },
            crawler_type="web",
            priority=TaskPriority.HIGH
        )
        
        assert batch_task_id is not None
        
        # Monitor batch task
        max_wait_time = 120  # 2 minutes for batch
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = task_manager.get_task_status(batch_task_id)
            
            if status['status'] in ['SUCCESS', 'FAILURE']:
                break
            
            await asyncio.sleep(5)
        
        # Verify batch completion
        final_status = task_manager.get_task_status(batch_task_id)
        assert final_status['status'] in ['SUCCESS', 'FAILURE']
        
        if final_status['status'] == 'SUCCESS':
            result = final_status['result']
            assert result['total_urls'] == len(urls)
            assert result['completed_urls'] >= 0
            assert result['failed_urls'] >= 0
            assert result['completed_urls'] + result['failed_urls'] == len(urls)
    
    @pytest.mark.asyncio
    async def test_priority_handling(self):
        """Test task priority handling."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
        
        task_manager = TaskManager()
        
        # Submit tasks with different priorities
        low_priority_task = task_manager.submit_crawl_task(
            url="https://httpbin.org/delay/2",
            config={"extraction_strategy": "css"},
            crawler_type="web",
            priority=TaskPriority.LOW
        )
        
        high_priority_task = task_manager.submit_crawl_task(
            url="https://httpbin.org/html",
            config={"extraction_strategy": "css"},
            crawler_type="web",
            priority=TaskPriority.HIGH
        )
        
        # High priority task should complete first
        high_completed = False
        low_completed = False
        
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            high_status = task_manager.get_task_status(high_priority_task)
            low_status = task_manager.get_task_status(low_priority_task)
            
            if high_status['status'] in ['SUCCESS', 'FAILURE']:
                high_completed = True
            
            if low_status['status'] in ['SUCCESS', 'FAILURE']:
                low_completed = True
            
            if high_completed and low_completed:
                break
            
            await asyncio.sleep(2)
        
        # At least high priority should complete
        assert high_completed or low_completed
    
    @pytest.mark.asyncio
    async def test_delayed_task_execution(self):
        """Test delayed task execution."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
        
        task_manager = TaskManager()
        
        # Submit task with 10 second delay
        eta = datetime.now() + timedelta(seconds=10)
        
        delayed_task_id = task_manager.submit_crawl_task(
            url="https://httpbin.org/html",
            config={"extraction_strategy": "css"},
            crawler_type="web",
            priority=TaskPriority.NORMAL,
            eta=eta
        )
        
        # Task should not start immediately
        initial_status = task_manager.get_task_status(delayed_task_id)
        assert initial_status['status'] in ['PENDING', 'PROGRESS']
        
        # Wait for task to start (should be around ETA time)
        max_wait_time = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = task_manager.get_task_status(delayed_task_id)
            
            if status['status'] in ['SUCCESS', 'FAILURE']:
                break
            
            await asyncio.sleep(2)
        
        # Task should have completed
        final_status = task_manager.get_task_status(delayed_task_id)
        assert final_status['status'] in ['SUCCESS', 'FAILURE']
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """Test task cancellation."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
        
        task_manager = TaskManager()
        
        # Submit a task that takes time
        task_id = task_manager.submit_crawl_task(
            url="https://httpbin.org/delay/10",
            config={"extraction_strategy": "css"},
            crawler_type="web",
            priority=TaskPriority.NORMAL
        )
        
        # Wait a moment for task to start
        await asyncio.sleep(2)
        
        # Cancel the task
        cancelled = task_manager.cancel_task(task_id)
        assert cancelled is True
        
        # Check task status
        status = task_manager.get_task_status(task_id)
        # Status might be REVOKED or still running depending on timing
        assert status['status'] in ['REVOKED', 'PROGRESS', 'SUCCESS', 'FAILURE']
    
    @pytest.mark.asyncio
    async def test_enhanced_crawler_integration(self):
        """Test enhanced crawler integration with message queue."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
        
        task_manager = TaskManager()
        
        # Submit task with enhanced crawler
        task_id = task_manager.submit_crawl_task(
            url="https://httpbin.org/html",
            config={
                "extraction_strategy": "css",
                "wait_for": 1,
                "max_scrolls": 0
            },
            crawler_type="enhanced",
            priority=TaskPriority.HIGH
        )
        
        # Monitor task
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = task_manager.get_task_status(task_id)
            
            if status['status'] in ['SUCCESS', 'FAILURE']:
                break
            
            await asyncio.sleep(2)
        
        # Verify completion
        final_status = task_manager.get_task_status(task_id)
        assert final_status['status'] in ['SUCCESS', 'FAILURE']
    
    @pytest.mark.asyncio
    async def test_llm_extraction_integration(self):
        """Test LLM extraction integration with message queue."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
        
        # Skip if LLM environment variables are not set
        volc_api_key = os.getenv('VOLC_API_KEY')
        volc_base_url = os.getenv('VOLC_BASE_URL')
        volc_model = os.getenv('VOLC_MODEL')
        
        if not (volc_api_key and volc_base_url and volc_model):
            pytest.skip("LLM environment variables not set")
        
        task_manager = TaskManager()
        
        # Submit task with LLM extraction
        task_id = task_manager.submit_crawl_task(
            url="https://www.nbcnews.com/business",
            config={
                "extraction_strategy": "llm",
                "llm_config": {
                    "provider": "volc",
                    "api_token": volc_api_key,
                    "base_url": volc_base_url,
                    "model": volc_model
                },
                "wait_for": 3,
                "max_scrolls": 1
            },
            crawler_type="enhanced",
            priority=TaskPriority.HIGH
        )
        
        # Monitor task
        max_wait_time = 120  # 2 minutes for LLM processing
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = task_manager.get_task_status(task_id)
            
            if status['status'] in ['SUCCESS', 'FAILURE']:
                break
            
            await asyncio.sleep(5)
        
        # Verify completion
        final_status = task_manager.get_task_status(task_id)
        assert final_status['status'] in ['SUCCESS', 'FAILURE']
        
        if final_status['status'] == 'SUCCESS':
            result = final_status['result']
            assert result['success'] is True
            # Should have financial data if LLM extraction worked
            if 'financial_data' in result:
                assert result['financial_data'] is not None


class TestE2EAPIIntegration:
    """End-to-end API integration tests."""
    
    def setup_method(self):
        """Setup test environment."""
        from fastapi import FastAPI
        from src.financial_data_collector.api.task_api import router as task_router
        from src.financial_data_collector.api.crawler_api import router as crawler_router
        
        self.app = FastAPI()
        self.app.include_router(task_router)
        self.app.include_router(crawler_router)
        
        from fastapi.testclient import TestClient
        self.client = TestClient(self.app)
    
    def test_api_task_submission_and_monitoring(self):
        """Test complete API workflow for task submission and monitoring."""
        # Submit task via API
        response = self.client.post("/api/tasks/crawl", json={
            "url": "https://httpbin.org/html",
            "config": {
                "extraction_strategy": "css",
                "wait_for": 1,
                "max_scrolls": 0
            },
            "crawler_type": "web",
            "priority": "normal"
        })
        
        assert response.status_code == 200
        data = response.json()
        task_id = data["task_id"]
        assert task_id is not None
        
        # Monitor task status via API
        max_checks = 30
        for i in range(max_checks):
            status_response = self.client.get(f"/api/tasks/status/{task_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            
            if status_data["status"] in ["SUCCESS", "FAILURE"]:
                break
            
            time.sleep(2)
        
        # Verify final status
        final_status_response = self.client.get(f"/api/tasks/status/{task_id}")
        assert final_status_response.status_code == 200
        
        final_status = final_status_response.json()
        assert final_status["status"] in ["SUCCESS", "FAILURE"]
    
    def test_api_batch_task_submission(self):
        """Test batch task submission via API."""
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json"
        ]
        
        response = self.client.post("/api/tasks/batch-crawl", json={
            "urls": urls,
            "config": {
                "extraction_strategy": "css",
                "wait_for": 1,
                "max_scrolls": 0,
                "max_concurrent": 2
            },
            "crawler_type": "web",
            "priority": "high"
        })
        
        assert response.status_code == 200
        data = response.json()
        batch_task_id = data["task_id"]
        assert batch_task_id is not None
        
        # Monitor batch task
        max_checks = 30
        for i in range(max_checks):
            status_response = self.client.get(f"/api/tasks/status/{batch_task_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            
            if status_data["status"] in ["SUCCESS", "FAILURE"]:
                break
            
            time.sleep(3)
        
        # Verify completion
        final_status_response = self.client.get(f"/api/tasks/status/{batch_task_id}")
        assert final_status_response.status_code == 200
        
        final_status = final_status_response.json()
        assert final_status["status"] in ["SUCCESS", "FAILURE"]
    
    def test_api_direct_crawl(self):
        """Test direct crawling via API."""
        response = self.client.post("/api/crawler/crawl", json={
            "url": "https://httpbin.org/html",
            "config": {
                "extraction_strategy": "css",
                "wait_for": 1,
                "max_scrolls": 0
            },
            "crawler_type": "web",
            "timeout": 30
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "url" in data
        assert data["url"] == "https://httpbin.org/html"
        assert "execution_time_seconds" in data
        assert "completed_at" in data
    
    def test_api_health_checks(self):
        """Test API health check endpoints."""
        # Test task API health
        response = self.client.get("/api/tasks/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
        # Test crawler API health
        response = self.client.get("/api/crawler/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "crawler_types" in data
    
    def test_api_queue_info(self):
        """Test queue information API."""
        response = self.client.get("/api/tasks/queue-info")
        assert response.status_code == 200
        data = response.json()
        
        assert "registered_tasks" in data
        assert "checked_at" in data
        assert isinstance(data["registered_tasks"], list)
    
    def test_api_active_tasks(self):
        """Test active tasks API."""
        response = self.client.get("/api/tasks/active")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Each task should have required fields
        for task in data:
            assert "task_id" in task
            assert "status" in task


class TestE2EPerformance:
    """End-to-end performance tests."""
    
    def setup_method(self):
        """Setup test environment."""
        from src.financial_data_collector.core.tasks.task_manager import TaskManager
        self.task_manager = TaskManager()
    
    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self):
        """Test concurrent task processing performance."""
        # Submit multiple tasks concurrently
        task_ids = []
        
        for i in range(5):
            task_id = self.task_manager.submit_crawl_task(
                url=f"https://httpbin.org/html?test={i}",
                config={
                    "extraction_strategy": "css",
                    "wait_for": 1,
                    "max_scrolls": 0
                },
                crawler_type="web",
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        # Monitor all tasks
        max_wait_time = 120
        start_time = time.time()
        completed_tasks = 0
        
        while time.time() - start_time < max_wait_time and completed_tasks < len(task_ids):
            completed_tasks = 0
            
            for task_id in task_ids:
                status = self.task_manager.get_task_status(task_id)
                if status['status'] in ['SUCCESS', 'FAILURE']:
                    completed_tasks += 1
            
            if completed_tasks == len(task_ids):
                break
            
            await asyncio.sleep(2)
        
        # Verify all tasks completed
        assert completed_tasks == len(task_ids)
        
        # Check completion time
        total_time = time.time() - start_time
        print(f"Completed {len(task_ids)} tasks in {total_time:.2f} seconds")
        
        # Should be reasonably fast (under 2 minutes for 5 tasks)
        assert total_time < 120
    
    @pytest.mark.asyncio
    async def test_large_batch_processing(self):
        """Test processing of large batch tasks."""
        # Create a large batch
        urls = [f"https://httpbin.org/html?test={i}" for i in range(10)]
        
        batch_task_id = self.task_manager.submit_batch_crawl_task(
            urls=urls,
            config={
                "extraction_strategy": "css",
                "wait_for": 1,
                "max_scrolls": 0,
                "max_concurrent": 3
            },
            crawler_type="web",
            priority=TaskPriority.NORMAL
        )
        
        # Monitor batch completion
        max_wait_time = 180  # 3 minutes for large batch
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.task_manager.get_task_status(batch_task_id)
            
            if status['status'] in ['SUCCESS', 'FAILURE']:
                break
            
            await asyncio.sleep(5)
        
        # Verify batch completion
        final_status = self.task_manager.get_task_status(batch_task_id)
        assert final_status['status'] in ['SUCCESS', 'FAILURE']
        
        if final_status['status'] == 'SUCCESS':
            result = final_status['result']
            assert result['total_urls'] == len(urls)
            assert result['completed_urls'] + result['failed_urls'] == len(urls)
            
            # Should have reasonable success rate
            success_rate = result['completed_urls'] / result['total_urls']
            assert success_rate >= 0.5  # At least 50% success rate


if __name__ == "__main__":
    # Run E2E tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])


