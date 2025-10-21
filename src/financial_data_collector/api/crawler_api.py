"""
REST API for direct crawler operations (non-queued).
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.crawler.web_crawler import WebCrawler
from ..core.crawler.enhanced_web_crawler import EnhancedWebCrawler

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/crawler", tags=["crawler"])


# Request/Response models
class DirectCrawlRequest(BaseModel):
    """Request model for direct crawling (immediate execution)."""
    url: str = Field(..., description="Target URL to crawl")
    config: Dict[str, Any] = Field(default_factory=dict, description="Crawling configuration")
    crawler_type: str = Field(default="web", description="Type of crawler (web, enhanced)")
    timeout: Optional[int] = Field(300, description="Timeout in seconds")


class CrawlResponse(BaseModel):
    """Response model for crawl results."""
    success: bool
    url: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    crawler_type: str
    execution_time_seconds: float
    completed_at: str


# API endpoints
@router.post("/crawl", response_model=CrawlResponse)
async def direct_crawl(request: DirectCrawlRequest):
    """
    Execute crawling directly without queuing (immediate execution).
    """
    start_time = datetime.now()
    crawler = None
    
    try:
        logger.info(f"API: Starting direct crawl for URL: {request.url}")
        
        # Initialize crawler based on type
        if request.crawler_type == "enhanced":
            crawler = EnhancedWebCrawler("DirectCrawler")
        else:
            crawler = WebCrawler("DirectCrawler")
        
        # Initialize and start crawler
        crawler.initialize(request.config)
        await crawler.start()
        
        # Execute crawling
        if request.crawler_type == "enhanced":
            result = await crawler.crawl_url_enhanced(request.url, request.config)
        else:
            result = await crawler.collect_data("web", {"url": request.url, **request.config})
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"API: Direct crawl completed for URL: {request.url} in {execution_time:.2f}s")
        
        return CrawlResponse(
            success=True,
            url=request.url,
            result=result,
            crawler_type=request.crawler_type,
            execution_time_seconds=execution_time,
            completed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.error(f"API: Direct crawl failed for URL {request.url}: {e}")
        
        return CrawlResponse(
            success=False,
            url=request.url,
            error=str(e),
            crawler_type=request.crawler_type,
            execution_time_seconds=execution_time,
            completed_at=datetime.now().isoformat()
        )
        
    finally:
        # Cleanup crawler
        if crawler:
            try:
                await crawler.stop()
            except Exception as e:
                logger.warning(f"API: Error stopping crawler: {e}")


@router.get("/health")
async def crawler_health_check():
    """
    Health check for crawler API.
    """
    try:
        # Test crawler initialization
        crawler = WebCrawler("HealthCheckCrawler")
        crawler.initialize({})
        
        return {
            "status": "healthy",
            "message": "Crawler API is operational",
            "checked_at": datetime.now().isoformat(),
            "crawler_types": ["web", "enhanced"]
        }
        
    except Exception as e:
        logger.error(f"API: Crawler health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Crawler API health check failed: {e}",
            "checked_at": datetime.now().isoformat()
        }


