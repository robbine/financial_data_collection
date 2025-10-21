"""
Sentiment analysis plugin for financial data.
"""

from typing import Any, Dict, List, Optional
import re
import logging
from src.financial_data_collector.core.plugins.base import DataProcessorPlugin

logger = logging.getLogger(__name__)


class SentimentAnalysisPlugin(DataProcessorPlugin):
    """Plugin for analyzing sentiment in financial text data."""
    
    def __init__(self):
        super().__init__("SentimentAnalysis", "1.0.0")
        self.input_types = [str, dict, list]
        self.output_types = [dict]
        
        # Sentiment keywords
        self.positive_keywords = [
            'bullish', 'positive', 'growth', 'profit', 'gain', 'increase', 'rise',
            'strong', 'excellent', 'outperform', 'beat', 'surge', 'rally', 'boom',
            'optimistic', 'confident', 'upgrade', 'buy', 'outperform', 'strong buy'
        ]
        
        self.negative_keywords = [
            'bearish', 'negative', 'decline', 'loss', 'drop', 'decrease', 'fall',
            'weak', 'poor', 'underperform', 'miss', 'crash', 'plunge', 'recession',
            'pessimistic', 'concern', 'downgrade', 'sell', 'underperform', 'strong sell'
        ]
        
        self.neutral_keywords = [
            'stable', 'unchanged', 'neutral', 'hold', 'maintain', 'steady',
            'flat', 'sideways', 'consolidation', 'range-bound'
        ]
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the sentiment analysis plugin."""
        self.config = config
        
        # Load custom keywords if provided
        if 'positive_keywords' in config:
            self.positive_keywords.extend(config['positive_keywords'])
        
        if 'negative_keywords' in config:
            self.negative_keywords.extend(config['negative_keywords'])
        
        if 'neutral_keywords' in config:
            self.neutral_keywords.extend(config['neutral_keywords'])
        
        # Set sensitivity threshold
        self.sensitivity_threshold = config.get('sensitivity_threshold', 0.1)
        
        logger.info(f"SentimentAnalysis plugin initialized with {len(self.positive_keywords)} positive, "
                   f"{len(self.negative_keywords)} negative, and {len(self.neutral_keywords)} neutral keywords")
    
    def process_data(self, data: Any) -> Any:
        """Process data for sentiment analysis."""
        if isinstance(data, str):
            return self._analyze_text(data)
        elif isinstance(data, dict):
            return self._analyze_dict(data)
        elif isinstance(data, list):
            return self._analyze_list(data)
        else:
            raise ValueError(f"Unsupported data type for sentiment analysis: {type(data)}")
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a single text."""
        text_lower = text.lower()
        
        # Count keyword occurrences
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        neutral_count = sum(1 for word in self.neutral_keywords if word in text_lower)
        
        total_keywords = positive_count + negative_count + neutral_count
        
        if total_keywords == 0:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                "keyword_counts": {"positive": 0, "negative": 0, "neutral": 0}
            }
        
        # Calculate scores
        positive_score = positive_count / total_keywords
        negative_score = negative_count / total_keywords
        neutral_score = neutral_count / total_keywords
        
        # Determine sentiment
        if positive_score > negative_score and positive_score > neutral_score:
            sentiment = "positive"
            confidence = positive_score
        elif negative_score > positive_score and negative_score > neutral_score:
            sentiment = "negative"
            confidence = negative_score
        else:
            sentiment = "neutral"
            confidence = neutral_score
        
        # Apply sensitivity threshold
        if confidence < self.sensitivity_threshold:
            sentiment = "neutral"
            confidence = 0.0
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "scores": {
                "positive": positive_score,
                "negative": negative_score,
                "neutral": neutral_score
            },
            "keyword_counts": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            }
        }
    
    def _analyze_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of dictionary data."""
        results = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                results[key] = self._analyze_text(value)
            elif isinstance(value, dict):
                results[key] = self._analyze_dict(value)
            elif isinstance(value, list):
                results[key] = self._analyze_list(value)
        
        # Calculate overall sentiment
        if results:
            sentiments = [result.get("sentiment", "neutral") for result in results.values()]
            confidences = [result.get("confidence", 0.0) for result in results.values()]
            
            # Weighted average sentiment
            positive_weight = sum(conf for sent, conf in zip(sentiments, confidences) if sent == "positive")
            negative_weight = sum(conf for sent, conf in zip(sentiments, confidences) if sent == "negative")
            neutral_weight = sum(conf for sent, conf in zip(sentiments, confidences) if sent == "neutral")
            
            total_weight = positive_weight + negative_weight + neutral_weight
            
            if total_weight > 0:
                if positive_weight > negative_weight and positive_weight > neutral_weight:
                    overall_sentiment = "positive"
                    overall_confidence = positive_weight / total_weight
                elif negative_weight > positive_weight and negative_weight > neutral_weight:
                    overall_sentiment = "negative"
                    overall_confidence = negative_weight / total_weight
                else:
                    overall_sentiment = "neutral"
                    overall_confidence = neutral_weight / total_weight
            else:
                overall_sentiment = "neutral"
                overall_confidence = 0.0
            
            results["_overall"] = {
                "sentiment": overall_sentiment,
                "confidence": overall_confidence,
                "field_results": {k: v for k, v in results.items() if k != "_overall"}
            }
        
        return results
    
    def _analyze_list(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Analyze sentiment of list data."""
        results = []
        
        for item in data:
            if isinstance(item, str):
                results.append(self._analyze_text(item))
            elif isinstance(item, dict):
                results.append(self._analyze_dict(item))
            elif isinstance(item, list):
                results.append(self._analyze_list(item))
            else:
                results.append({
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "error": f"Unsupported item type: {type(item)}"
                })
        
        return results
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages."""
        return ["en"]  # English only for now
    
    def get_keyword_stats(self) -> Dict[str, int]:
        """Get keyword statistics."""
        return {
            "positive_keywords": len(self.positive_keywords),
            "negative_keywords": len(self.negative_keywords),
            "neutral_keywords": len(self.neutral_keywords)
        }
