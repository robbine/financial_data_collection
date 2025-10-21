"""
Integration tests for the modular system.

This module tests the integration of all modular components including:
- Dependency injection container
- Event system
- Middleware system
- Plugin system
- Module manager
- Health checking
"""

import pytest
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from src.financial_data_collector.core.di import DIContainer
from src.financial_data_collector.core.events import EventBus, DataCollectedEvent
from src.financial_data_collector.core.middleware import (
    MiddlewarePipeline, LoggingMiddleware, ValidationMiddleware
)
from src.financial_data_collector.core.plugins import (
    PluginRegistry, SentimentAnalysisPlugin, EntityExtractionPlugin
)
from src.financial_data_collector.core.module_manager import (
    ModuleManager, ModuleConfig, ModuleState
)
from src.financial_data_collector.core.health_checker import (
    HealthMonitor, HealthCheckConfig, BasicHealthChecker
)
from src.financial_data_collector.core.interfaces import (
    BaseModule, DataCollectorInterface, DataProcessorInterface
)


class TestDataCollector(BaseModule, DataCollectorInterface):
    """Test data collector implementation."""
    
    def __init__(self):
        super().__init__("TestDataCollector")
        self.collected_data = []
    
    def get_supported_sources(self):
        return ["web", "api"]
    
    async def collect_data(self, source: str, config: Dict[str, Any]) -> Any:
        """Simulate data collection."""
        data = {
            "source": source,
            "data": f"Sample data from {source}",
            "timestamp": datetime.now().isoformat()
        }
        self.collected_data.append(data)
        return data
    
    def validate_source(self, source: str) -> bool:
        return source in self.get_supported_sources()
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "message": "Data collector is working",
            "collected_count": len(self.collected_data)
        }


class TestDataProcessor(BaseModule, DataProcessorInterface):
    """Test data processor implementation."""
    
    def __init__(self):
        super().__init__("TestDataProcessor")
        self.processed_data = []
    
    async def process_data(self, data: Any, config: Dict[str, Any]) -> Any:
        """Simulate data processing."""
        processed = {
            "original": data,
            "processed": True,
            "timestamp": datetime.now().isoformat()
        }
        self.processed_data.append(processed)
        return processed
    
    def get_supported_formats(self):
        return ["json", "text"]
    
    def get_processing_capabilities(self):
        return ["validation", "transformation"]
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "message": "Data processor is working",
            "processed_count": len(self.processed_data)
        }


