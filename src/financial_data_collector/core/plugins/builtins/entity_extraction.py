"""
Entity extraction plugin for financial data.
"""

from typing import Any, Dict, List, Optional, Set
import re
import logging
from datetime import datetime
from ..base import DataProcessorPlugin

logger = logging.getLogger(__name__)


class EntityExtractionPlugin(DataProcessorPlugin):
    """Plugin for extracting entities from financial text data."""
    
    def __init__(self):
        super().__init__("EntityExtraction", "1.0.0")
        self.input_types = [str, dict, list]
        self.output_types = [dict]
        
        # Financial entity patterns
        self.entity_patterns = {
            'ticker': r'\b[A-Z]{1,5}\b',  # Stock tickers
            'currency': r'\$[\d,]+\.?\d*',  # Currency amounts
            'percentage': r'\d+\.?\d*%',   # Percentages
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Dates
            'time': r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',  # Times
            'price': r'\$\d+\.?\d*',  # Prices
            'volume': r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:shares?|units?)\b',  # Volume
            'market_cap': r'\$\d+(?:\.\d+)?[BMK]',  # Market cap (B, M, K)
            'pe_ratio': r'P/E\s*:?\s*\d+\.?\d*',  # P/E ratio
            'dividend': r'\d+\.?\d*%\s*dividend',  # Dividend yield
        }
        
        # Company name patterns
        self.company_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|Corporation|Company|Ltd|Limited|LLC|LP|L\.P\.)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Group|Holdings|International|Global|Systems|Technologies)\b',
        ]
        
        # Financial terms
        self.financial_terms = {
            'revenue', 'profit', 'earnings', 'income', 'sales', 'revenue', 'assets',
            'liabilities', 'equity', 'debt', 'cash', 'investment', 'portfolio',
            'dividend', 'yield', 'return', 'growth', 'margin', 'ratio', 'valuation'
        }
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the entity extraction plugin."""
        self.config = config
        
        # Load custom patterns if provided
        if 'custom_patterns' in config:
            self.entity_patterns.update(config['custom_patterns'])
        
        if 'custom_company_patterns' in config:
            self.company_patterns.extend(config['custom_company_patterns'])
        
        if 'custom_financial_terms' in config:
            self.financial_terms.update(config['custom_financial_terms'])
        
        # Set extraction options
        self.extract_confidence = config.get('extract_confidence', True)
        self.min_confidence = config.get('min_confidence', 0.5)
        
        logger.info(f"EntityExtraction plugin initialized with {len(self.entity_patterns)} patterns")
    
    def process_data(self, data: Any) -> Any:
        """Process data for entity extraction."""
        if isinstance(data, str):
            return self._extract_from_text(data)
        elif isinstance(data, dict):
            return self._extract_from_dict(data)
        elif isinstance(data, list):
            return self._extract_from_list(data)
        else:
            raise ValueError(f"Unsupported data type for entity extraction: {type(data)}")
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract entities from a single text."""
        entities = {}
        
        # Extract using regex patterns
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates
        
        # Extract company names
        company_matches = []
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            company_matches.extend(matches)
        
        if company_matches:
            entities['companies'] = list(set(company_matches))
        
        # Extract financial terms
        financial_terms_found = []
        text_lower = text.lower()
        for term in self.financial_terms:
            if term.lower() in text_lower:
                financial_terms_found.append(term)
        
        if financial_terms_found:
            entities['financial_terms'] = financial_terms_found
        
        # Calculate confidence scores if enabled
        if self.extract_confidence:
            entities = self._add_confidence_scores(entities, text)
        
        return {
            "entities": entities,
            "extraction_metadata": {
                "text_length": len(text),
                "entity_types_found": len(entities),
                "total_entities": sum(len(v) if isinstance(v, list) else 1 for v in entities.values())
            }
        }
    
    def _extract_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from dictionary data."""
        results = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                results[key] = self._extract_from_text(value)
            elif isinstance(value, dict):
                results[key] = self._extract_from_dict(value)
            elif isinstance(value, list):
                results[key] = self._extract_from_list(value)
        
        # Merge all entities
        all_entities = {}
        for result in results.values():
            if isinstance(result, dict) and 'entities' in result:
                for entity_type, entities in result['entities'].items():
                    if entity_type not in all_entities:
                        all_entities[entity_type] = []
                    if isinstance(entities, list):
                        all_entities[entity_type].extend(entities)
                    else:
                        all_entities[entity_type].append(entities)
        
        # Remove duplicates
        for entity_type in all_entities:
            all_entities[entity_type] = list(set(all_entities[entity_type]))
        
        return {
            "entities": all_entities,
            "field_results": results,
            "extraction_metadata": {
                "fields_processed": len(results),
                "entity_types_found": len(all_entities)
            }
        }
    
    def _extract_from_list(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Extract entities from list data."""
        results = []
        
        for item in data:
            if isinstance(item, str):
                results.append(self._extract_from_text(item))
            elif isinstance(item, dict):
                results.append(self._extract_from_dict(item))
            elif isinstance(item, list):
                results.append(self._extract_from_list(item))
            else:
                results.append({
                    "entities": {},
                    "extraction_metadata": {
                        "error": f"Unsupported item type: {type(item)}"
                    }
                })
        
        return results
    
    def _add_confidence_scores(self, entities: Dict[str, List[str]], text: str) -> Dict[str, Any]:
        """Add confidence scores to extracted entities."""
        scored_entities = {}
        
        for entity_type, entity_list in entities.items():
            scored_list = []
            for entity in entity_list:
                # Simple confidence calculation based on pattern match strength
                confidence = self._calculate_entity_confidence(entity, entity_type, text)
                
                if confidence >= self.min_confidence:
                    scored_list.append({
                        "value": entity,
                        "confidence": confidence
                    })
            
            if scored_list:
                scored_entities[entity_type] = scored_list
        
        return scored_entities
    
    def _calculate_entity_confidence(self, entity: str, entity_type: str, text: str) -> float:
        """Calculate confidence score for an entity."""
        # Base confidence
        confidence = 0.5
        
        # Adjust based on entity type
        if entity_type == 'ticker':
            # Tickers should be short and uppercase
            if len(entity) <= 5 and entity.isupper():
                confidence += 0.3
        elif entity_type == 'currency':
            # Currency should have $ and numbers
            if '$' in entity and any(c.isdigit() for c in entity):
                confidence += 0.3
        elif entity_type == 'percentage':
            # Percentage should end with %
            if entity.endswith('%'):
                confidence += 0.3
        elif entity_type == 'companies':
            # Company names should have common suffixes
            company_suffixes = ['Inc', 'Corp', 'Corporation', 'Company', 'Ltd', 'Limited', 'LLC']
            if any(suffix in entity for suffix in company_suffixes):
                confidence += 0.3
        
        # Adjust based on context (appears multiple times)
        entity_count = text.lower().count(entity.lower())
        if entity_count > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_supported_entity_types(self) -> List[str]:
        """Get supported entity types."""
        return list(self.entity_patterns.keys()) + ['companies', 'financial_terms']
    
    def add_custom_pattern(self, entity_type: str, pattern: str) -> None:
        """Add a custom entity pattern."""
        self.entity_patterns[entity_type] = pattern
        logger.info(f"Added custom pattern for {entity_type}: {pattern}")
    
    def get_pattern_stats(self) -> Dict[str, int]:
        """Get pattern statistics."""
        return {
            "entity_patterns": len(self.entity_patterns),
            "company_patterns": len(self.company_patterns),
            "financial_terms": len(self.financial_terms)
        }
