"""
Data models for financial data storage.

This module defines Pydantic models for financial data, news data,
and crawl tasks to ensure data consistency across the system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator


class DataType(Enum):
    """Data type enumeration."""
    STOCK = "stock"
    INDEX = "index"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    NEWS = "news"
    TASK = "task"


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FinancialData(BaseModel):
    """Financial data model for storing market data."""
    
    symbol: str = Field(..., description="Financial instrument symbol")
    data_type: DataType = Field(default=DataType.STOCK, description="Type of financial data")
    
    # Price data
    price: Optional[float] = Field(None, description="Current price")
    open_price: Optional[float] = Field(None, alias="open", description="Opening price")
    high_price: Optional[float] = Field(None, alias="high", description="Highest price")
    low_price: Optional[float] = Field(None, alias="low", description="Lowest price")
    close_price: Optional[float] = Field(None, alias="close", description="Closing price")
    
    # Volume and market data
    volume: Optional[int] = Field(None, description="Trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    
    # Technical indicators
    change: Optional[float] = Field(None, description="Price change")
    change_percent: Optional[float] = Field(None, description="Price change percentage")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Data timestamp")
    source: str = Field(..., description="Data source (e.g., yahoo_finance, alpha_vantage)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True
        use_enum_values = True
        
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate symbol format."""
        if not v or not isinstance(v, str):
            raise ValueError("Symbol must be a non-empty string")
        return v.upper().strip()
    
    @validator('price', 'open_price', 'high_price', 'low_price', 'close_price')
    def validate_prices(cls, v):
        """Validate price values."""
        if v is not None and v < 0:
            raise ValueError("Prices cannot be negative")
        return v
    
    @validator('volume', 'market_cap')
    def validate_positive_values(cls, v):
        """Validate positive numeric values."""
        if v is not None and v < 0:
            raise ValueError("Volume and market cap cannot be negative")
        return v


class NewsData(BaseModel):
    """News data model for storing financial news."""
    
    title: str = Field(..., description="News headline")
    content: Optional[str] = Field(None, description="News content/summary")
    url: str = Field(..., description="News article URL")
    
    # Classification
    symbols: List[str] = Field(default_factory=list, description="Related financial symbols")
    sentiment: Optional[str] = Field(None, description="Sentiment analysis result")
    category: Optional[str] = Field(None, description="News category")
    
    # Metadata
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    source: str = Field(..., description="News source")
    author: Optional[str] = Field(None, description="Article author")
    language: str = Field(default="en", description="Article language")
    
    # Storage metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Storage timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate and normalize symbols."""
        if not v:
            return []
        return [s.upper().strip() for s in v if s and isinstance(s, str)]
    
    @validator('sentiment')
    def validate_sentiment(cls, v):
        """Validate sentiment values."""
        if v is not None:
            v = v.lower().strip()
            if v not in ['positive', 'negative', 'neutral']:
                raise ValueError("Sentiment must be positive, negative, or neutral")
        return v


class CrawlTask(BaseModel):
    """Crawl task model for storing task information."""
    
    task_id: str = Field(..., description="Unique task identifier")
    url: str = Field(..., description="Target URL to crawl")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    
    # Task configuration
    crawler_type: str = Field(default="web", description="Type of crawler (web, enhanced)")
    priority: int = Field(default=2, description="Task priority (1-4)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Crawler configuration")
    
    # Timing information
    created_at: datetime = Field(default_factory=datetime.now, description="Task creation time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    
    # Results and errors
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Retry information
    retry_count: int = Field(default=0, description="Number of retries")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
    
    @validator('task_id')
    def validate_task_id(cls, v):
        """Validate task ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("Task ID must be a non-empty string")
        return v.strip()
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority range."""
        if not 1 <= v <= 4:
            raise ValueError("Priority must be between 1 and 4")
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """Basic URL validation."""
        if not v or not isinstance(v, str):
            raise ValueError("URL must be a non-empty string")
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v.strip()
    
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def is_running(self) -> bool:
        """Check if task is running."""
        return self.status == TaskStatus.RUNNING
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

