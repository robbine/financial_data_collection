"""
Validation middleware implementation.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import json
import jsonschema
import logging
from .base import Middleware

logger = logging.getLogger(__name__)


class ValidationMiddleware(Middleware):
    """Middleware for data validation."""
    
    def __init__(self, schema: Optional[Dict] = None, required_fields: Optional[List[str]] = None):
        super().__init__("ValidationMiddleware")
        self.schema = schema
        self.required_fields = required_fields or []
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with validation."""
        # Validate required fields
        if self.required_fields:
            self._validate_required_fields(data)
        
        # Validate JSON schema if provided
        if self.schema:
            self._validate_schema(data)
        
        # Process through next middleware
        return await next_middleware()
    
    def _validate_required_fields(self, data: Any) -> None:
        """Validate required fields."""
        if isinstance(data, dict):
            missing_fields = [field for field in self.required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
        else:
            raise ValueError(f"Data must be a dictionary for field validation, got {type(data)}")
    
    def _validate_schema(self, data: Any) -> None:
        """Validate data against JSON schema."""
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Schema validation failed: {e.message}")
        except jsonschema.SchemaError as e:
            raise ValueError(f"Invalid schema: {e.message}")


class TypeValidationMiddleware(Middleware):
    """Middleware for type validation."""
    
    def __init__(self, expected_types: Union[type, List[type]]):
        super().__init__("TypeValidationMiddleware")
        if isinstance(expected_types, type):
            self.expected_types = [expected_types]
        else:
            self.expected_types = expected_types
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with type validation."""
        if not isinstance(data, tuple(self.expected_types)):
            raise TypeError(f"Expected data of type {self.expected_types}, got {type(data)}")
        
        return await next_middleware()


class RangeValidationMiddleware(Middleware):
    """Middleware for range validation."""
    
    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        super().__init__("RangeValidationMiddleware")
        self.min_value = min_value
        self.max_value = max_value
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with range validation."""
        if isinstance(data, (int, float)):
            if self.min_value is not None and data < self.min_value:
                raise ValueError(f"Value {data} is below minimum {self.min_value}")
            if self.max_value is not None and data > self.max_value:
                raise ValueError(f"Value {data} is above maximum {self.max_value}")
        elif isinstance(data, dict):
            # Validate numeric values in dictionary
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if self.min_value is not None and value < self.min_value:
                        raise ValueError(f"Value {value} for key '{key}' is below minimum {self.min_value}")
                    if self.max_value is not None and value > self.max_value:
                        raise ValueError(f"Value {value} for key '{key}' is above maximum {self.max_value}")
        
        return await next_middleware()


class DataQualityMiddleware(Middleware):
    """Middleware for data quality checks."""
    
    def __init__(self, 
                 check_null: bool = True,
                 check_empty: bool = True,
                 check_duplicates: bool = False,
                 null_threshold: float = 0.5):
        super().__init__("DataQualityMiddleware")
        self.check_null = check_null
        self.check_empty = check_empty
        self.check_duplicates = check_duplicates
        self.null_threshold = null_threshold
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with quality checks."""
        if isinstance(data, dict):
            self._check_dict_quality(data)
        elif isinstance(data, list):
            self._check_list_quality(data)
        
        return await next_middleware()
    
    def _check_dict_quality(self, data: Dict) -> None:
        """Check quality of dictionary data."""
        if not data:
            raise ValueError("Data is empty")
        
        if self.check_null:
            null_count = sum(1 for v in data.values() if v is None)
            null_ratio = null_count / len(data)
            if null_ratio > self.null_threshold:
                raise ValueError(f"Too many null values: {null_ratio:.2%} (threshold: {self.null_threshold:.2%})")
        
        if self.check_empty:
            empty_count = sum(1 for v in data.values() if v == "" or v == [])
            if empty_count > 0:
                logger.warning(f"Found {empty_count} empty values in data")
    
    def _check_list_quality(self, data: List) -> None:
        """Check quality of list data."""
        if not data:
            raise ValueError("Data list is empty")
        
        if self.check_duplicates:
            if len(data) != len(set(data)):
                logger.warning("Found duplicate values in data list")
        
        if self.check_null:
            null_count = sum(1 for v in data if v is None)
            null_ratio = null_count / len(data)
            if null_ratio > self.null_threshold:
                raise ValueError(f"Too many null values: {null_ratio:.2%} (threshold: {self.null_threshold:.2%})")
