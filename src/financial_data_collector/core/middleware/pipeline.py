"""
Data processing pipeline implementation.
"""

from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
from .base import Middleware, MiddlewarePipeline, MiddlewareRegistry

logger = logging.getLogger(__name__)


class DataProcessingPipeline(MiddlewarePipeline):
    """Specialized pipeline for data processing with predefined stages."""
    
    def __init__(self, name: str = "DataProcessingPipeline"):
        super().__init__(name)
        self._stages = {
            "preprocessing": [],
            "validation": [],
            "transformation": [],
            "postprocessing": []
        }
        self._stage_order = ["preprocessing", "validation", "transformation", "postprocessing"]
    
    def add_to_stage(self, stage: str, middleware: Middleware) -> 'DataProcessingPipeline':
        """
        Add middleware to a specific stage.
        
        Args:
            stage: Stage name (preprocessing, validation, transformation, postprocessing)
            middleware: Middleware to add
            
        Returns:
            Self for method chaining
        """
        if stage not in self._stages:
            raise ValueError(f"Invalid stage: {stage}. Valid stages: {list(self._stages.keys())}")
        
        self._stages[stage].append(middleware)
        return self
    
    def get_stage_middlewares(self, stage: str) -> List[Middleware]:
        """Get middlewares for a specific stage."""
        return self._stages.get(stage, [])
    
    async def process(self, data: Any) -> Any:
        """Process data through all stages."""
        current_data = data
        
        for stage in self._stage_order:
            stage_middlewares = self._stages[stage]
            if not stage_middlewares:
                continue
            
            logger.debug(f"Processing stage: {stage} with {len(stage_middlewares)} middlewares")
            
            # Create a mini-pipeline for this stage
            stage_pipeline = MiddlewarePipeline(f"{self.name}_{stage}")
            for middleware in stage_middlewares:
                stage_pipeline.add_middleware(middleware)
            
            # Process through stage
            current_data = await stage_pipeline.process(current_data)
        
        return current_data
    
    def get_stage_info(self) -> Dict[str, int]:
        """Get information about each stage."""
        return {stage: len(middlewares) for stage, middlewares in self._stages.items()}


class ConditionalPipeline(MiddlewarePipeline):
    """Pipeline that can conditionally execute different paths."""
    
    def __init__(self, name: str = "ConditionalPipeline"):
        super().__init__(name)
        self._conditions: List[tuple] = []  # (condition_func, pipeline)
        self._default_pipeline: Optional[MiddlewarePipeline] = None
    
    def add_condition(self, condition: callable, pipeline: MiddlewarePipeline) -> 'ConditionalPipeline':
        """
        Add a conditional pipeline.
        
        Args:
            condition: Function that returns True if this pipeline should be used
            pipeline: Pipeline to execute if condition is True
            
        Returns:
            Self for method chaining
        """
        self._conditions.append((condition, pipeline))
        return self
    
    def set_default_pipeline(self, pipeline: MiddlewarePipeline) -> 'ConditionalPipeline':
        """
        Set the default pipeline to use if no conditions match.
        
        Args:
            pipeline: Default pipeline
            
        Returns:
            Self for method chaining
        """
        self._default_pipeline = pipeline
        return self
    
    async def process(self, data: Any) -> Any:
        """Process data through conditional pipelines."""
        # Check conditions in order
        for condition, pipeline in self._conditions:
            if condition(data):
                logger.debug(f"Condition matched, using pipeline: {pipeline.name}")
                return await pipeline.process(data)
        
        # Use default pipeline if no conditions matched
        if self._default_pipeline:
            logger.debug(f"No conditions matched, using default pipeline: {self._default_pipeline.name}")
            return await self._default_pipeline.process(data)
        
        # Return original data if no pipeline to use
        logger.warning("No conditions matched and no default pipeline set")
        return data


class ParallelPipeline(MiddlewarePipeline):
    """Pipeline that can process data through multiple parallel paths."""
    
    def __init__(self, name: str = "ParallelPipeline"):
        super().__init__(name)
        self._parallel_pipelines: List[MiddlewarePipeline] = []
        self._merge_strategy: str = "first"  # first, last, merge, combine
    
    def add_parallel_pipeline(self, pipeline: MiddlewarePipeline) -> 'ParallelPipeline':
        """
        Add a parallel pipeline.
        
        Args:
            pipeline: Pipeline to run in parallel
            
        Returns:
            Self for method chaining
        """
        self._parallel_pipelines.append(pipeline)
        return self
    
    def set_merge_strategy(self, strategy: str) -> 'ParallelPipeline':
        """
        Set the merge strategy for parallel results.
        
        Args:
            strategy: Merge strategy (first, last, merge, combine)
            
        Returns:
            Self for method chaining
        """
        valid_strategies = ["first", "last", "merge", "combine"]
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid merge strategy: {strategy}. Valid strategies: {valid_strategies}")
        
        self._merge_strategy = strategy
        return self
    
    async def process(self, data: Any) -> Any:
        """Process data through parallel pipelines."""
        if not self._parallel_pipelines:
            return data
        
        # Run all pipelines in parallel
        tasks = [pipeline.process(data) for pipeline in self._parallel_pipelines]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        if not valid_results:
            logger.error("All parallel pipelines failed")
            return data
        
        # Merge results based on strategy
        if self._merge_strategy == "first":
            return valid_results[0]
        elif self._merge_strategy == "last":
            return valid_results[-1]
        elif self._merge_strategy == "merge":
            if isinstance(valid_results[0], dict):
                merged = {}
                for result in valid_results:
                    if isinstance(result, dict):
                        merged.update(result)
                return merged
            else:
                return valid_results[0]
        elif self._merge_strategy == "combine":
            return valid_results
        
        return valid_results[0]


class PipelineBuilder:
    """Builder for creating complex data processing pipelines."""
    
    def __init__(self):
        self._registry = MiddlewareRegistry()
        self._pipelines: Dict[str, MiddlewarePipeline] = {}
    
    def register_middleware(self, name: str, middleware: Middleware) -> 'PipelineBuilder':
        """Register a middleware."""
        self._registry.register_middleware(name, middleware)
        return self
    
    def create_pipeline(self, name: str) -> 'PipelineBuilder':
        """Create a new pipeline."""
        self._pipelines[name] = MiddlewarePipeline(name)
        return self
    
    def create_data_processing_pipeline(self, name: str) -> 'PipelineBuilder':
        """Create a data processing pipeline."""
        self._pipelines[name] = DataProcessingPipeline(name)
        return self
    
    def create_conditional_pipeline(self, name: str) -> 'PipelineBuilder':
        """Create a conditional pipeline."""
        self._pipelines[name] = ConditionalPipeline(name)
        return self
    
    def create_parallel_pipeline(self, name: str) -> 'PipelineBuilder':
        """Create a parallel pipeline."""
        self._pipelines[name] = ParallelPipeline(name)
        return self
    
    def add_middleware_to_pipeline(self, pipeline_name: str, middleware: Middleware) -> 'PipelineBuilder':
        """Add middleware to a pipeline."""
        if pipeline_name in self._pipelines:
            self._pipelines[pipeline_name].add_middleware(middleware)
        return self
    
    def get_pipeline(self, name: str) -> Optional[MiddlewarePipeline]:
        """Get a pipeline by name."""
        return self._pipelines.get(name)
    
    def build(self) -> Dict[str, MiddlewarePipeline]:
        """Build and return all pipelines."""
        return self._pipelines.copy()
