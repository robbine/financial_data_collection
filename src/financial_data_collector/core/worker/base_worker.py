from celery import Celery
from ..crawler.crawler_factory import CrawlerFactory
from ...utils.logger import financial_logger  # 金融合规日志
from ..tasks.celery_app import celery_app

class FinancialBaseWorker:
    def __init__(self, app_name: str, queue_name: str):
        self.celery = celery_app
        self.queue_name = queue_name
        self.logger = financial_logger  # 符合SEC 17a-4审计要求的日志器

    def _initialize_crawler(self, crawler_type: str, config: dict):
        """初始化爬虫实例（封装CrawlerFactory调用）"""
        return CrawlerFactory.get_crawler(crawler_type, config)

    def start(self):
        """启动worker，日志自动附加数据源标识"""
        self.logger.info(f"Starting {self.queue_name} worker")
        self.celery.worker_main([
            'worker',
            f'--queue={self.queue_name}',
            '--loglevel=INFO',
            '--concurrency=2'  # 基础并发配置
        ])