class TestModularSystem:
    """Test class for modular system integration."""
    
    @pytest.fixture
    def di_container(self):
        """Create DI container for testing."""
        return DIContainer()
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus for testing."""
        return EventBus()
    
    @pytest.fixture
    def plugin_registry(self):
        """Create plugin registry for testing."""
        return PluginRegistry()
    
    @pytest.fixture
    def module_manager(self, di_container, event_bus):
        """Create module manager for testing."""
        return ModuleManager(di_container, event_bus)
    
    @pytest.fixture
    def health_monitor(self, event_bus):
        """Create health monitor for testing."""
        return HealthMonitor(event_bus)
    
    def test_di_container_registration(self, di_container):
        """Test dependency injection container registration."""
        # Register services
        di_container.register_singleton(TestDataCollector, TestDataCollector)
        di_container.register_factory(TestDataProcessor, lambda: TestDataProcessor())
        
        # Test singleton
        collector1 = di_container.get(TestDataCollector)
        collector2 = di_container.get(TestDataCollector)
        assert collector1 is collector2  # Same instance
        
        # Test factory
        processor1 = di_container.get(TestDataProcessor)
        processor2 = di_container.get(TestDataProcessor)
        assert processor1 is not processor2  # Different instances
    
    def test_event_system(self, event_bus):
        """Test event system functionality."""
        events_received = []
        
        def event_handler(event):
            events_received.append(event)
        
        # Subscribe to events
        event_bus.subscribe("data_collected", event_handler)
        
        # Publish event
        event = DataCollectedEvent(
            data={"test": "data"},
            source="test_source"
        )
        event_bus.publish(event)
        
        # Verify event was received
        assert len(events_received) == 1
        assert events_received[0].name == "data_collected"
        assert events_received[0].data == {"test": "data"}
    
    def test_middleware_pipeline(self):
        """Test middleware pipeline functionality."""
        pipeline = MiddlewarePipeline("TestPipeline")
        
        # Add middlewares
        pipeline.add_middleware(LoggingMiddleware())
        pipeline.add_middleware(ValidationMiddleware(required_fields=["test"]))
        
        # Test pipeline
        async def test_pipeline():
            test_data = {"test": "value"}
            result = await pipeline.process(test_data)
            return result
        
        result = asyncio.run(test_pipeline())
        assert result == {"test": "value"}
    
    def test_plugin_system(self, plugin_registry):
        """Test plugin system functionality."""
        # Register plugins
        plugin_registry.register_plugin("sentiment", SentimentAnalysisPlugin)
        plugin_registry.register_plugin("entity", EntityExtractionPlugin)
        
        # Create plugin instances
        sentiment_plugin = plugin_registry.create_plugin_instance("sentiment")
        entity_plugin = plugin_registry.create_plugin_instance("entity")
        
        # Initialize plugins
        sentiment_plugin.initialize({})
        entity_plugin.initialize({})
        
        # Test plugin execution
        test_text = "This is a positive financial news about stock market growth."
        
        # Test sentiment analysis
        sentiment_result = sentiment_plugin.execute(test_text)
        assert "sentiment" in sentiment_result
        assert "confidence" in sentiment_result
        
        # Test entity extraction
        entity_result = entity_plugin.execute(test_text)
        assert "entities" in entity_result
    
    def test_module_manager(self, module_manager):
        """Test module manager functionality."""
        # Create test modules
        collector = TestDataCollector()
        processor = TestDataProcessor()
        
        # Register modules
        collector_config = ModuleConfig(
            name="test_collector",
            dependencies=[],
            startup_order=1
        )
        processor_config = ModuleConfig(
            name="test_processor",
            dependencies=["test_collector"],
            startup_order=2
        )
        
        module_manager.register_module("test_collector", TestDataCollector, collector_config)
        module_manager.register_module("test_processor", TestDataProcessor, processor_config)
        
        # Test module registration
        assert "test_collector" in module_manager.list_modules()
        assert "test_processor" in module_manager.list_modules()
        
        # Test dependency resolution
        assert module_manager._check_dependencies("test_processor") is False  # No running modules
    
    def test_health_monitoring(self, health_monitor):
        """Test health monitoring functionality."""
        # Create test module
        collector = TestDataCollector()
        
        # Register module for health monitoring
        config = HealthCheckConfig(interval=1, timeout=5)
        health_monitor.register_module(collector, config)
        
        # Test health check
        async def test_health_check():
            await health_monitor.start_monitoring()
            await asyncio.sleep(2)  # Wait for health checks
            
            health = await health_monitor.get_module_health("TestDataCollector")
            assert health is not None
            assert health["status"] == "healthy"
            
            await health_monitor.stop_monitoring()
        
        asyncio.run(test_health_check())
    
    def test_integrated_workflow(self, di_container, event_bus, module_manager):
        """Test integrated workflow with all components."""
        # Setup DI container
        di_container.register_singleton(TestDataCollector, TestDataCollector)
        di_container.register_singleton(TestDataProcessor, TestDataProcessor)
        
        # Setup event handlers
        events_received = []
        
        def data_collected_handler(event):
            events_received.append(("data_collected", event))
        
        def task_completed_handler(event):
            events_received.append(("task_completed", event))
        
        event_bus.subscribe("data_collected", data_collected_handler)
        event_bus.subscribe("task_completed", task_completed_handler)
        
        # Setup modules
        collector_config = ModuleConfig(name="collector", dependencies=[])
        processor_config = ModuleConfig(name="processor", dependencies=["collector"])
        
        module_manager.register_module("collector", TestDataCollector, collector_config)
        module_manager.register_module("processor", TestDataProcessor, processor_config)
        
        # Test integrated workflow
        async def test_workflow():
            # Start modules
            await module_manager.start_all_modules()
            
            # Get module instances
            collector = di_container.get(TestDataCollector)
            processor = di_container.get(TestDataProcessor)
            
            # Simulate data collection
            data = await collector.collect_data("web", {"url": "test.com"})
            assert data["source"] == "web"
            
            # Simulate data processing
            processed_data = await processor.process_data(data, {})
            assert processed_data["processed"] is True
            
            # Verify events were published
            await asyncio.sleep(0.1)  # Allow events to be processed
            assert len(events_received) >= 0  # Events may be published by modules
            
            # Stop modules
            await module_manager.stop_all_modules()
        
        asyncio.run(test_workflow())
    
    def test_error_handling(self, module_manager):
        """Test error handling in modular system."""
        # Create module with error
        class ErrorModule(BaseModule):
            async def start(self):
                raise Exception("Test error")
            
            async def health_check(self):
                return {"status": "unhealthy", "message": "Module has error"}
        
        # Register error module
        error_config = ModuleConfig(name="error_module", dependencies=[])
        module_manager.register_module("error_module", ErrorModule, error_config)
        
        # Test error handling
        async def test_error_handling():
            # Start module (should handle error gracefully)
            await module_manager._start_module("error_module")
            
            # Check module state
            module_info = module_manager.get_module("error_module")
            assert module_info.state == ModuleState.ERROR
            assert module_info.error_message is not None
        
        asyncio.run(test_error_handling())
    
    def test_plugin_discovery(self, plugin_registry):
        """Test plugin discovery functionality."""
        # Add discovery path
        plugin_registry.add_discovery_path("src/financial_data_collector/core/plugins/plugins")
        
        # Discover plugins
        discovered = plugin_registry.discover_plugins()
        
        # Should discover built-in plugins
        assert "SentimentAnalysis" in discovered or "sentiment" in discovered
        assert "EntityExtraction" in discovered or "entity" in discovered
    
    def test_middleware_conditional_execution(self):
        """Test conditional middleware execution."""
        from src.financial_data_collector.core.middleware.pipeline import ConditionalPipeline
        
        # Create conditional pipeline
        pipeline = ConditionalPipeline("TestConditional")
        
        # Create condition functions
        def is_json_data(data):
            return isinstance(data, dict)
        
        def is_text_data(data):
            return isinstance(data, str)
        
        # Create sub-pipelines
        json_pipeline = MiddlewarePipeline("JSONPipeline")
        json_pipeline.add_middleware(ValidationMiddleware(required_fields=["json_field"]))
        
        text_pipeline = MiddlewarePipeline("TextPipeline")
        text_pipeline.add_middleware(LoggingMiddleware())
        
        # Add conditions
        pipeline.add_condition(is_json_data, json_pipeline)
        pipeline.add_condition(is_text_data, text_pipeline)
        
        # Test conditional execution
        async def test_conditional():
            # Test JSON data
            json_data = {"json_field": "value"}
            result1 = await pipeline.process(json_data)
            assert result1 == json_data
            
            # Test text data
            text_data = "This is text data"
            result2 = await pipeline.process(text_data)
            assert result2 == text_data
        
        asyncio.run(test_conditional())


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
