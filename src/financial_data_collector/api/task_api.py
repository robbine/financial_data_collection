"""
REST API for task management and message queue operations.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..core.tasks.task_manager import TaskManager, TaskPriority

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Initialize task manager
task_manager = TaskManager()


# Request/Response models
class CrawlTaskRequest(BaseModel):
    """Request model for single URL crawl task."""
    url: str = Field(..., description="Target URL to crawl")
    config: Dict[str, Any] = Field(default_factory=dict, description="Crawling configuration")
    crawler_type: str = Field(default="web", description="Type of crawler (web, enhanced)")
    priority: str = Field(default="normal", description="Task priority (low, normal, high, urgent)")
    eta: Optional[datetime] = Field(None, description="Estimated time of arrival for delayed execution")


class BatchCrawlTaskRequest(BaseModel):
    """Request model for batch URL crawl task."""
    urls: List[str] = Field(..., description="List of URLs to crawl")
    config: Dict[str, Any] = Field(default_factory=dict, description="Crawling configuration")
    crawler_type: str = Field(default="web", description="Type of crawler (web, enhanced)")
    priority: str = Field(default="normal", description="Task priority (low, normal, high, urgent)")
    eta: Optional[datetime] = Field(None, description="Estimated time of arrival for delayed execution")


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    progress: Optional[Dict[str, Any]] = None
    tracked_info: Optional[Dict[str, Any]] = None
    elapsed_seconds: Optional[float] = None
    checked_at: str


class TaskSubmissionResponse(BaseModel):
    """Response model for task submission."""
    task_id: str
    message: str
    submitted_at: str


class QueueInfoResponse(BaseModel):
    """Response model for queue information."""
    active_tasks: Optional[Dict[str, Any]] = None
    scheduled_tasks: Optional[Dict[str, Any]] = None
    reserved_tasks: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
    registered_tasks: List[str]
    checked_at: str


# API endpoints
@router.post("/crawl", response_model=TaskSubmissionResponse)
async def submit_crawl_task(request: CrawlTaskRequest):
    """
    Submit a single URL crawling task to the message queue.
    """
    try:
        # Validate priority
        try:
            priority = TaskPriority(request.priority.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid priority '{request.priority}'. Must be one of: {[p.value for p in TaskPriority]}"
            )
        
        # Submit task
        task_id = task_manager.submit_crawl_task(
            url=request.url,
            config=request.config,
            crawler_type=request.crawler_type,
            priority=priority,
            eta=request.eta
        )
        
        logger.info(f"API: Submitted crawl task {task_id} for URL: {request.url}")
        
        return TaskSubmissionResponse(
            task_id=task_id,
            message=f"Crawl task submitted successfully for URL: {request.url}",
            submitted_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"API: Failed to submit crawl task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-crawl", response_model=TaskSubmissionResponse)
async def submit_batch_crawl_task(request: BatchCrawlTaskRequest):
    """
    Submit a batch URL crawling task to the message queue.
    """
    try:
        # Validate priority
        try:
            priority = TaskPriority(request.priority.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid priority '{request.priority}'. Must be one of: {[p.value for p in TaskPriority]}"
            )
        
        # Submit batch task
        task_id = task_manager.submit_batch_crawl_task(
            urls=request.urls,
            config=request.config,
            crawler_type=request.crawler_type,
            priority=priority,
            eta=request.eta
        )
        
        logger.info(f"API: Submitted batch crawl task {task_id} for {len(request.urls)} URLs")
        
        return TaskSubmissionResponse(
            task_id=task_id,
            message=f"Batch crawl task submitted successfully for {len(request.urls)} URLs",
            submitted_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"API: Failed to submit batch crawl task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a specific task.
    """
    try:
        status_info = task_manager.get_task_status(task_id)
        
        return TaskStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"API: Failed to get status for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running or pending task.
    """
    try:
        success = task_manager.cancel_task(task_id)
        
        if success:
            return {"message": f"Task {task_id} cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or could not be cancelled")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=List[TaskStatusResponse])
async def get_active_tasks():
    """
    Get information about all active tasks.
    """
    try:
        active_tasks = task_manager.get_active_tasks()
        
        return [TaskStatusResponse(**task_info) for task_info in active_tasks]
        
    except Exception as e:
        logger.error(f"API: Failed to get active tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_completed_tasks(max_age_hours: int = 24):
    """
    Clean up completed tasks older than specified age.
    """
    try:
        cleaned_count = task_manager.cleanup_completed_tasks(max_age_hours)
        
        return {
            "message": f"Cleaned up {cleaned_count} completed tasks",
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours,
            "cleaned_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"API: Failed to cleanup tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue-info", response_model=QueueInfoResponse)
async def get_queue_info():
    """
    Get information about message queue status.
    """
    try:
        queue_info = task_manager.get_queue_info()
        
        return QueueInfoResponse(**queue_info)
        
    except Exception as e:
        logger.error(f"API: Failed to get queue info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check for task API.
    """
    try:
        # Test Redis connection
        queue_info = task_manager.get_queue_info()
        
        return {
            "status": "healthy",
            "message": "Task API is operational",
            "checked_at": datetime.now().isoformat(),
            "queue_accessible": "error" not in queue_info
        }
        
    except Exception as e:
        logger.error(f"API: Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Task API health check failed: {e}",
            "checked_at": datetime.now().isoformat()
        }


