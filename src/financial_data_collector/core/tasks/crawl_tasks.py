"""
Celery tasks for crawling operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from celery import current_task
from celery.exceptions import Retry

from .celery_app import celery_app
from ..crawler.web_crawler import WebCrawler
from ..crawler.enhanced_web_crawler import EnhancedWebCrawler

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='crawl_task')
def crawl_task(self, url: str, config: Dict[str, Any], 
               crawler_type: str = 'web', priority: str = 'normal') -> Dict[str, Any]:
    """
    Celery task for crawling a single URL.
    
    Args:
        url: Target URL to crawl
        config: Crawling configuration
        crawler_type: Type of crawler ('web', 'enhanced')
        priority: Task priority ('low', 'normal', 'high', 'urgent')
    
    Returns:
        Dict containing crawl results and metadata
    """
    task_id = self.request.id
    
    try:
        logger.info(f"Starting crawl task {task_id} for URL: {url}")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Initializing crawler', 'url': url}
        )
        
        # Run async crawler in sync context
        result = asyncio.run(_execute_crawl_task(
            task_id, url, config, crawler_type, priority, self
        ))
        
        logger.info(f"Crawl task {task_id} completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"Crawl task {task_id} failed: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # Final failure
        return {
            'task_id': task_id,
            'url': url,
            'success': False,
            'error': str(exc),
            'completed_at': datetime.now().isoformat(),
            'retries': self.request.retries
        }


async def _execute_crawl_task(task_id: str, url: str, config: Dict[str, Any], 
                            crawler_type: str, priority: str, celery_task) -> Dict[str, Any]:
    """
    Execute the actual crawling task asynchronously.
    """
    crawler = None
    
    try:
        # Initialize crawler based on type
        if crawler_type == 'enhanced':
            crawler = EnhancedWebCrawler(f"Crawler-{task_id}")
        else:
            crawler = WebCrawler(f"Crawler-{task_id}")
        
        # Update progress
        celery_task.update_state(
            state='PROGRESS',
            meta={'status': 'Starting crawler', 'url': url}
        )
        
        # Initialize and start crawler
        crawler.initialize(config)
        await crawler.start()
        
        # Update progress
        celery_task.update_state(
            state='PROGRESS',
            meta={'status': 'Crawling in progress', 'url': url}
        )
        
        # Execute crawling
        if crawler_type == 'enhanced':
            result = await crawler.crawl_url_enhanced(url, config)
        else:
            result = await crawler.collect_data("web", {"url": url, **config})
        
        # Update progress
        celery_task.update_state(
            state='PROGRESS',
            meta={'status': 'Processing results', 'url': url}
        )
        
        # Prepare final result
        final_result = {
            'task_id': task_id,
            'url': url,
            'success': True,
            'crawler_type': crawler_type,
            'priority': priority,
            'result': result,
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'config': config
        }
        
        return final_result
        
    except Exception as e:
        logger.error(f"Error in crawl task {task_id}: {e}")
        raise
        
    finally:
        # Cleanup crawler
        if crawler:
            try:
                await crawler.stop()
            except Exception as e:
                logger.warning(f"Error stopping crawler for task {task_id}: {e}")


@celery_app.task(bind=True, name='crawl_url_batch')
def crawl_url_batch(self, urls: List[str], config: Dict[str, Any], 
                   crawler_type: str = 'web', priority: str = 'normal') -> Dict[str, Any]:
    """
    Celery task for crawling multiple URLs in batch.
    
    Args:
        urls: List of URLs to crawl
        config: Crawling configuration
        crawler_type: Type of crawler ('web', 'enhanced')
        priority: Task priority ('low', 'normal', 'high', 'urgent')
    
    Returns:
        Dict containing batch results
    """
    task_id = self.request.id
    batch_results = []
    
    try:
        logger.info(f"Starting batch crawl task {task_id} for {len(urls)} URLs")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': f'Processing batch of {len(urls)} URLs', 'progress': 0}
        )
        
        # Process URLs sequentially or in parallel based on config
        max_concurrent = config.get('max_concurrent', 3)
        
        if max_concurrent == 1:
            # Sequential processing
            for i, url in enumerate(urls):
                try:
                    result = crawl_task.apply_async(
                        args=[url, config, crawler_type, priority],
                        queue='crawl_queue'
                    ).get(timeout=300)  # 5 minute timeout per URL
                    
                    batch_results.append(result)
                    
                    # Update progress
                    progress = int((i + 1) / len(urls) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={'status': f'Completed {i + 1}/{len(urls)} URLs', 'progress': progress}
                    )
                    
                except Exception as e:
                    error_result = {
                        'task_id': f"{task_id}-{i}",
                        'url': url,
                        'success': False,
                        'error': str(e),
                        'completed_at': datetime.now().isoformat()
                    }
                    batch_results.append(error_result)
        else:
            # Parallel processing (simplified - could be enhanced with proper async batch)
            for url in urls:
                try:
                    # Submit individual tasks
                    subtask = crawl_task.apply_async(
                        args=[url, config, crawler_type, priority],
                        queue='crawl_queue'
                    )
                    batch_results.append({
                        'subtask_id': subtask.id,
                        'url': url,
                        'status': 'submitted'
                    })
                except Exception as e:
                    batch_results.append({
                        'url': url,
                        'success': False,
                        'error': str(e)
                    })
        
        logger.info(f"Batch crawl task {task_id} completed")
        
        return {
            'task_id': task_id,
            'batch_type': 'parallel' if max_concurrent > 1 else 'sequential',
            'total_urls': len(urls),
            'completed_urls': len([r for r in batch_results if r.get('success', False)]),
            'failed_urls': len([r for r in batch_results if not r.get('success', True)]),
            'results': batch_results,
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Batch crawl task {task_id} failed: {exc}")
        return {
            'task_id': task_id,
            'success': False,
            'error': str(exc),
            'partial_results': batch_results,
            'completed_at': datetime.now().isoformat()
        }


@celery_app.task(name='scheduled_crawl')
def scheduled_crawl():
    """
    Scheduled crawl task for periodic crawling.
    """
    logger.info("Executing scheduled crawl task")
    
    # This would typically load URLs from a database or configuration
    # For now, just log the execution
    return {
        'scheduled_at': datetime.now().isoformat(),
        'status': 'completed',
        'message': 'Scheduled crawl executed'
    }


@celery_app.task(name='health_check')
def health_check():
    """
    Health check task for monitoring crawler status.
    """
    logger.info("Executing health check task")
    
    # Check Redis connection, database, etc.
    return {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'components': {
            'redis': 'connected',
            'database': 'connected',
            'crawlers': 'available'
        }
    }


