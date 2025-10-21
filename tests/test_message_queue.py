"""
Message Queue System Tests

Comprehensive test suite for the message queue integration including:
- Task submission and execution
- Batch processing
- Priority handling
- Error handling and retries
- API integration
"""

import asyncio
import pytest
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority
from src.financial_data_collector.core.tasks.crawl_tasks import crawl_task, crawl_url_batch
from src.financial_data_collector.core.tasks.celery_app import celery_app


class TestTaskManager:
    """Test TaskManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.task_manager = TaskManager()
        self.test_url = "https://httpbin.org/html"
        self.test_config = {
            "extraction_strategy": "css",
            "wait_for": 1,
            "max_scrolls": 0
        }
    
    def test_task_manager_initialization(self):
        """Test TaskManager initialization."""
        assert self.task_manager is not None
        assert self.task_manager.celery_app == celery_app
        assert isinstance(self.task_manager.active_tasks, dict)
        assert len(self.task_manager.active_tasks) == 0
    
    def test_submit_crawl_task(self):
        """Test single crawl task submission."""
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.id = "test-task-123"
            mock_result.return_value.apply_async.return_value = mock_result.return_value
            
            task_id = self.task_manager.submit_crawl_task(
                url=self.test_url,
                config=self.test_config,
                crawler_type="web",
                priority=TaskPriority.NORMAL
            )
            
            assert task_id == "test-task-123"
            assert task_id in self.task_manager.active_tasks
            assert self.task_manager.active_tasks[task_id]['type'] == 'single_crawl'
            assert self.task_manager.active_tasks[task_id]['url'] == self.test_url
    
    def test_submit_batch_crawl_task(self):
        """Test batch crawl task submission."""
        urls = [self.test_url, "https://httpbin.org/json"]
        
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.id = "batch-task-456"
            mock_result.return_value.apply_async.return_value = mock_result.return_value
            
            task_id = self.task_manager.submit_batch_crawl_task(
                urls=urls,
                config=self.test_config,
                crawler_type="web",
                priority=TaskPriority.HIGH
            )
            
            assert task_id == "batch-task-456"
            assert task_id in self.task_manager.active_tasks
            assert self.task_manager.active_tasks[task_id]['type'] == 'batch_crawl'
            assert self.task_manager.active_tasks[task_id]['url_count'] == len(urls)
    
    def test_submit_delayed_task(self):
        """Test delayed task submission."""
        eta = datetime.now() + timedelta(minutes=5)
        
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.id = "delayed-task-789"
            mock_result.return_value.apply_async.return_value = mock_result.return_value
            
            task_id = self.task_manager.submit_crawl_task(
                url=self.test_url,
                config=self.test_config,
                crawler_type="web",
                priority=TaskPriority.LOW,
                eta=eta
            )
            
            assert task_id == "delayed-task-789"
            # Verify apply_async was called with eta
            mock_result.return_value.apply_async.assert_called_once()
            call_kwargs = mock_result.return_value.apply_async.call_args[1]
            assert 'eta' in call_kwargs
    
    def test_get_task_status(self):
        """Test task status retrieval."""
        task_id = "test-task-123"
        
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.status = "SUCCESS"
            mock_result.return_value.ready.return_value = True
            mock_result.return_value.result = {"success": True, "data": "test"}
            mock_result.return_value.info = {"progress": 100}
            
            # Add task to active tasks
            self.task_manager.active_tasks[task_id] = {
                'type': 'single_crawl',
                'url': self.test_url,
                'submitted_at': datetime.now()
            }
            
            status = self.task_manager.get_task_status(task_id)
            
            assert status['task_id'] == task_id
            assert status['status'] == "SUCCESS"
            assert status['result'] == {"success": True, "data": "test"}
            assert 'elapsed_seconds' in status
    
    def test_cancel_task(self):
        """Test task cancellation."""
        task_id = "test-task-123"
        
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.revoke.return_value = True
            
            # Add task to active tasks
            self.task_manager.active_tasks[task_id] = {
                'type': 'single_crawl',
                'url': self.test_url,
                'submitted_at': datetime.now()
            }
            
            success = self.task_manager.cancel_task(task_id)
            
            assert success is True
            mock_result.return_value.revoke.assert_called_once_with(terminate=True)
    
    def test_get_active_tasks(self):
        """Test getting active tasks."""
        # Add some test tasks
        self.task_manager.active_tasks["task-1"] = {
            'type': 'single_crawl',
            'url': self.test_url,
            'submitted_at': datetime.now()
        }
        self.task_manager.active_tasks["task-2"] = {
            'type': 'batch_crawl',
            'urls': [self.test_url],
            'submitted_at': datetime.now()
        }
        
        with patch.object(self.task_manager, 'get_task_status') as mock_status:
            mock_status.return_value = {
                'task_id': 'task-1',
                'status': 'SUCCESS',
                'checked_at': datetime.now().isoformat()
            }
            
            active_tasks = self.task_manager.get_active_tasks()
            
            assert len(active_tasks) == 2
            assert all('task_id' in task for task in active_tasks)
    
    def test_cleanup_completed_tasks(self):
        """Test cleanup of completed tasks."""
        # Add old completed task
        old_time = datetime.now() - timedelta(hours=25)
        self.task_manager.active_tasks["old-task"] = {
            'type': 'single_crawl',
            'url': self.test_url,
            'submitted_at': old_time
        }
        
        # Add recent task
        recent_time = datetime.now() - timedelta(hours=1)
        self.task_manager.active_tasks["recent-task"] = {
            'type': 'single_crawl',
            'url': self.test_url,
            'submitted_at': recent_time
        }
        
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            # Old task is completed
            mock_result.return_value.ready.return_value = True
            
            cleaned_count = self.task_manager.cleanup_completed_tasks(max_age_hours=24)
            
            assert cleaned_count == 1
            assert "old-task" not in self.task_manager.active_tasks
            assert "recent-task" in self.task_manager.active_tasks
    
    def test_get_queue_info(self):
        """Test queue information retrieval."""
        with patch.object(self.task_manager.celery_app.control, 'inspect') as mock_inspect:
            mock_inspect.return_value.active.return_value = {"worker1": []}
            mock_inspect.return_value.scheduled.return_value = {"worker1": []}
            mock_inspect.return_value.reserved.return_value = {"worker1": []}
            mock_inspect.return_value.stats.return_value = {"worker1": {"total": 0}}
            
            queue_info = self.task_manager.get_queue_info()
            
            assert 'active_tasks' in queue_info
            assert 'scheduled_tasks' in queue_info
            assert 'reserved_tasks' in queue_info
            assert 'stats' in queue_info
            assert 'registered_tasks' in queue_info
    
    def test_priority_conversion(self):
        """Test priority enum to Celery priority conversion."""
        assert self.task_manager._get_celery_priority(TaskPriority.LOW) == 1
        assert self.task_manager._get_celery_priority(TaskPriority.NORMAL) == 5
        assert self.task_manager._get_celery_priority(TaskPriority.HIGH) == 7
        assert self.task_manager._get_celery_priority(TaskPriority.URGENT) == 9


class TestCeleryTasks:
    """Test Celery task functions."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_url = "https://httpbin.org/html"
        self.test_config = {
            "extraction_strategy": "css",
            "wait_for": 1,
            "max_scrolls": 0
        }
    
    @pytest.mark.asyncio
    async def test_crawl_task_success(self):
        """Test successful crawl task execution."""
        with patch('src.financial_data_collector.core.tasks.crawl_tasks.asyncio.run') as mock_run:
            mock_run.return_value = {
                'task_id': 'test-123',
                'url': self.test_url,
                'success': True,
                'result': {'title': 'Test Page', 'content': 'Test content'}
            }
            
            # Mock the task context
            mock_task = Mock()
            mock_task.request.id = "test-123"
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            mock_task.update_state = Mock()
            
            result = crawl_task(
                self.test_url,
                self.test_config,
                "web",
                "normal"
            )
            
            assert result['task_id'] == 'test-123'
            assert result['success'] is True
            assert result['url'] == self.test_url
    
    @pytest.mark.asyncio
    async def test_crawl_task_failure_with_retry(self):
        """Test crawl task failure with retry."""
        with patch('src.financial_data_collector.core.tasks.crawl_tasks.asyncio.run') as mock_run:
            mock_run.side_effect = Exception("Network error")
            
            # Mock the task context
            mock_task = Mock()
            mock_task.request.id = "test-123"
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            mock_task.update_state = Mock()
            mock_task.retry = Mock(side_effect=Exception("Retry called"))
            
            with pytest.raises(Exception, match="Retry called"):
                crawl_task(
                    self.test_url,
                    self.test_config,
                    "web",
                    "normal"
                )
    
    def test_crawl_url_batch_sequential(self):
        """Test batch crawl with sequential processing."""
        urls = [self.test_url, "https://httpbin.org/json"]
        config = {**self.test_config, "max_concurrent": 1}
        
        with patch('src.financial_data_collector.core.tasks.crawl_tasks.crawl_task.apply_async') as mock_apply:
            mock_result = Mock()
            mock_result.get.return_value = {
                'task_id': 'subtask-1',
                'success': True,
                'result': {'title': 'Test Page 1'}
            }
            mock_apply.return_value = mock_result
            
            # Mock the task context
            mock_task = Mock()
            mock_task.request.id = "batch-123"
            mock_task.update_state = Mock()
            
            result = crawl_url_batch(
                urls,
                config,
                "web",
                "normal"
            )
            
            assert result['task_id'] == "batch-123"
            assert result['batch_type'] == 'sequential'
            assert result['total_urls'] == len(urls)
            assert result['completed_urls'] == len(urls)
    
    def test_crawl_url_batch_parallel(self):
        """Test batch crawl with parallel processing."""
        urls = [self.test_url, "https://httpbin.org/json"]
        config = {**self.test_config, "max_concurrent": 2}
        
        with patch('src.financial_data_collector.core.tasks.crawl_tasks.crawl_task.apply_async') as mock_apply:
            mock_result = Mock()
            mock_result.id = "subtask-1"
            mock_apply.return_value = mock_result
            
            # Mock the task context
            mock_task = Mock()
            mock_task.request.id = "batch-123"
            mock_task.update_state = Mock()
            
            result = crawl_url_batch(
                urls,
                config,
                "web",
                "normal"
            )
            
            assert result['task_id'] == "batch-123"
            assert result['batch_type'] == 'parallel'
            assert result['total_urls'] == len(urls)
            # Should have submitted all URLs
            assert mock_apply.call_count == len(urls)
    
    def test_scheduled_crawl(self):
        """Test scheduled crawl task."""
        result = crawl_task.scheduled_crawl()
        
        assert 'scheduled_at' in result
        assert 'status' in result
        assert result['status'] == 'completed'
    
    def test_health_check(self):
        """Test health check task."""
        result = crawl_task.health_check()
        
        assert 'timestamp' in result
        assert 'status' in result
        assert result['status'] == 'healthy'
        assert 'components' in result


