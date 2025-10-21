"""
Celery application configuration for asynchronous task processing.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Create Celery app
celery_app = Celery(
    'financial_data_collector',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['src.financial_data_collector.core.tasks.crawl_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'src.financial_data_collector.core.tasks.crawl_tasks.crawl_task': {'queue': 'crawl_queue'},
        'src.financial_data_collector.core.tasks.crawl_tasks.crawl_url_batch': {'queue': 'batch_queue'},
    },
    
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Beat scheduler for periodic tasks
    beat_schedule={
        'daily-crawl': {
            'task': 'src.financial_data_collector.core.tasks.crawl_tasks.scheduled_crawl',
            'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
        },
        'hourly-monitor': {
            'task': 'src.financial_data_collector.core.tasks.crawl_tasks.health_check',
            'schedule': crontab(minute=0),  # Every hour
        },
    },
)

# Task monitoring
celery_app.conf.update(
    worker_send_task_events=True,
    task_send_sent_event=True,
)

if __name__ == '__main__':
    celery_app.start()


