// Initialize MongoDB for Financial Data Collector
// This script sets up the initial MongoDB collections and indexes

// Switch to the application database
db = db.getSiblingDB('fdc_docs');

// Create collections with validation
db.createCollection('raw_data', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["source", "symbol", "data_type", "raw_data", "collected_at"],
      properties: {
        source: { bsonType: "string" },
        symbol: { bsonType: "string" },
        data_type: { bsonType: "string" },
        raw_data: { bsonType: "object" },
        metadata: { bsonType: "object" },
        collected_at: { bsonType: "date" },
        processed_at: { bsonType: "date" }
      }
    }
  }
});

db.createCollection('processed_data', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["raw_data_id", "symbol", "data_type", "processed_data", "processed_at"],
      properties: {
        raw_data_id: { bsonType: "objectId" },
        symbol: { bsonType: "string" },
        data_type: { bsonType: "string" },
        processed_data: { bsonType: "object" },
        processing_metadata: { bsonType: "object" },
        processed_at: { bsonType: "date" }
      }
    }
  }
});

db.createCollection('events', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "source", "timestamp"],
      properties: {
        name: { bsonType: "string" },
        source: { bsonType: "string" },
        data: { bsonType: "object" },
        metadata: { bsonType: "object" },
        timestamp: { bsonType: "date" }
      }
    }
  }
});

db.createCollection('tasks', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "status", "created_at"],
      properties: {
        name: { bsonType: "string" },
        module_id: { bsonType: "objectId" },
        status: { bsonType: "string", enum: ["pending", "running", "completed", "failed", "cancelled"] },
        config: { bsonType: "object" },
        result: { bsonType: "object" },
        error_message: { bsonType: "string" },
        started_at: { bsonType: "date" },
        completed_at: { bsonType: "date" },
        created_at: { bsonType: "date" }
      }
    }
  }
});

db.createCollection('health_checks', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["module_name", "status", "timestamp"],
      properties: {
        module_name: { bsonType: "string" },
        status: { bsonType: "string", enum: ["healthy", "degraded", "unhealthy", "unknown"] },
        message: { bsonType: "string" },
        details: { bsonType: "object" },
        response_time: { bsonType: "double" },
        timestamp: { bsonType: "date" }
      }
    }
  }
});

db.createCollection('metrics', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["module_name", "metric_name", "timestamp"],
      properties: {
        module_name: { bsonType: "string" },
        metric_name: { bsonType: "string" },
        metric_value: { bsonType: "double" },
        metric_data: { bsonType: "object" },
        timestamp: { bsonType: "date" }
      }
    }
  }
});

// Create indexes for performance
db.raw_data.createIndex({ "source": 1 });
db.raw_data.createIndex({ "symbol": 1 });
db.raw_data.createIndex({ "data_type": 1 });
db.raw_data.createIndex({ "collected_at": -1 });
db.raw_data.createIndex({ "source": 1, "symbol": 1, "collected_at": -1 });

db.processed_data.createIndex({ "symbol": 1 });
db.processed_data.createIndex({ "data_type": 1 });
db.processed_data.createIndex({ "processed_at": -1 });
db.processed_data.createIndex({ "raw_data_id": 1 });

db.events.createIndex({ "name": 1 });
db.events.createIndex({ "source": 1 });
db.events.createIndex({ "timestamp": -1 });
db.events.createIndex({ "name": 1, "timestamp": -1 });

db.tasks.createIndex({ "status": 1 });
db.tasks.createIndex({ "module_id": 1 });
db.tasks.createIndex({ "created_at": -1 });
db.tasks.createIndex({ "name": 1, "status": 1 });

db.health_checks.createIndex({ "module_name": 1 });
db.health_checks.createIndex({ "status": 1 });
db.health_checks.createIndex({ "timestamp": -1 });
db.health_checks.createIndex({ "module_name": 1, "timestamp": -1 });

db.metrics.createIndex({ "module_name": 1 });
db.metrics.createIndex({ "metric_name": 1 });
db.metrics.createIndex({ "timestamp": -1 });
db.metrics.createIndex({ "module_name": 1, "metric_name": 1, "timestamp": -1 });

// Create TTL indexes for automatic cleanup
db.raw_data.createIndex({ "collected_at": 1 }, { expireAfterSeconds: 7776000 }); // 90 days
db.processed_data.createIndex({ "processed_at": 1 }, { expireAfterSeconds: 15552000 }); // 180 days
db.events.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 2592000 }); // 30 days
db.health_checks.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 2592000 }); // 30 days
db.metrics.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 }); // 90 days

// Insert initial data
db.raw_data.insertMany([
  {
    source: "yahoo_finance",
    symbol: "AAPL",
    data_type: "quote",
    raw_data: {
      price: 150.25,
      volume: 1000000,
      market_cap: 2500000000000
    },
    metadata: {
      api_version: "v1",
      request_id: "req_001"
    },
    collected_at: new Date()
  },
  {
    source: "alpha_vantage",
    symbol: "MSFT",
    data_type: "quote",
    raw_data: {
      price: 300.50,
      volume: 500000,
      market_cap: 2200000000000
    },
    metadata: {
      api_version: "v1",
      request_id: "req_002"
    },
    collected_at: new Date()
  }
]);

db.events.insertMany([
  {
    name: "data_collected",
    source: "yahoo_finance",
    data: { symbol: "AAPL", price: 150.25 },
    metadata: { collection_time: 0.5 },
    timestamp: new Date()
  },
  {
    name: "task_completed",
    source: "data_processor",
    data: { task_id: "task_001", status: "success" },
    metadata: { processing_time: 2.1 },
    timestamp: new Date()
  }
]);

db.health_checks.insertMany([
  {
    module_name: "web_crawler",
    status: "healthy",
    message: "Web crawler is working normally",
    details: { last_crawl: new Date(), pages_crawled: 100 },
    response_time: 0.1,
    timestamp: new Date()
  },
  {
    module_name: "data_processor",
    status: "healthy",
    message: "Data processor is working normally",
    details: { processed_count: 1000, error_count: 0 },
    response_time: 0.05,
    timestamp: new Date()
  }
]);

db.metrics.insertMany([
  {
    module_name: "web_crawler",
    metric_name: "pages_crawled",
    metric_value: 100,
    metric_data: { period: "1h" },
    timestamp: new Date()
  },
  {
    module_name: "data_processor",
    metric_name: "processing_time",
    metric_value: 2.1,
    metric_data: { average: true },
    timestamp: new Date()
  }
]);

print("MongoDB initialization completed successfully!");
print("Collections created: raw_data, processed_data, events, tasks, health_checks, metrics");
print("Indexes created for optimal performance");
print("Initial data inserted");
