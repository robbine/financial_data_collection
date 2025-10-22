import os
from celery import Celery
from celery.schedules import crontab

# 创建 Celery app
celery_app = Celery(
    'financial_data_collector',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['financial_data_collector.core.tasks.crawl_tasks']  # 相对路径
)

# Celery 配置
celery_app.conf.update(
    task_routes={
        'financial_data_collector.core.tasks.crawl_tasks.crawl_task': {'queue': 'crawl_queue'},
        'financial_data_collector.core.tasks.crawl_tasks.crawl_url_batch': {'queue': 'batch_queue'},
    },
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_default_retry_delay=60,
    task_max_retries=3,
    beat_schedule={
        'daily-crawl': {
            'task': 'financial_data_collector.core.tasks.crawl_tasks.scheduled_crawl',  # 相对路径
            'schedule': crontab(hour=9, minute=0),
        },
        'hourly-monitor': {
            'task': 'financial_data_collector.core.tasks.crawl_tasks.health_check',  # 相对路径
            'schedule': crontab(minute=0),
        },
    },
    worker_send_task_events=True,
    task_send_sent_event=True,
)
