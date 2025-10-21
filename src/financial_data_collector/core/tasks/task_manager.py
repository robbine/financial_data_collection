"""
Task management interface for message queue operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

from .celery_app import celery_app
from .crawl_tasks import crawl_task, crawl_url_batch

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'


class TaskStatus(Enum):
    """Task status levels."""
    PENDING = 'PENDING'
    PROGRESS = 'PROGRESS'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RETRY = 'RETRY'
    REVOKED = 'REVOKED'


class TaskManager:
    """
    High-level task manager for crawling operations with message queue support.
    """
    
    def __init__(self):
        self.celery_app = celery_app
        self.active_tasks: Dict[str, Any] = {}
    
    def submit_crawl_task(self, url: str, config: Dict[str, Any], 
                         crawler_type: str = 'web', priority: TaskPriority = TaskPriority.NORMAL,
                         eta: Optional[datetime] = None) -> str:
        """
        Submit a single URL crawling task to the message queue.
        
        Args:
            url: Target URL to crawl
            config: Crawling configuration
            crawler_type: Type of crawler ('web', 'enhanced')
            priority: Task priority
            eta: Estimated time of arrival (for delayed execution)
        
        Returns:
            Task ID for tracking
        """
        try:
            # Prepare task arguments
            task_kwargs = {
                'args': [url, config, crawler_type, priority.value],
                'queue': 'crawl_queue',
                'priority': self._get_celery_priority(priority)
            }
            
            if eta:
                task_kwargs['eta'] = eta
            
            # Submit task
            result = crawl_task.apply_async(**task_kwargs)
            
            # Track task
            self.active_tasks[result.id] = {
                'type': 'single_crawl',
                'url': url,
                'priority': priority.value,
                'submitted_at': datetime.now(),
                'celery_result': result
            }
            
            logger.info(f"Submitted crawl task {result.id} for URL: {url}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to submit crawl task for URL {url}: {e}")
            raise
    
    def submit_batch_crawl_task(self, urls: List[str], config: Dict[str, Any],
                               crawler_type: str = 'web', priority: TaskPriority = TaskPriority.NORMAL,
                               eta: Optional[datetime] = None) -> str:
        """
        Submit a batch crawling task to the message queue.
        
        Args:
            urls: List of URLs to crawl
            config: Crawling configuration
            crawler_type: Type of crawler ('web', 'enhanced')
            priority: Task priority
            eta: Estimated time of arrival
        
        Returns:
            Batch task ID for tracking
        """
        try:
            # Prepare task arguments
            task_kwargs = {
                'args': [urls, config, crawler_type, priority.value],
                'queue': 'batch_queue',
                'priority': self._get_celery_priority(priority)
            }
            
            if eta:
                task_kwargs['eta'] = eta
            
            # Submit task
            result = crawl_url_batch.apply_async(**task_kwargs)
            
            # Track task
            self.active_tasks[result.id] = {
                'type': 'batch_crawl',
                'urls': urls,
                'url_count': len(urls),
                'priority': priority.value,
                'submitted_at': datetime.now(),
                'celery_result': result
            }
            
            logger.info(f"Submitted batch crawl task {result.id} for {len(urls)} URLs")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to submit batch crawl task for {len(urls)} URLs: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.
        
        Args:
            task_id: Task ID to check
        
        Returns:
            Dict containing task status information
        """
        try:
            # Get Celery result
            result = self.celery_app.AsyncResult(task_id)
            
            # Get tracked task info
            tracked_task = self.active_tasks.get(task_id, {})
            
            status_info = {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'progress': getattr(result, 'info', {}),
                'tracked_info': tracked_task,
                'checked_at': datetime.now().isoformat()
            }
            
            # Add timing information
            if tracked_task:
                submitted_at = tracked_task.get('submitted_at')
                if submitted_at:
                    elapsed = datetime.now() - submitted_at
                    status_info['elapsed_seconds'] = elapsed.total_seconds()
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get status for task {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running or pending task.
        
        Args:
            task_id: Task ID to cancel
        
        Returns:
            True if task was cancelled, False otherwise
        """
        try:
            result = self.celery_app.AsyncResult(task_id)
            result.revoke(terminate=True)
            
            # Update tracked task
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['cancelled_at'] = datetime.now()
            
            logger.info(f"Cancelled task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get information about all active tasks.
        
        Returns:
            List of active task information
        """
        active_tasks = []
        
        for task_id, task_info in self.active_tasks.items():
            try:
                status_info = self.get_task_status(task_id)
                active_tasks.append(status_info)
            except Exception as e:
                logger.warning(f"Failed to get status for tracked task {task_id}: {e}")
        
        return active_tasks
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed tasks older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for completed tasks
        
        Returns:
            Number of tasks cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        tasks_to_remove = []
        
        for task_id, task_info in self.active_tasks.items():
            try:
                submitted_at = task_info.get('submitted_at')
                if not submitted_at or submitted_at < cutoff_time:
                    # Check if task is completed
                    result = self.celery_app.AsyncResult(task_id)
                    if result.ready():
                        tasks_to_remove.append(task_id)
                        
            except Exception as e:
                logger.warning(f"Error checking task {task_id} for cleanup: {e}")
        
        # Remove completed tasks
        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} completed tasks")
        
        return cleaned_count
    
    def get_queue_info(self) -> Dict[str, Any]:
        """
        Get information about message queue status.
        
        Returns:
            Dict containing queue information
        """
        try:
            inspect = self.celery_app.control.inspect()
            
            queue_info = {
                'active_tasks': inspect.active(),
                'scheduled_tasks': inspect.scheduled(),
                'reserved_tasks': inspect.reserved(),
                'stats': inspect.stats(),
                'registered_tasks': list(self.celery_app.tasks.keys()),
                'checked_at': datetime.now().isoformat()
            }
            
            return queue_info
            
        except Exception as e:
            logger.error(f"Failed to get queue info: {e}")
            return {
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    def _get_celery_priority(self, priority: TaskPriority) -> int:
        """
        Convert TaskPriority enum to Celery priority number.
        
        Args:
            priority: TaskPriority enum value
        
        Returns:
            Celery priority number (0-9, higher is more priority)
        """
        priority_map = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 5,
            TaskPriority.HIGH: 7,
            TaskPriority.URGENT: 9
        }
        return priority_map.get(priority, 5)


