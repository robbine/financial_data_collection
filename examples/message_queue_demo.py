"""
Message Queue Integration Demo

This demo shows how to use the message queue system for asynchronous crawling tasks.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from src.financial_data_collector.core.tasks.task_manager import TaskManager, TaskPriority


async def demo_message_queue_integration():
    """Demonstrate message queue integration for crawling tasks."""
    
    print("🚀 Message Queue Integration Demo")
    print("=" * 50)
    
    # Initialize task manager
    task_manager = TaskManager()
    
    # Demo 1: Submit single crawl task
    print("\n📋 Demo 1: Submit Single Crawl Task")
    print("-" * 30)
    
    crawl_config = {
        "extraction_strategy": "css",
        "wait_for": 2,
        "max_scrolls": 1,
        "word_count_threshold": 100
    }
    
    task_id = task_manager.submit_crawl_task(
        url="https://www.nbcnews.com/business",
        config=crawl_config,
        crawler_type="web",
        priority=TaskPriority.NORMAL
    )
    
    print(f"✅ Submitted task: {task_id}")
    
    # Demo 2: Submit batch crawl task
    print("\n📋 Demo 2: Submit Batch Crawl Task")
    print("-" * 30)
    
    urls = [
        "https://www.nbcnews.com/business",
        "https://finance.yahoo.com",
        "https://www.reuters.com/business"
    ]
    
    batch_config = {
        "extraction_strategy": "css",
        "wait_for": 1,
        "max_scrolls": 0,
        "max_concurrent": 2  # Process 2 URLs concurrently
    }
    
    batch_task_id = task_manager.submit_batch_crawl_task(
        urls=urls,
        config=batch_config,
        crawler_type="web",
        priority=TaskPriority.HIGH
    )
    
    print(f"✅ Submitted batch task: {batch_task_id}")
    print(f"📊 URLs in batch: {len(urls)}")
    
    # Demo 3: Submit delayed task
    print("\n📋 Demo 3: Submit Delayed Task")
    print("-" * 30)
    
    delayed_time = datetime.now() + timedelta(minutes=1)
    
    delayed_task_id = task_manager.submit_crawl_task(
        url="https://www.bloomberg.com/markets",
        config=crawl_config,
        crawler_type="enhanced",
        priority=TaskPriority.LOW,
        eta=delayed_time
    )
    
    print(f"✅ Submitted delayed task: {delayed_task_id}")
    print(f"⏰ Scheduled for: {delayed_time.isoformat()}")
    
    # Demo 4: Monitor task status
    print("\n📋 Demo 4: Monitor Task Status")
    print("-" * 30)
    
    tasks_to_monitor = [task_id, batch_task_id, delayed_task_id]
    
    for i in range(5):  # Check status 5 times
        print(f"\n🔍 Status Check {i + 1}:")
        
        for task_id_to_check in tasks_to_monitor:
            status = task_manager.get_task_status(task_id_to_check)
            
            print(f"  Task {task_id_to_check}:")
            print(f"    Status: {status['status']}")
            
            if status.get('elapsed_seconds'):
                print(f"    Elapsed: {status['elapsed_seconds']:.1f}s")
            
            if status.get('progress'):
                progress = status['progress']
                if isinstance(progress, dict) and 'status' in progress:
                    print(f"    Progress: {progress['status']}")
        
        if i < 4:  # Don't wait after the last check
            print("  ⏳ Waiting 10 seconds...")
            time.sleep(10)
    
    # Demo 5: Get active tasks
    print("\n📋 Demo 5: Get Active Tasks")
    print("-" * 30)
    
    active_tasks = task_manager.get_active_tasks()
    print(f"📊 Total active tasks: {len(active_tasks)}")
    
    for task in active_tasks:
        print(f"  Task {task['task_id']}:")
        print(f"    Status: {task['status']}")
        print(f"    Type: {task.get('tracked_info', {}).get('type', 'unknown')}")
        print(f"    Priority: {task.get('tracked_info', {}).get('priority', 'unknown')}")
    
    # Demo 6: Get queue information
    print("\n📋 Demo 6: Get Queue Information")
    print("-" * 30)
    
    queue_info = task_manager.get_queue_info()
    
    print("📊 Queue Information:")
    if queue_info.get('stats'):
        stats = queue_info['stats']
        if stats:
            for worker, worker_stats in stats.items():
                print(f"  Worker {worker}:")
                print(f"    Pool: {worker_stats.get('pool', {})}")
                print(f"    Total tasks: {worker_stats.get('total', 'N/A')}")
    
    if queue_info.get('registered_tasks'):
        print(f"  Registered tasks: {len(queue_info['registered_tasks'])}")
        for task_name in queue_info['registered_tasks'][:5]:  # Show first 5
            print(f"    - {task_name}")
    
    # Demo 7: Cancel a task (if still pending)
    print("\n📋 Demo 7: Task Cancellation")
    print("-" * 30)
    
    # Try to cancel the delayed task
    cancelled = task_manager.cancel_task(delayed_task_id)
    if cancelled:
        print(f"✅ Cancelled delayed task: {delayed_task_id}")
    else:
        print(f"ℹ️  Could not cancel task {delayed_task_id} (may have already started)")
    
    # Demo 8: Cleanup completed tasks
    print("\n📋 Demo 8: Cleanup Completed Tasks")
    print("-" * 30)
    
    cleaned_count = task_manager.cleanup_completed_tasks(max_age_hours=1)
    print(f"🧹 Cleaned up {cleaned_count} completed tasks")
    
    print("\n🎉 Message Queue Demo Completed!")
    print("=" * 50)


async def demo_api_usage():
    """Demonstrate API usage patterns."""
    
    print("\n🌐 API Usage Demo")
    print("=" * 30)
    
    print("📝 Example API calls:")
    
    # Example 1: Submit single crawl via API
    print("\n1. Submit Single Crawl Task:")
    print("POST /api/tasks/crawl")
    print(json.dumps({
        "url": "https://www.nbcnews.com/business",
        "config": {
            "extraction_strategy": "llm",
            "llm_config": {
                "provider": "volc",
                "model": "ep-20250725215501-7zrfm"
            }
        },
        "crawler_type": "enhanced",
        "priority": "high"
    }, indent=2))
    
    # Example 2: Submit batch crawl via API
    print("\n2. Submit Batch Crawl Task:")
    print("POST /api/tasks/batch-crawl")
    print(json.dumps({
        "urls": [
            "https://finance.yahoo.com",
            "https://www.reuters.com/business",
            "https://www.bloomberg.com/markets"
        ],
        "config": {
            "extraction_strategy": "css",
            "max_concurrent": 2
        },
        "crawler_type": "web",
        "priority": "normal"
    }, indent=2))
    
    # Example 3: Check task status via API
    print("\n3. Check Task Status:")
    print("GET /api/tasks/status/{task_id}")
    
    # Example 4: Get active tasks via API
    print("\n4. Get Active Tasks:")
    print("GET /api/tasks/active")
    
    # Example 5: Direct crawl (immediate execution) via API
    print("\n5. Direct Crawl (Immediate):")
    print("POST /api/crawler/crawl")
    print(json.dumps({
        "url": "https://www.nbcnews.com/business",
        "config": {
            "extraction_strategy": "css"
        },
        "crawler_type": "web",
        "timeout": 60
    }, indent=2))


def demo_docker_compose_integration():
    """Demonstrate Docker Compose integration."""
    
    print("\n🐳 Docker Compose Integration")
    print("=" * 35)
    
    print("📋 Services added to docker-compose.dev.yml:")
    print("  • celery-worker: Processes crawling tasks")
    print("  • celery-beat: Handles scheduled tasks")
    print("  • redis: Message broker and result backend")
    
    print("\n🚀 Starting the system:")
    print("  docker compose -f docker-compose.dev.yml up -d")
    
    print("\n📊 Monitoring:")
    print("  • Redis Commander: http://localhost:8081")
    print("  • Task API: http://localhost:8000/api/tasks/")
    print("  • Crawler API: http://localhost:8000/api/crawler/")
    
    print("\n🔧 Management commands:")
    print("  # View worker logs")
    print("  docker compose -f docker-compose.dev.yml logs celery-worker")
    print("")
    print("  # View beat logs")
    print("  docker compose -f docker-compose.dev.yml logs celery-beat")
    print("")
    print("  # Scale workers")
    print("  docker compose -f docker-compose.dev.yml up -d --scale celery-worker=3")


if __name__ == "__main__":
    print("🎯 Financial Data Collector - Message Queue Integration")
    print("=" * 60)
    
    # Run demos
    asyncio.run(demo_message_queue_integration())
    asyncio.run(demo_api_usage())
    demo_docker_compose_integration()
    
    print("\n✨ All demos completed!")
    print("\n💡 Next steps:")
    print("  1. Start the system: docker compose -f docker-compose.dev.yml up -d")
    print("  2. Test API endpoints with curl or Postman")
    print("  3. Monitor tasks via Redis Commander")
    print("  4. Scale workers based on load")


