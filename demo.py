#!/usr/bin/env python3
"""
Demo script for the Financial Data Collector modular system.

This script demonstrates the key features of the modular architecture including:
- Dependency injection
- Event system
- Middleware pipeline
- Plugin system
- Module management
- Health monitoring
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from financial_data_collector.core.di import DIContainer
from financial_data_collector.core.events import EventBus, DataCollectedEvent
from financial_data_collector.core.middleware import (
    MiddlewarePipeline, LoggingMiddleware, ValidationMiddleware
)
from financial_data_collector.core.plugins import (
    PluginRegistry, SentimentAnalysisPlugin, EntityExtractionPlugin
)
from financial_data_collector.core.module_manager import (
    ModuleManager, ModuleConfig, ModuleState
)
from financial_data_collector.core.health_checker import (
    HealthMonitor, HealthCheckConfig, BasicHealthChecker
)
from financial_data_collector.core.interfaces import (
    BaseModule, DataCollectorInterface, DataProcessorInterface
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoDataCollector(BaseModule, DataCollectorInterface):
    """Demo data collector implementation."""
    
    def __init__(self):
        super().__init__("DemoDataCollector")
        self.collected_data = []
    
    def get_supported_sources(self):
        return ["web", "api", "file"]
    
    async def collect_data(self, source: str, config: dict) -> dict:
        """Simulate data collection."""
        data = {
            "source": source,
            "data": f"Sample financial data from {source}",
            "timestamp": "2024-01-01T00:00:00Z",
            "symbol": "AAPL",
            "price": 150.25,
            "volume": 1000000
        }
        self.collected_data.append(data)
        logger.info(f"Collected data from {source}")
        return data
    
    def validate_source(self, source: str) -> bool:
        return source in self.get_supported_sources()
    
    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "message": "Data collector is working",
            "collected_count": len(self.collected_data)
        }


class DemoDataProcessor(BaseModule, DataProcessorInterface):
    """Demo data processor implementation."""
    
    def __init__(self):
        super().__init__("DemoDataProcessor")
        self.processed_data = []
    
    async def process_data(self, data: dict, config: dict) -> dict:
        """Simulate data processing."""
        processed = {
            "original": data,
            "processed": True,
            "enhanced_price": data.get("price", 0) * 1.1,  # Simulate price enhancement
            "timestamp": "2024-01-01T00:00:01Z"
        }
        self.processed_data.append(processed)
        logger.info(f"Processed data: {data.get('symbol', 'unknown')}")
        return processed
    
    def get_supported_formats(self):
        return ["json", "dict"]
    
    def get_processing_capabilities(self):
        return ["enhancement", "validation", "transformation"]
    
    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "message": "Data processor is working",
            "processed_count": len(self.processed_data)
        }


async def demo_dependency_injection():
    """Demonstrate dependency injection system."""
    print("\n=== Dependency Injection Demo ===")
    
    container = DIContainer()
    
    # Register services
    container.register_singleton(DemoDataCollector, DemoDataCollector)
    container.register_factory(DemoDataProcessor, lambda: DemoDataProcessor())
    
    # Get instances
    collector1 = container.get(DemoDataCollector)
    collector2 = container.get(DemoDataCollector)
    processor1 = container.get(DemoDataProcessor)
    processor2 = container.get(DemoDataProcessor)
    
    print(f"Collector instances are same: {collector1 is collector2}")
    print(f"Processor instances are different: {processor1 is not processor2}")
    
    # Test functionality
    data = await collector1.collect_data("web", {})
    processed = await processor1.process_data(data, {})
    print(f"Collected: {data['symbol']} at ${data['price']}")
    print(f"Processed: Enhanced price ${processed['enhanced_price']:.2f}")


async def demo_event_system():
    """Demonstrate event system."""
    print("\n=== Event System Demo ===")
    
    event_bus = EventBus()
    events_received = []
    
    def data_collected_handler(event):
        events_received.append(("data_collected", event.data))
        print(f"Event received: Data collected from {event.data.get('source', 'unknown')}")
    
    def task_completed_handler(event):
        events_received.append(("task_completed", event.data))
        print(f"Event received: Task completed for {event.data.get('symbol', 'unknown')}")
    
    # Subscribe to events
    event_bus.subscribe("data_collected", data_collected_handler)
    event_bus.subscribe("task_completed", task_completed_handler)
    
    # Publish events
    event1 = DataCollectedEvent(
        data={"source": "web", "symbol": "AAPL", "price": 150.25},
        source="demo_collector"
    )
    event_bus.publish(event1)
    
    # Simulate task completion
    from financial_data_collector.core.events import TaskCompletedEvent
    event2 = TaskCompletedEvent(
        task_id="task_001",
        result={"status": "success", "symbol": "AAPL"},
        source="demo_processor"
    )
    event_bus.publish(event2)
    
    print(f"Total events received: {len(events_received)}")


async def demo_middleware_pipeline():
    """Demonstrate middleware pipeline."""
    print("\n=== Middleware Pipeline Demo ===")
    
    # Create pipeline
    pipeline = MiddlewarePipeline("DemoPipeline")
    
    # Add middlewares
    pipeline.add_middleware(LoggingMiddleware(log_level=logging.INFO))
    pipeline.add_middleware(ValidationMiddleware(required_fields=["symbol", "price"]))
    
    # Test data
    test_data = {
        "symbol": "AAPL",
        "price": 150.25,
        "volume": 1000000,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    print(f"Original data: {test_data}")
    
    # Process through pipeline
    result = await pipeline.process(test_data)
    
    print(f"Processed data: {result}")
    print(f"Pipeline length: {len(pipeline)} middlewares")


async def demo_plugin_system():
    """Demonstrate plugin system."""
    print("\n=== Plugin System Demo ===")
    
    registry = PluginRegistry()
    
    # Register plugins
    registry.register_plugin("sentiment", SentimentAnalysisPlugin)
    registry.register_plugin("entity", EntityExtractionPlugin)
    
    # Create plugin instances
    sentiment_plugin = registry.create_plugin_instance("sentiment")
    entity_plugin = registry.create_plugin_instance("entity")
    
    # Initialize plugins
    sentiment_plugin.initialize({"sensitivity_threshold": 0.1})
    entity_plugin.initialize({"extract_confidence": True, "min_confidence": 0.5})
    
    # Test text
    test_text = "Apple Inc. reported strong quarterly earnings with 15% revenue growth. The stock price surged to $150.25, up 5% from yesterday."
    
    print(f"Test text: {test_text}")
    
    # Test sentiment analysis
    sentiment_result = sentiment_plugin.execute(test_text)
    print(f"Sentiment: {sentiment_result['sentiment']} (confidence: {sentiment_result['confidence']:.2f})")
    
    # Test entity extraction
    entity_result = entity_plugin.execute(test_text)
    print(f"Entities found: {len(entity_result['entities'])} types")
    for entity_type, entities in entity_result['entities'].items():
        if entities:
            print(f"  {entity_type}: {entities}")


async def demo_module_management():
    """Demonstrate module management."""
    print("\n=== Module Management Demo ===")
    
    # Setup
    container = DIContainer()
    event_bus = EventBus()
    module_manager = ModuleManager(container, event_bus)
    
    # Register modules
    collector_config = ModuleConfig(
        name="demo_collector",
        dependencies=[],
        startup_order=1
    )
    processor_config = ModuleConfig(
        name="demo_processor", 
        dependencies=["demo_collector"],
        startup_order=2
    )
    
    module_manager.register_module("demo_collector", DemoDataCollector, collector_config)
    module_manager.register_module("demo_processor", DemoDataProcessor, processor_config)
    
    print(f"Registered modules: {module_manager.list_modules()}")
    
    # Start modules
    await module_manager.start_all_modules()
    
    # Check module status
    status = module_manager.get_module_status()
    for module_name, module_status in status.items():
        print(f"Module {module_name}: {module_status['state']}")
    
    # Stop modules
    await module_manager.stop_all_modules()
    print("All modules stopped")


async def demo_health_monitoring():
    """Demonstrate health monitoring."""
    print("\n=== Health Monitoring Demo ===")
    
    # Setup
    event_bus = EventBus()
    health_monitor = HealthMonitor(event_bus)
    
    # Create test modules
    collector = DemoDataCollector()
    processor = DemoDataProcessor()
    
    # Register modules for health monitoring
    config = HealthCheckConfig(interval=1, timeout=5)
    health_monitor.register_module(collector, config)
    health_monitor.register_module(processor, config)
    
    # Start health monitoring
    await health_monitor.start_monitoring()
    
    # Wait for health checks
    await asyncio.sleep(2)
    
    # Get health status
    collector_health = await health_monitor.get_module_health("DemoDataCollector")
    processor_health = await health_monitor.get_module_health("DemoDataProcessor")
    system_health = await health_monitor.get_system_health()
    
    print(f"Collector health: {collector_health['status']}")
    print(f"Processor health: {processor_health['status']}")
    print(f"System health: {system_health['status']}")
    
    # Stop health monitoring
    await health_monitor.stop_monitoring()
    print("Health monitoring stopped")


async def demo_integrated_workflow():
    """Demonstrate integrated workflow."""
    print("\n=== Integrated Workflow Demo ===")
    
    # Setup all components
    container = DIContainer()
    event_bus = EventBus()
    module_manager = ModuleManager(container, event_bus)
    health_monitor = HealthMonitor(event_bus)
    plugin_registry = PluginRegistry()
    
    # Register services
    container.register_singleton(DemoDataCollector, DemoDataCollector)
    container.register_singleton(DemoDataProcessor, DemoDataProcessor)
    
    # Setup event handlers
    workflow_events = []
    
    def workflow_handler(event):
        workflow_events.append(event.name)
        print(f"Workflow event: {event.name}")
    
    event_bus.subscribe("data_collected", workflow_handler)
    event_bus.subscribe("task_completed", workflow_handler)
    
    # Register modules
    collector_config = ModuleConfig(name="workflow_collector", dependencies=[])
    processor_config = ModuleConfig(name="workflow_processor", dependencies=["workflow_collector"])
    
    module_manager.register_module("workflow_collector", DemoDataCollector, collector_config)
    module_manager.register_module("workflow_processor", DemoDataProcessor, processor_config)
    
    # Register plugins
    plugin_registry.register_plugin("sentiment", SentimentAnalysisPlugin)
    sentiment_plugin = plugin_registry.create_plugin_instance("sentiment")
    sentiment_plugin.initialize({})
    
    # Start system
    await module_manager.start_all_modules()
    await health_monitor.start_monitoring()
    
    # Simulate workflow
    collector = container.get(DemoDataCollector)
    processor = container.get(DemoDataProcessor)
    
    # Collect data
    data = await collector.collect_data("api", {"symbol": "AAPL"})
    print(f"Collected: {data['symbol']} at ${data['price']}")
    
    # Process data
    processed = await processor.process_data(data, {})
    print(f"Processed: Enhanced price ${processed['enhanced_price']:.2f}")
    
    # Analyze sentiment
    news_text = f"Positive news about {data['symbol']} with strong performance"
    sentiment = sentiment_plugin.execute(news_text)
    print(f"Sentiment analysis: {sentiment['sentiment']} (confidence: {sentiment['confidence']:.2f})")
    
    # Check system health
    system_health = await health_monitor.get_system_health()
    print(f"System health: {system_health['status']}")
    
    # Stop system
    await health_monitor.stop_monitoring()
    await module_manager.stop_all_modules()
    
    print(f"Workflow completed with {len(workflow_events)} events")


async def main():
    """Run all demos."""
    print("Financial Data Collector - Modular System Demo")
    print("=" * 50)
    
    try:
        await demo_dependency_injection()
        await demo_event_system()
        await demo_middleware_pipeline()
        await demo_plugin_system()
        await demo_module_management()
        await demo_health_monitoring()
        await demo_integrated_workflow()
        
        print("\n" + "=" * 50)
        print("All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
