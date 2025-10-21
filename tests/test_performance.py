"""
Performance Tests for Message Queue System

Comprehensive performance testing including:
- Load testing
- Stress testing
- Memory usage monitoring
- Throughput measurement
- Latency analysis
"""

import pytest
import asyncio
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority


class TestLoadPerformance:
    """Load testing for message queue system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.task_manager = TaskManager()
        self.test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
            "https://httpbin.org/robots.txt"
        ]
    
    def test_single_task_submission_performance(self):
        """Test performance of single task submissions."""
        submission_times = []
        
        for i in range(20):
            start_time = time.time()
            
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"perf-test-{i}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_crawl_task(
                    url=f"https://httpbin.org/html?test={i}",
                    config={"extraction_strategy": "css"},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                
                end_time = time.time()
                submission_times.append(end_time - start_time)
        
        # Analyze performance
        avg_time = statistics.mean(submission_times)
        max_time = max(submission_times)
        min_time = min(submission_times)
        
        print(f"Single task submission performance:")
        print(f"  Average: {avg_time:.4f}s")
        print(f"  Min: {min_time:.4f}s")
        print(f"  Max: {max_time:.4f}s")
        
        # Should be fast (under 0.1s per submission)
        assert avg_time < 0.1
        assert max_time < 0.2
    
    def test_batch_task_submission_performance(self):
        """Test performance of batch task submissions."""
        batch_sizes = [5, 10, 20, 50]
        batch_times = []
        
        for batch_size in batch_sizes:
            urls = [f"https://httpbin.org/html?test={i}" for i in range(batch_size)]
            
            start_time = time.time()
            
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"batch-perf-{batch_size}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_batch_crawl_task(
                    urls=urls,
                    config={"extraction_strategy": "css", "max_concurrent": 3},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                
                end_time = time.time()
                batch_times.append(end_time - start_time)
        
        # Analyze performance
        print(f"Batch task submission performance:")
        for i, batch_size in enumerate(batch_sizes):
            print(f"  Batch size {batch_size}: {batch_times[i]:.4f}s")
        
        # Batch submissions should be reasonably fast
        assert all(time < 1.0 for time in batch_times)
    
    def test_concurrent_submission_performance(self):
        """Test performance under concurrent submissions."""
        num_threads = 10
        tasks_per_thread = 5
        results = []
        
        def submit_tasks(thread_id):
            thread_results = []
            
            for i in range(tasks_per_thread):
                start_time = time.time()
                
                with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                    mock_result.return_value.id = f"concurrent-{thread_id}-{i}"
                    mock_result.return_value.apply_async.return_value = mock_result.return_value
                    
                    task_id = self.task_manager.submit_crawl_task(
                        url=f"https://httpbin.org/html?thread={thread_id}&task={i}",
                        config={"extraction_strategy": "css"},
                        crawler_type="web",
                        priority=TaskPriority.NORMAL
                    )
                    
                    end_time = time.time()
                    thread_results.append(end_time - start_time)
            
            return thread_results
        
        # Run concurrent submissions
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(submit_tasks, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        # Analyze performance
        avg_time = statistics.mean(results)
        max_time = max(results)
        min_time = min(results)
        
        print(f"Concurrent submission performance ({num_threads} threads, {tasks_per_thread} tasks each):")
        print(f"  Total tasks: {len(results)}")
        print(f"  Average: {avg_time:.4f}s")
        print(f"  Min: {min_time:.4f}s")
        print(f"  Max: {max_time:.4f}s")
        
        # Should handle concurrency well
        assert avg_time < 0.2
        assert max_time < 0.5
    
    def test_priority_queue_performance(self):
        """Test performance with different priority levels."""
        priorities = [TaskPriority.LOW, TaskPriority.NORMAL, TaskPriority.HIGH, TaskPriority.URGENT]
        priority_times = {}
        
        for priority in priorities:
            times = []
            
            for i in range(10):
                start_time = time.time()
                
                with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                    mock_result.return_value.id = f"priority-{priority.value}-{i}"
                    mock_result.return_value.apply_async.return_value = mock_result.return_value
                    
                    task_id = self.task_manager.submit_crawl_task(
                        url=f"https://httpbin.org/html?priority={priority.value}&test={i}",
                        config={"extraction_strategy": "css"},
                        crawler_type="web",
                        priority=priority
                    )
                    
                    end_time = time.time()
                    times.append(end_time - start_time)
                
                priority_times[priority.value] = statistics.mean(times)
        
        print(f"Priority queue performance:")
        for priority, avg_time in priority_times.items():
            print(f"  {priority}: {avg_time:.4f}s")
        
        # All priorities should be fast
        assert all(time < 0.1 for time in priority_times.values())


class TestMemoryPerformance:
    """Memory usage testing for message queue system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.task_manager = TaskManager()
        self.process = psutil.Process()
    
    def test_memory_usage_with_many_tasks(self):
        """Test memory usage with many active tasks."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many tasks
        task_ids = []
        for i in range(100):
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"memory-test-{i}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_crawl_task(
                    url=f"https://httpbin.org/html?test={i}",
                    config={"extraction_strategy": "css"},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
        
        peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"Memory usage with {len(task_ids)} tasks:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Peak: {peak_memory:.2f} MB")
        print(f"  Increase: {memory_increase:.2f} MB")
        
        # Memory increase should be reasonable (under 50MB for 100 tasks)
        assert memory_increase < 50
        
        # Cleanup
        self.task_manager.active_tasks.clear()
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        print(f"  After cleanup: {final_memory:.2f} MB")
    
    def test_memory_leak_prevention(self):
        """Test that memory is properly cleaned up."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and cleanup tasks multiple times
        for cycle in range(5):
            task_ids = []
            
            # Create tasks
            for i in range(20):
                with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                    mock_result.return_value.id = f"leak-test-{cycle}-{i}"
                    mock_result.return_value.apply_async.return_value = mock_result.return_value
                    
                    task_id = self.task_manager.submit_crawl_task(
                        url=f"https://httpbin.org/html?cycle={cycle}&test={i}",
                        config={"extraction_strategy": "css"},
                        crawler_type="web",
                        priority=TaskPriority.NORMAL
                    )
                    task_ids.append(task_id)
            
            # Simulate task completion and cleanup
            for task_id in task_ids:
                if task_id in self.task_manager.active_tasks:
                    del self.task_manager.active_tasks[task_id]
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory leak test:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Increase: {memory_increase:.2f} MB")
        
        # Memory increase should be minimal (under 10MB)
        assert memory_increase < 10


