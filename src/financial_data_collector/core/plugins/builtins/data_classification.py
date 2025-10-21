"""
Data classification plugin for financial data.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import logging
from datetime import datetime
from src.financial_data_collector.core.plugins.base import DataProcessorPlugin

logger = logging.getLogger(__name__)


class DataClassificationPlugin(DataProcessorPlugin):
    """Plugin for classifying financial data into categories."""
    
    def __init__(self):
        super().__init__("DataClassification", "1.0.0")
        self.input_types = [str, dict, list]
        self.output_types = [dict]
        
        # Classification rules
        self.classification_rules = {
            'news': {
                'keywords': ['news', 'report', 'announcement', 'update', 'breaking', 'alert'],
                'patterns': [r'\b(?:news|report|announcement|update|breaking|alert)\b'],
                'confidence': 0.8
            },
            'analysis': {
                'keywords': ['analysis', 'research', 'study', 'report', 'insight', 'forecast'],
                'patterns': [r'\b(?:analysis|research|study|insight|forecast|prediction)\b'],
                'confidence': 0.8
            },
            'market_data': {
                'keywords': ['price', 'volume', 'trading', 'market', 'stock', 'quote'],
                'patterns': [r'\b(?:price|volume|trading|market|stock|quote|chart)\b'],
                'confidence': 0.9
            },
            'earnings': {
                'keywords': ['earnings', 'revenue', 'profit', 'income', 'quarterly', 'annual'],
                'patterns': [r'\b(?:earnings|revenue|profit|income|quarterly|annual|EPS)\b'],
                'confidence': 0.9
            },
            'regulatory': {
                'keywords': ['SEC', 'filing', 'regulation', 'compliance', 'legal', 'audit'],
                'patterns': [r'\b(?:SEC|filing|regulation|compliance|legal|audit|regulatory)\b'],
                'confidence': 0.9
            },
            'social_media': {
                'keywords': ['tweet', 'post', 'social', 'twitter', 'facebook', 'reddit'],
                'patterns': [r'\b(?:tweet|post|social|twitter|facebook|reddit|instagram)\b'],
                'confidence': 0.8
            },
            'research': {
                'keywords': ['research', 'study', 'survey', 'poll', 'data', 'statistics'],
                'patterns': [r'\b(?:research|study|survey|poll|data|statistics|findings)\b'],
                'confidence': 0.8
            }
        }
        
        # Data source patterns
        self.source_patterns = {
            'news_sites': [r'(?:reuters|bloomberg|cnbc|yahoo|marketwatch|wsj|ft)\.com'],
            'social_platforms': [r'(?:twitter|facebook|reddit|linkedin)\.com'],
            'financial_data': [r'(?:yahoo|google|alpha|quandl|fred)\.com'],
            'regulatory': [r'(?:sec\.gov|edgar|federalreserve)\.gov']
        }
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the data classification plugin."""
        self.config = config
        
        # Load custom rules if provided
        if 'custom_rules' in config:
            self.classification_rules.update(config['custom_rules'])
        
        if 'custom_source_patterns' in config:
            self.source_patterns.update(config['custom_source_patterns'])
        
        # Set classification options
        self.multi_class = config.get('multi_class', True)
        self.min_confidence = config.get('min_confidence', 0.3)
        self.include_metadata = config.get('include_metadata', True)
        
        logger.info(f"DataClassification plugin initialized with {len(self.classification_rules)} rules")
    
    def process_data(self, data: Any) -> Any:
        """Process data for classification."""
        if isinstance(data, str):
            return self._classify_text(data)
        elif isinstance(data, dict):
            return self._classify_dict(data)
        elif isinstance(data, list):
            return self._classify_list(data)
        else:
            raise ValueError(f"Unsupported data type for classification: {type(data)}")
    
    def _classify_text(self, text: str) -> Dict[str, Any]:
        """Classify a single text."""
        classifications = {}
        text_lower = text.lower()
        
        # Apply classification rules
        for category, rule in self.classification_rules.items():
            confidence = self._calculate_confidence(text_lower, rule)
            
            if confidence >= self.min_confidence:
                classifications[category] = {
                    'confidence': confidence,
                    'matched_keywords': self._find_matched_keywords(text_lower, rule['keywords']),
                    'matched_patterns': self._find_matched_patterns(text, rule['patterns'])
                }
        
        # Determine primary classification
        if classifications:
            primary_category = max(classifications.keys(), 
                                  key=lambda k: classifications[k]['confidence'])
            primary_confidence = classifications[primary_category]['confidence']
        else:
            primary_category = 'unknown'
            primary_confidence = 0.0
        
        result = {
            'primary_classification': primary_category,
            'primary_confidence': primary_confidence,
            'all_classifications': classifications
        }
        
        if self.include_metadata:
            result['metadata'] = self._extract_metadata(text)
        
        return result
    
    def _classify_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify dictionary data."""
        results = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                results[key] = self._classify_text(value)
            elif isinstance(value, dict):
                results[key] = self._classify_dict(value)
            elif isinstance(value, list):
                results[key] = self._classify_list(value)
        
        # Merge classifications
        all_classifications = {}
        for result in results.values():
            if isinstance(result, dict) and 'all_classifications' in result:
                for category, info in result['all_classifications'].items():
                    if category not in all_classifications:
                        all_classifications[category] = {
                            'confidence': 0.0,
                            'matched_keywords': [],
                            'matched_patterns': []
                        }
                    
                    # Take the highest confidence
                    if info['confidence'] > all_classifications[category]['confidence']:
                        all_classifications[category] = info
        
        # Determine overall primary classification
        if all_classifications:
            primary_category = max(all_classifications.keys(),
                                  key=lambda k: all_classifications[k]['confidence'])
            primary_confidence = all_classifications[primary_category]['confidence']
        else:
            primary_category = 'unknown'
            primary_confidence = 0.0
        
        return {
            'primary_classification': primary_category,
            'primary_confidence': primary_confidence,
            'all_classifications': all_classifications,
            'field_results': results
        }
    
    def _classify_list(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Classify list data."""
        results = []
        
        for item in data:
            if isinstance(item, str):
                results.append(self._classify_text(item))
            elif isinstance(item, dict):
                results.append(self._classify_dict(item))
            elif isinstance(item, list):
                results.append(self._classify_list(item))
            else:
                results.append({
                    'primary_classification': 'unknown',
                    'primary_confidence': 0.0,
                    'all_classifications': {},
                    'error': f"Unsupported item type: {type(item)}"
                })
        
        return results
    
    def _calculate_confidence(self, text: str, rule: Dict[str, Any]) -> float:
        """Calculate confidence score for a classification rule."""
        confidence = 0.0
        
        # Check keywords
        keyword_matches = sum(1 for keyword in rule['keywords'] if keyword in text)
        if keyword_matches > 0:
            confidence += (keyword_matches / len(rule['keywords'])) * 0.6
        
        # Check patterns
        pattern_matches = 0
        for pattern in rule['patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_matches += 1
        
        if pattern_matches > 0:
            confidence += (pattern_matches / len(rule['patterns'])) * 0.4
        
        # Apply rule-specific confidence multiplier
        confidence *= rule.get('confidence', 1.0)
        
        return min(confidence, 1.0)
    
    def _find_matched_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find matched keywords in text."""
        return [keyword for keyword in keywords if keyword in text]
    
    def _find_matched_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Find matched patterns in text."""
        matched = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matched.append(pattern)
        return matched
    
    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text."""
        metadata = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'sentence_count': len(re.split(r'[.!?]+', text)),
            'has_numbers': bool(re.search(r'\d', text)),
            'has_urls': bool(re.search(r'http[s]?://', text)),
            'has_emails': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        }
        
        # Detect data source
        source_type = 'unknown'
        for source_category, patterns in self.source_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    source_type = source_category
                    break
            if source_type != 'unknown':
                break
        
        metadata['detected_source'] = source_type
        
        return metadata
    
    def add_classification_rule(self, category: str, rule: Dict[str, Any]) -> None:
        """Add a custom classification rule."""
        self.classification_rules[category] = rule
        logger.info(f"Added classification rule for {category}")
    
    def get_supported_categories(self) -> List[str]:
        """Get supported classification categories."""
        return list(self.classification_rules.keys())
    
    def get_rule_stats(self) -> Dict[str, int]:
        """Get classification rule statistics."""
        return {
            "total_rules": len(self.classification_rules),
            "total_keywords": sum(len(rule['keywords']) for rule in self.classification_rules.values()),
            "total_patterns": sum(len(rule['patterns']) for rule in self.classification_rules.values())
        }
