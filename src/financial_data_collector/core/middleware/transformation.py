"""
Transformation middleware implementation.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import json
import pandas as pd
from datetime import datetime
import logging
from .base import Middleware

logger = logging.getLogger(__name__)


class TransformationMiddleware(Middleware):
    """Base middleware for data transformation."""
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "TransformationMiddleware")
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with transformation."""
        transformed_data = self.transform(data)
        return await next_middleware()
    
    def transform(self, data: Any) -> Any:
        """Transform the data. Override in subclasses."""
        return data


class JSONTransformMiddleware(TransformationMiddleware):
    """Middleware for JSON data transformation."""
    
    def __init__(self, 
                 pretty_print: bool = False,
                 ensure_ascii: bool = False,
                 sort_keys: bool = False):
        super().__init__("JSONTransformMiddleware")
        self.pretty_print = pretty_print
        self.ensure_ascii = ensure_ascii
        self.sort_keys = sort_keys
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with JSON transformation."""
        # Convert to JSON string if needed
        if not isinstance(data, str):
            data = json.dumps(data, ensure_ascii=self.ensure_ascii, sort_keys=self.sort_keys)
        
        # Pretty print if requested
        if self.pretty_print:
            try:
                parsed = json.loads(data)
                data = json.dumps(parsed, indent=2, ensure_ascii=self.ensure_ascii, sort_keys=self.sort_keys)
            except json.JSONDecodeError:
                pass  # Keep original if not valid JSON
        
        return await next_middleware()


class DataFrameTransformMiddleware(TransformationMiddleware):
    """Middleware for DataFrame transformation."""
    
    def __init__(self, 
                 columns: Optional[List[str]] = None,
                 drop_na: bool = False,
                 fill_na: Optional[Any] = None,
                 rename_columns: Optional[Dict[str, str]] = None):
        super().__init__("DataFrameTransformMiddleware")
        self.columns = columns
        self.drop_na = drop_na
        self.fill_na = fill_na
        self.rename_columns = rename_columns or {}
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with DataFrame transformation."""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
            
            # Select specific columns
            if self.columns:
                df = df[self.columns]
            
            # Rename columns
            if self.rename_columns:
                df = df.rename(columns=self.rename_columns)
            
            # Handle missing values
            if self.drop_na:
                df = df.dropna()
            elif self.fill_na is not None:
                df = df.fillna(self.fill_na)
            
            return await next_middleware()
        else:
            return await next_middleware()


class DataTypeTransformMiddleware(TransformationMiddleware):
    """Middleware for data type transformation."""
    
    def __init__(self, 
                 string_fields: Optional[List[str]] = None,
                 numeric_fields: Optional[List[str]] = None,
                 date_fields: Optional[List[str]] = None,
                 date_format: str = "%Y-%m-%d"):
        super().__init__("DataTypeTransformMiddleware")
        self.string_fields = string_fields or []
        self.numeric_fields = numeric_fields or []
        self.date_fields = date_fields or []
        self.date_format = date_format
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with type transformation."""
        if isinstance(data, dict):
            transformed_data = data.copy()
            
            # Convert string fields
            for field in self.string_fields:
                if field in transformed_data:
                    transformed_data[field] = str(transformed_data[field])
            
            # Convert numeric fields
            for field in self.numeric_fields:
                if field in transformed_data:
                    try:
                        transformed_data[field] = float(transformed_data[field])
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert field '{field}' to numeric")
            
            # Convert date fields
            for field in self.date_fields:
                if field in transformed_data:
                    try:
                        if isinstance(transformed_data[field], str):
                            transformed_data[field] = datetime.strptime(transformed_data[field], self.date_format)
                        elif isinstance(transformed_data[field], datetime):
                            pass  # Already a datetime
                    except ValueError:
                        logger.warning(f"Could not convert field '{field}' to date using format '{self.date_format}'")
            
            return await next_middleware()
        else:
            return await next_middleware()


class FilterTransformMiddleware(TransformationMiddleware):
    """Middleware for data filtering."""
    
    def __init__(self, 
                 filter_condition: Optional[Callable] = None,
                 include_fields: Optional[List[str]] = None,
                 exclude_fields: Optional[List[str]] = None):
        super().__init__("FilterTransformMiddleware")
        self.filter_condition = filter_condition
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields or []
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with filtering."""
        if isinstance(data, dict):
            filtered_data = data.copy()
            
            # Apply field inclusion/exclusion
            if self.include_fields:
                filtered_data = {k: v for k, v in filtered_data.items() if k in self.include_fields}
            
            if self.exclude_fields:
                filtered_data = {k: v for k, v in filtered_data.items() if k not in self.exclude_fields}
            
            # Apply custom filter condition
            if self.filter_condition:
                filtered_data = {k: v for k, v in filtered_data.items() if self.filter_condition(k, v)}
            
            return await next_middleware()
        else:
            return await next_middleware()


class AggregationTransformMiddleware(TransformationMiddleware):
    """Middleware for data aggregation."""
    
    def __init__(self, 
                 group_by: Optional[str] = None,
                 aggregations: Optional[Dict[str, str]] = None):
        super().__init__("AggregationTransformMiddleware")
        self.group_by = group_by
        self.aggregations = aggregations or {}
    
    async def process(self, data: Any, next_middleware: Callable) -> Any:
        """Process data with aggregation."""
        if isinstance(data, list) and self.group_by:
            # Group data by specified field
            grouped_data = {}
            for item in data:
                if isinstance(item, dict) and self.group_by in item:
                    key = item[self.group_by]
                    if key not in grouped_data:
                        grouped_data[key] = []
                    grouped_data[key].append(item)
            
            # Apply aggregations
            if self.aggregations:
                aggregated_data = {}
                for group_key, group_items in grouped_data.items():
                    aggregated_item = {self.group_by: group_key}
                    for field, agg_func in self.aggregations.items():
                        values = [item.get(field) for item in group_items if field in item]
                        if values:
                            if agg_func == "sum":
                                aggregated_item[field] = sum(v for v in values if isinstance(v, (int, float)))
                            elif agg_func == "avg":
                                numeric_values = [v for v in values if isinstance(v, (int, float))]
                                aggregated_item[field] = sum(numeric_values) / len(numeric_values) if numeric_values else 0
                            elif agg_func == "count":
                                aggregated_item[field] = len(values)
                            elif agg_func == "max":
                                aggregated_item[field] = max(values)
                            elif agg_func == "min":
                                aggregated_item[field] = min(values)
                    aggregated_data[group_key] = aggregated_item
                
                return await next_middleware()
        
        return await next_middleware()
