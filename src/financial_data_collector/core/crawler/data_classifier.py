"""
Data classification service for crawled content.

This module provides intelligent data type classification for crawled content,
extracting financial symbols and determining the appropriate data type
(financial/news/generic) based on URL patterns and content analysis.
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DataClassifier:
    """
    Intelligent data classifier for crawled content.
    
    Features:
    - URL pattern analysis for data type detection
    - Financial symbol extraction from URLs and content
    - Safe type conversion utilities
    - Content analysis for news vs financial data
    """
    
    def __init__(self):
        """Initialize the data classifier."""
        self.financial_domains = [
            "finance.yahoo.com",
            "marketwatch.com", 
            "bloomberg.com",
            "investing.com",
            "seekingalpha.com",
            "fool.com",
            "nasdaq.com",
            "wsj.com",
            "reuters.com",
            "cnbc.com"
        ]
        
        self.news_indicators = [
            "news", "article", "story", "blog", "press-release"
        ]
        
        self.financial_indicators = [
            "quote", "stock", "price", "market", "trading", "financial"
        ]
        
        # Common stock symbol patterns
        self.symbol_patterns = [
            r'/quote/([A-Z]+)',
            r'/symbol/([A-Z]+)',
            r'=([A-Z]{1,5})',
            r'/([A-Z]{1,5})-',
            r'\?symbol=([A-Z]+)',
            r'&symbol=([A-Z]+)'
        ]
        
        # Words to exclude from symbol extraction
        self.exclude_words = {
            "THE", "AND", "OR", "FOR", "TO", "OF", "IN", "ON", "AT", "BY",
            "WITH", "FROM", "THIS", "THAT", "HAS", "HAVE", "WAS", "WERE",
            "BEEN", "BEING", "WILL", "WOULD", "COULD", "SHOULD", "MAY",
            "MIGHT", "CAN", "MUST", "SHALL", "GET", "GOT", "GONE", "COME",
            "CAME", "TAKE", "TOOK", "TAKEN", "MAKE", "MADE", "GIVE", "GAVE",
            "GIVEN", "SEE", "SAW", "SEEN", "KNOW", "KNEW", "KNOWN", "THINK",
            "THOUGHT", "LOOK", "LOOKED", "USE", "USED", "FIND", "FOUND",
            "WORK", "WORKED", "CALL", "CALLED", "TRY", "TRIED", "ASK", "ASKED",
            "NEED", "NEEDED", "FEEL", "FELT", "BECOME", "BECAME", "LEAVE",
            "LEFT", "PUT", "MEAN", "MEANT", "KEEP", "KEPT", "LET", "BEGIN",
            "BEGAN", "BEGUN", "SEEM", "SEEMED", "HELP", "HELPED", "TALK",
            "TALKED", "TURN", "TURNED", "START", "STARTED", "SHOW", "SHOWED",
            "HEAR", "HEARD", "PLAY", "PLAYED", "RUN", "RAN", "MOVE", "MOVED",
            "LIVE", "LIVED", "BELIEVE", "BELIEVED", "HOLD", "HELD", "BRING",
            "BROUGHT", "HAPPEN", "HAPPENED", "WRITE", "WROTE", "SIT", "SAT",
            "STAND", "STOOD", "LOSE", "LOST", "PAY", "PAID", "MEET", "MET",
            "INCLUDE", "INCLUDED", "CONTINUE", "CONTINUED", "SET", "CHANGE",
            "CHANGED", "LEAD", "LED", "UNDERSTAND", "UNDERSTOOD", "WATCH",
            "WATCHED", "FOLLOW", "FOLLOWED", "STOP", "STOPPED", "CREATE",
            "CREATED", "SPEAK", "SPOKE", "READ", "ALLOW", "ALLOWED", "ADD",
            "ADDED", "SPEND", "SPENT", "GROW", "GREW", "OPEN", "OPENED",
            "WALK", "WALKED", "WIN", "WON", "OFFER", "OFFERED", "REMEMBER",
            "REMEMBERED", "LOVE", "LOVED", "CONSIDER", "CONSIDERED", "APPEAR",
            "APPEARED", "BUY", "BOUGHT", "WAIT", "WAITED", "SERVE", "SERVED",
            "DIE", "DIED", "SEND", "SENT", "EXPECT", "EXPECTED", "BUILD",
            "BUILT", "STAY", "STAYED", "FALL", "FELL", "CUT", "REACH",
            "REACHED", "KILL", "KILLED", "REMAIN", "REMAINED", "SUGGEST",
            "SUGGESTED", "RAISE", "RAISED", "PASS", "PASSED", "SELL", "SOLD",
            "REQUIRE", "REQUIRED", "REPORT", "REPORTED", "DECIDE", "DECIDED",
            "PULL", "PULLED"
        }
    
    def determine_data_type(self, url: str, data: Dict[str, Any]) -> str:
        """
        Determine the type of data based on URL and content.
        
        Args:
            url: The crawled URL
            data: The crawled data content
            
        Returns:
            Data type: 'financial', 'news', or 'generic'
        """
        url_lower = url.lower()
        
        # Check for financial domains
        if any(domain in url_lower for domain in self.financial_domains):
            return "financial"
        
        # Check URL patterns for financial indicators
        if any(indicator in url_lower for indicator in self.financial_indicators):
            return "financial"
        
        # Check URL patterns for news indicators
        if any(indicator in url_lower for indicator in self.news_indicators):
            return "news"
        
        # Check content for news indicators
        content_text = ""
        if isinstance(data, dict):
            # Extract text content from various fields
            content_text = " ".join([
                str(data.get("title", "")),
                str(data.get("content", "")),
                str(data.get("summary", "")),
                str(data.get("text", ""))
            ]).lower()
        elif isinstance(data, str):
            content_text = data.lower()
        
        # Check for news-like content
        if any(indicator in content_text for indicator in self.news_indicators):
            return "news"
        
        # Check for financial content indicators
        financial_content_indicators = [
            "stock", "price", "market", "trading", "financial", "earnings",
            "revenue", "profit", "dividend", "analyst", "investment"
        ]
        
        if any(indicator in content_text for indicator in financial_content_indicators):
            return "financial"
        
        return "generic"
    
    def extract_symbol_from_url(self, url: str) -> str:
        """
        Extract stock symbol from URL patterns.
        
        Args:
            url: The URL to extract symbol from
            
        Returns:
            Extracted stock symbol or "UNKNOWN"
        """
        url_upper = url.upper()
        
        for pattern in self.symbol_patterns:
            match = re.search(pattern, url_upper)
            if match:
                symbol = match.group(1)
                # Validate symbol length and format
                if 1 <= len(symbol) <= 5 and symbol.isalpha():
                    return symbol
        
        return "UNKNOWN"
    
    def extract_symbols_from_content(self, content: str) -> List[str]:
        """
        Extract stock symbols from content text.
        
        Args:
            content: Text content to extract symbols from
            
        Returns:
            List of extracted symbols (max 10 unique)
        """
        if not content:
            return []
        
        content_upper = content.upper()
        
        # Find potential symbols using regex
        symbol_pattern = r'\b([A-Z]{1,5})\b'
        potential_symbols = re.findall(symbol_pattern, content_upper)
        
        # Filter out common words
        symbols = [
            symbol for symbol in potential_symbols 
            if symbol not in self.exclude_words and len(symbol) >= 1
        ]
        
        # Remove duplicates and limit to 10
        unique_symbols = list(set(symbols))
        return unique_symbols[:10]
    
    def safe_float(self, value: Any) -> Optional[float]:
        """
        Safely convert value to float.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or None if conversion fails
        """
        if value is None:
            return None
        
        try:
            # Handle string values that might contain commas or currency symbols
            if isinstance(value, str):
                # Remove common formatting characters
                cleaned = re.sub(r'[,$€£¥₹%]', '', value.strip())
                # Remove parentheses (often used for negative values)
                cleaned = cleaned.replace('(', '-').replace(')', '')
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def safe_int(self, value: Any) -> Optional[int]:
        """
        Safely convert value to int.
        
        Args:
            value: Value to convert
            
        Returns:
            Integer value or None if conversion fails
        """
        if value is None:
            return None
        
        try:
            # Handle string values that might contain commas
            if isinstance(value, str):
                cleaned = re.sub(r'[,]', '', value.strip())
                return int(float(cleaned))  # Convert via float first to handle decimals
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def extract_financial_data_fields(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """
        Extract and normalize financial data fields from crawled data.
        
        Args:
            data: Raw crawled data
            url: Source URL
            
        Returns:
            Normalized financial data fields
        """
        return {
            "symbol": data.get("symbol") or self.extract_symbol_from_url(url),
            "price": self.safe_float(data.get("price")),
            "open_price": self.safe_float(data.get("open") or data.get("open_price")),
            "high_price": self.safe_float(data.get("high") or data.get("high_price")),
            "low_price": self.safe_float(data.get("low") or data.get("low_price")),
            "close_price": self.safe_float(data.get("close") or data.get("close_price")),
            "volume": self.safe_int(data.get("volume")),
            "change": self.safe_float(data.get("change")),
            "change_percent": self.safe_float(data.get("change_percent") or data.get("change_percentage")),
            "market_cap": self.safe_float(data.get("market_cap") or data.get("market_capitalization"))
        }
    
    def extract_news_data_fields(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """
        Extract and normalize news data fields from crawled data.
        
        Args:
            data: Raw crawled data
            url: Source URL
            
        Returns:
            Normalized news data fields
        """
        content = data.get("content", data.get("summary", ""))
        return {
            "title": data.get("title", ""),
            "content": content,
            "url": url,
            "symbols": self.extract_symbols_from_content(content),
            "sentiment": data.get("sentiment"),
            "category": data.get("category"),
            "author": data.get("author"),
            "published_at": data.get("published_at") or data.get("timestamp")
        }
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the classifier.
        
        Returns:
            Classification statistics
        """
        return {
            "financial_domains": len(self.financial_domains),
            "news_indicators": len(self.news_indicators),
            "financial_indicators": len(self.financial_indicators),
            "symbol_patterns": len(self.symbol_patterns),
            "exclude_words": len(self.exclude_words)
        }