class TestMessageQueueIntegration:
    """Integration tests for message queue system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.task_manager = TaskManager()
    
    @pytest.mark.asyncio
    async def test_end_to_end_task_flow(self):
        """Test complete task flow from submission to completion."""
        # This test would require a running Redis instance
        # For now, we'll mock the Celery interactions
        
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            # Mock successful task execution
            mock_result.return_value.id = "integration-test-123"
            mock_result.return_value.apply_async.return_value = mock_result.return_value
            mock_result.return_value.status = "SUCCESS"
            mock_result.return_value.ready.return_value = True
            mock_result.return_value.result = {
                'success': True,
                'data': 'Integration test data'
            }
            
            # Submit task
            task_id = self.task_manager.submit_crawl_task(
                url="https://httpbin.org/html",
                config={"extraction_strategy": "css"},
                crawler_type="web",
                priority=TaskPriority.NORMAL
            )
            
            assert task_id == "integration-test-123"
            
            # Check status
            status = self.task_manager.get_task_status(task_id)
            assert status['status'] == "SUCCESS"
            assert status['result']['success'] is True
    
    def test_priority_handling(self):
        """Test task priority handling."""
        priorities = [
            TaskPriority.LOW,
            TaskPriority.NORMAL,
            TaskPriority.HIGH,
            TaskPriority.URGENT
        ]
        
        for priority in priorities:
            celery_priority = self.task_manager._get_celery_priority(priority)
            assert isinstance(celery_priority, int)
            assert 1 <= celery_priority <= 9
    
    def test_error_handling(self):
        """Test error handling in task operations."""
        # Test invalid task ID
        status = self.task_manager.get_task_status("invalid-task-id")
        assert status['status'] == 'UNKNOWN'
        assert 'error' in status
        
        # Test cancellation of non-existent task
        success = self.task_manager.cancel_task("non-existent-task")
        assert success is False


class TestPerformance:
    """Performance tests for message queue system."""
    
    def test_task_submission_performance(self):
        """Test task submission performance."""
        task_manager = TaskManager()
        
        with patch.object(task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.id = "perf-test-{i}"
            mock_result.return_value.apply_async.return_value = mock_result.return_value
            
            start_time = time.time()
            
            # Submit multiple tasks
            task_ids = []
            for i in range(10):
                task_id = task_manager.submit_crawl_task(
                    url=f"https://httpbin.org/html?test={i}",
                    config={"extraction_strategy": "css"},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
            
            end_time = time.time()
            submission_time = end_time - start_time
            
            # Should be fast (under 1 second for 10 tasks)
            assert submission_time < 1.0
            assert len(task_ids) == 10
            assert len(task_manager.active_tasks) == 10
    
    def test_batch_task_performance(self):
        """Test batch task performance."""
        task_manager = TaskManager()
        urls = [f"https://httpbin.org/html?test={i}" for i in range(20)]
        
        with patch.object(task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.id = "batch-perf-test"
            mock_result.return_value.apply_async.return_value = mock_result.return_value
            
            start_time = time.time()
            
            task_id = task_manager.submit_batch_crawl_task(
                urls=urls,
                config={"extraction_strategy": "css", "max_concurrent": 5},
                crawler_type="web",
                priority=TaskPriority.NORMAL
            )
            
            end_time = time.time()
            submission_time = end_time - start_time
            
            # Should be fast even for large batches
            assert submission_time < 2.0
            assert task_id == "batch-perf-test"
            assert task_manager.active_tasks[task_id]['url_count'] == len(urls)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])


