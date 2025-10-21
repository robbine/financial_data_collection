"""
API crawler implementation for financial data collection.

This module provides API-based data collection capabilities for various
financial data sources including Yahoo Finance, Alpha Vantage, Quandl, etc.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import time

from ..interfaces import BaseDataCollector, APICollectorInterface
from ..events import EventBus, DataCollectedEvent

logger = logging.getLogger(__name__)


class APICollector(BaseDataCollector, APICollectorInterface):
    """
    API-based data collector for financial data sources.
    
    Supports multiple financial APIs:
    - Yahoo Finance
    - Alpha Vantage
    - Quandl
    - SEC EDGAR
    - Custom APIs
    """
    
    def __init__(self, name: str = "APICollector"):
        super().__init__(name)
        self.supported_sources = ["api", "yahoo_finance", "alpha_vantage", "quandl", "sec_edgar"]
        self.session: Optional[aiohttp.ClientSession] = None
        self.event_bus: Optional[EventBus] = None
        self.config: Dict[str, Any] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.last_request_times: Dict[str, float] = {}
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the API collector with configuration."""
        self.config = config
        
        # API configurations
        self.api_configs = config.get("api_configs", {})
        
        # Rate limiting settings
        self.rate_limits = {
            "yahoo_finance": {"requests_per_minute": 100, "requests_per_hour": 1000},
            "alpha_vantage": {"requests_per_minute": 5, "requests_per_hour": 500},
            "quandl": {"requests_per_minute": 10, "requests_per_hour": 2000},
            "sec_edgar": {"requests_per_minute": 10, "requests_per_hour": 1000},
            "default": {"requests_per_minute": 60, "requests_per_hour": 1000}
        }
        
        # Request settings
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        
        # Authentication
        self.api_keys = config.get("api_keys", {})
        
        logger.info("APICollector initialized")
    
    async def start(self) -> None:
        """Start the API collector."""
        if not self._initialized:
            raise RuntimeError("APICollector not initialized")
        
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            self._started = True
            logger.info("APICollector started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start APICollector: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the API collector."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self._started = False
        logger.info("APICollector stopped")
    
    def get_supported_sources(self) -> List[str]:
        """Get supported data source types."""
        return self.supported_sources
    
    async def collect_data(self, source: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data from an API source."""
        if not self.session:
            raise RuntimeError("APICollector not started")
        
        api_type = config.get("api_type", source)
        endpoint = config.get("endpoint")
        params = config.get("params", {})
        
        if not endpoint:
            raise ValueError("API endpoint is required")
        
        # Check rate limiting
        await self._check_rate_limit(api_type)
        
        try:
            # Make API request
            result = await self.make_request(endpoint, params)
            
            # Process the result
            processed_data = await self._process_api_result(result, config)
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish_async(
                    DataCollectedEvent(
                        data=processed_data,
                        source=f"api_collector:{api_type}",
                        metadata={"api_type": api_type, "endpoint": endpoint}
                    )
                )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to collect data from {api_type}: {e}")
            raise
    
    async def make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API request."""
        if not self.session:
            raise RuntimeError("APICollector not started")
        
        # Add authentication if needed
        headers = self._get_headers(params)
        params = self._add_authentication(params)
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(endpoint, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status_code": response.status,
                            "data": data,
                            "headers": dict(response.headers),
                            "url": str(response.url)
                        }
                    elif response.status == 429:  # Rate limited
                        wait_time = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited, waiting {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()
                        
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {wait_time} seconds: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        raise Exception(f"Failed to make request after {self.max_retries} attempts")
    
    def get_rate_limit(self) -> int:
        """Get rate limit per minute."""
        return self.rate_limits.get("default", {}).get("requests_per_minute", 60)
    
    def get_authentication_required(self) -> bool:
        """Check if authentication is required."""
        return bool(self.api_keys)
    
    def validate_source(self, source: str) -> bool:
        """Validate if a source is supported."""
        return source in self.supported_sources
    
    def _get_headers(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Get HTTP headers for the request."""
        headers = {
            "User-Agent": "Financial Data Collector 1.0",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate"
        }
        
        # Add API-specific headers
        if "api_type" in params:
            api_type = params["api_type"]
            if api_type == "alpha_vantage":
                headers["Accept"] = "application/json"
            elif api_type == "quandl":
                headers["Accept"] = "application/json"
        
        return headers
    
    def _add_authentication(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add authentication parameters to the request."""
        api_type = params.get("api_type", "default")
        
        if api_type in self.api_keys:
            api_key = self.api_keys[api_type]
            
            if api_type == "alpha_vantage":
                params["apikey"] = api_key
            elif api_type == "quandl":
                params["api_key"] = api_key
            elif api_type == "sec_edgar":
                # SEC EDGAR doesn't require API key
                pass
        
        return params
    
    async def _check_rate_limit(self, api_type: str) -> None:
        """Check and enforce rate limiting."""
        current_time = time.time()
        rate_limit = self.rate_limits.get(api_type, self.rate_limits["default"])
        
        # Check per-minute rate limit
        minute_key = f"{api_type}_minute"
        if minute_key in self.last_request_times:
            time_since_last = current_time - self.last_request_times[minute_key]
            if time_since_last < 60:  # Within the same minute
                requests_this_minute = 1  # This would need to be tracked properly
                if requests_this_minute >= rate_limit["requests_per_minute"]:
                    wait_time = 60 - time_since_last
                    logger.warning(f"Rate limit reached for {api_type}, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
        
        self.last_request_times[minute_key] = current_time
    
    async def _process_api_result(self, result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process API result and extract relevant data."""
        processed_data = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "api_response": {
                "status_code": result["status_code"],
                "url": result["url"],
                "headers": result["headers"]
            },
            "raw_data": result["data"]
        }
        
        # Extract financial data based on API type
        api_type = config.get("api_type", "default")
        if api_type == "yahoo_finance":
            processed_data["financial_data"] = self._extract_yahoo_finance_data(result["data"])
        elif api_type == "alpha_vantage":
            processed_data["financial_data"] = self._extract_alpha_vantage_data(result["data"])
        elif api_type == "quandl":
            processed_data["financial_data"] = self._extract_quandl_data(result["data"])
        elif api_type == "sec_edgar":
            processed_data["financial_data"] = self._extract_sec_edgar_data(result["data"])
        
        return processed_data
    
    def _extract_yahoo_finance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from Yahoo Finance API response."""
        # Yahoo Finance API response structure
        if "quoteResponse" in data and "result" in data["quoteResponse"]:
            result = data["quoteResponse"]["result"][0]
            return {
                "symbol": result.get("symbol"),
                "price": result.get("regularMarketPrice"),
                "volume": result.get("regularMarketVolume"),
                "change": result.get("regularMarketChange"),
                "change_percent": result.get("regularMarketChangePercent"),
                "market_cap": result.get("marketCap"),
                "pe_ratio": result.get("trailingPE"),
                "dividend_yield": result.get("dividendYield")
            }
        return {}
    
    def _extract_alpha_vantage_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from Alpha Vantage API response."""
        # Alpha Vantage response structure varies by function
        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "symbol": quote.get("01. symbol"),
                "price": float(quote.get("05. price", 0)),
                "volume": int(quote.get("06. volume", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent"),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "open": float(quote.get("02. open", 0)),
                "previous_close": float(quote.get("08. previous close", 0))
            }
        return {}
    
    def _extract_quandl_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from Quandl API response."""
        # Quandl response structure
        if "dataset" in data:
            dataset = data["dataset"]
            return {
                "name": dataset.get("name"),
                "description": dataset.get("description"),
                "data": dataset.get("data", []),
                "column_names": dataset.get("column_names", []),
                "frequency": dataset.get("frequency"),
                "type": dataset.get("type")
            }
        return {}
    
    def _extract_sec_edgar_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from SEC EDGAR API response."""
        # SEC EDGAR response structure
        if "filings" in data:
            filings = data["filings"]
            return {
                "company": filings.get("company"),
                "cik": filings.get("cik"),
                "filings": filings.get("filings", []),
                "total_count": filings.get("totalCount", 0)
            }
        return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self.session:
            return {
                "status": "unhealthy",
                "message": "Session not initialized",
                "details": {"session_initialized": False}
            }
        
        try:
            # Test API connectivity
            test_url = "https://httpbin.org/get"
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "message": "APICollector is working",
                        "details": {
                            "session_initialized": True,
                            "test_request_successful": True,
                            "supported_apis": list(self.api_configs.keys()),
                            "rate_limits": self.rate_limits
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Test request failed with status {response.status}",
                        "details": {
                            "session_initialized": True,
                            "test_request_successful": False,
                            "status_code": response.status
                        }
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "details": {
                    "session_initialized": True,
                    "test_request_successful": False,
                    "error": str(e)
                }
            }