class TestThroughputPerformance:
    """Throughput testing for message queue system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.task_manager = TaskManager()
    
    def test_task_throughput(self):
        """Test task submission throughput."""
        num_tasks = 100
        start_time = time.time()
        
        task_ids = []
        for i in range(num_tasks):
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"throughput-test-{i}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_crawl_task(
                    url=f"https://httpbin.org/html?test={i}",
                    config={"extraction_strategy": "css"},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = num_tasks / total_time
        
        print(f"Task submission throughput:")
        print(f"  Tasks: {num_tasks}")
        print(f"  Time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} tasks/second")
        
        # Should achieve high throughput (over 100 tasks/second)
        assert throughput > 100
    
    def test_batch_throughput(self):
        """Test batch task throughput."""
        batch_sizes = [10, 25, 50, 100]
        batch_throughputs = []
        
        for batch_size in batch_sizes:
            urls = [f"https://httpbin.org/html?test={i}" for i in range(batch_size)]
            
            start_time = time.time()
            
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"batch-throughput-{batch_size}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_batch_crawl_task(
                    urls=urls,
                    config={"extraction_strategy": "css", "max_concurrent": 5},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                
                end_time = time.time()
                total_time = end_time - start_time
                throughput = batch_size / total_time
                batch_throughputs.append(throughput)
        
        print(f"Batch throughput by size:")
        for i, batch_size in enumerate(batch_sizes):
            print(f"  Batch size {batch_size}: {batch_throughputs[i]:.2f} URLs/second")
        
        # Batch throughput should be high
        assert all(throughput > 50 for throughput in batch_throughputs)
    
    def test_concurrent_throughput(self):
        """Test throughput under concurrent load."""
        num_threads = 5
        tasks_per_thread = 20
        total_tasks = num_threads * tasks_per_thread
        
        def submit_tasks(thread_id):
            thread_start = time.time()
            thread_tasks = []
            
            for i in range(tasks_per_thread):
                with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                    mock_result.return_value.id = f"concurrent-throughput-{thread_id}-{i}"
                    mock_result.return_value.apply_async.return_value = mock_result.return_value
                    
                    task_id = self.task_manager.submit_crawl_task(
                        url=f"https://httpbin.org/html?thread={thread_id}&task={i}",
                        config={"extraction_strategy": "css"},
                        crawler_type="web",
                        priority=TaskPriority.NORMAL
                    )
                    thread_tasks.append(task_id)
            
            thread_end = time.time()
            thread_time = thread_end - thread_start
            thread_throughput = tasks_per_thread / thread_time
            
            return thread_throughput, thread_tasks
        
        # Run concurrent submissions
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(submit_tasks, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        overall_throughput = total_tasks / total_time
        
        thread_throughputs = [result[0] for result in results]
        avg_thread_throughput = statistics.mean(thread_throughputs)
        
        print(f"Concurrent throughput test:")
        print(f"  Threads: {num_threads}")
        print(f"  Tasks per thread: {tasks_per_thread}")
        print(f"  Total tasks: {total_tasks}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Overall throughput: {overall_throughput:.2f} tasks/second")
        print(f"  Average thread throughput: {avg_thread_throughput:.2f} tasks/second")
        
        # Should maintain high throughput under concurrent load
        assert overall_throughput > 50
        assert avg_thread_throughput > 20


class TestLatencyPerformance:
    """Latency testing for message queue system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.task_manager = TaskManager()
    
    def test_task_submission_latency(self):
        """Test task submission latency."""
        latencies = []
        
        for i in range(50):
            start_time = time.time()
            
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"latency-test-{i}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_crawl_task(
                    url=f"https://httpbin.org/html?test={i}",
                    config={"extraction_strategy": "css"},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                
                end_time = time.time()
                latencies.append(end_time - start_time)
        
        # Analyze latency
        avg_latency = statistics.mean(latencies)
        p50_latency = statistics.median(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
        max_latency = max(latencies)
        
        print(f"Task submission latency:")
        print(f"  Average: {avg_latency*1000:.2f}ms")
        print(f"  P50: {p50_latency*1000:.2f}ms")
        print(f"  P95: {p95_latency*1000:.2f}ms")
        print(f"  P99: {p99_latency*1000:.2f}ms")
        print(f"  Max: {max_latency*1000:.2f}ms")
        
        # Latency should be low
        assert avg_latency < 0.05  # Under 50ms average
        assert p95_latency < 0.1   # Under 100ms for 95% of requests
        assert max_latency < 0.2   # Under 200ms maximum
    
    def test_status_check_latency(self):
        """Test task status check latency."""
        # Create a task first
        with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
            mock_result.return_value.id = "status-latency-test"
            mock_result.return_value.apply_async.return_value = mock_result.return_value
            
            task_id = self.task_manager.submit_crawl_task(
                url="https://httpbin.org/html",
                config={"extraction_strategy": "css"},
                crawler_type="web",
                priority=TaskPriority.NORMAL
            )
        
        # Test status check latency
        latencies = []
        
        for i in range(20):
            start_time = time.time()
            
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.status = "PROGRESS"
                mock_result.return_value.ready.return_value = False
                mock_result.return_value.result = None
                mock_result.return_value.info = {"status": "processing"}
                
                status = self.task_manager.get_task_status(task_id)
                
                end_time = time.time()
                latencies.append(end_time - start_time)
        
        # Analyze latency
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        
        print(f"Status check latency:")
        print(f"  Average: {avg_latency*1000:.2f}ms")
        print(f"  Max: {max_latency*1000:.2f}ms")
        
        # Status checks should be very fast
        assert avg_latency < 0.01  # Under 10ms average
        assert max_latency < 0.05  # Under 50ms maximum


class TestStressPerformance:
    """Stress testing for message queue system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.task_manager = TaskManager()
    
    def test_high_volume_stress(self):
        """Test system under high volume stress."""
        num_tasks = 500
        start_time = time.time()
        
        task_ids = []
        for i in range(num_tasks):
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"stress-test-{i}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_crawl_task(
                    url=f"https://httpbin.org/html?stress={i}",
                    config={"extraction_strategy": "css"},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = num_tasks / total_time
        
        print(f"High volume stress test:")
        print(f"  Tasks: {num_tasks}")
        print(f"  Time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} tasks/second")
        
        # Should handle high volume
        assert throughput > 50
        assert total_time < 30  # Should complete in under 30 seconds
    
    def test_memory_stress(self):
        """Test system under memory stress."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create many tasks to stress memory
        task_ids = []
        for i in range(200):
            with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                mock_result.return_value.id = f"memory-stress-{i}"
                mock_result.return_value.apply_async.return_value = mock_result.return_value
                
                task_id = self.task_manager.submit_crawl_task(
                    url=f"https://httpbin.org/html?memory={i}",
                    config={"extraction_strategy": "css"},
                    crawler_type="web",
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"Memory stress test:")
        print(f"  Initial memory: {initial_memory:.2f} MB")
        print(f"  Peak memory: {peak_memory:.2f} MB")
        print(f"  Memory increase: {memory_increase:.2f} MB")
        
        # Memory usage should be reasonable
        assert memory_increase < 100  # Under 100MB increase
        
        # Cleanup
        self.task_manager.active_tasks.clear()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        print(f"  After cleanup: {final_memory:.2f} MB")
    
    def test_concurrent_stress(self):
        """Test system under concurrent stress."""
        num_threads = 20
        tasks_per_thread = 10
        
        def stress_worker(thread_id):
            thread_tasks = []
            
            for i in range(tasks_per_thread):
                with patch.object(self.task_manager.celery_app, 'AsyncResult') as mock_result:
                    mock_result.return_value.id = f"concurrent-stress-{thread_id}-{i}"
                    mock_result.return_value.apply_async.return_value = mock_result.return_value
                    
                    task_id = self.task_manager.submit_crawl_task(
                        url=f"https://httpbin.org/html?thread={thread_id}&task={i}",
                        config={"extraction_strategy": "css"},
                        crawler_type="web",
                        priority=TaskPriority.NORMAL
                    )
                    thread_tasks.append(task_id)
            
            return thread_tasks
        
        # Run concurrent stress test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(stress_worker, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        total_tasks = num_threads * tasks_per_thread
        throughput = total_tasks / total_time
        
        print(f"Concurrent stress test:")
        print(f"  Threads: {num_threads}")
        print(f"  Tasks per thread: {tasks_per_thread}")
        print(f"  Total tasks: {total_tasks}")
        print(f"  Time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} tasks/second")
        
        # Should handle concurrent stress
        assert throughput > 20
        assert total_time < 20  # Should complete in under 20 seconds


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])


