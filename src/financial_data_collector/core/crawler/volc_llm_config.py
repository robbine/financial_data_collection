"""
Volcano Engine LLM Configuration for Crawl4AI

This module provides configuration for using Volcano Engine API with Crawl4AI
for financial data extraction.
"""

import os
from typing import Dict, Any, Optional
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import LLMConfig

class VolcLLMConfig:
    """Volcano Engine LLM configuration for Crawl4AI."""
    
    def __init__(self, api_key: str, base_url: str, model: str = "ep-20250725215501-7zrfm"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration for Crawl4AI."""
        return LLMConfig(
            provider=f"openai/{self.model}",  # Use OpenAI format with model name
            api_token=self.api_key,
            base_url=self.base_url
        )
    
    def get_extraction_strategy(self, instruction: str, schema: Dict[str, Any]) -> LLMExtractionStrategy:
        """Get LLM extraction strategy with Volcano Engine configuration."""
        llm_config = LLMConfig(
            provider=f"openai/{self.model}",
            api_token=self.api_key,
            base_url=self.base_url
        )
        return LLMExtractionStrategy(
            llm_config=llm_config,
            instruction=instruction,
            schema=schema
        )


def create_volc_llm_strategy(
    api_key: str, 
    base_url: str, 
    model: str = "ep-20250725215501-7zrfm",
    instruction: str = None,
    schema: Dict[str, Any] = None
) -> LLMExtractionStrategy:
    """
    Create LLM extraction strategy using Volcano Engine API.
    
    Args:
        api_key: Volcano Engine API key
        base_url: Volcano Engine base URL
        model: Model name (default: ep-20250725215501-7zrfm)
        instruction: Custom instruction for extraction
        schema: JSON schema for structured output
    
    Returns:
        LLMExtractionStrategy configured for Volcano Engine
    """
    
    # Default instruction for financial data extraction
    if instruction is None:
        instruction = """
        Extract financial data from the webpage. Focus on:
        1. Stock prices, volume, and market data
        2. Company information and financial metrics
        3. News articles and financial reports
        4. Market trends and analysis
        
        Return structured data with clear categorization of financial information.
        """
    
    # Default schema for financial data
    if schema is None:
        schema = {
            "type": "object",
            "properties": {
                "stock_data": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "price": {"type": "number"},
                        "volume": {"type": "number"},
                        "change": {"type": "number"},
                        "change_percent": {"type": "number"},
                        "market_cap": {"type": "number"}
                    }
                },
                "news": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "url": {"type": "string"}
                        }
                    }
                },
                "company_info": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "sector": {"type": "string"},
                        "industry": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
        }
    
    # Create LLMConfig for Volcano Engine
    llm_config = LLMConfig(
        provider=f"openai/{model}",  # Use OpenAI format with model name
        api_token=api_key,
        base_url=base_url
    )
    
    return LLMExtractionStrategy(
        llm_config=llm_config,
        instruction=instruction,
        schema=schema
    )


def get_volc_llm_config_from_env() -> Optional[VolcLLMConfig]:
    """Get Volcano Engine LLM configuration from environment variables."""
    api_key = os.getenv("VOLC_API_KEY")
    base_url = os.getenv("VOLC_BASE_URL")
    
    if api_key and base_url:
        return VolcLLMConfig(api_key, base_url)
    
    return None


# Example usage and configuration
def example_volc_configuration():
    """Example of how to configure Volcano Engine with Crawl4AI."""
    
    # Method 1: Direct configuration
    volc_config = VolcLLMConfig(
        api_key="your_volc_api_key",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        model="ep-20250725215501-7zrfm"
    )
    
    # Method 2: From environment variables
    volc_config = get_volc_llm_config_from_env()
    
    if volc_config:
        llm_config = volc_config.get_llm_config()
        extraction_strategy = volc_config.get_extraction_strategy(
            instruction="Extract financial data from the webpage",
            schema={
                "type": "object",
                "properties": {
                    "financial_data": {"type": "object"}
                }
            }
        )
        
        return llm_config, extraction_strategy
    
    return None, None
