-- Initialize Financial Data Collector Database
-- This script sets up the initial database schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS fdc_core;
CREATE SCHEMA IF NOT EXISTS fdc_data;
CREATE SCHEMA IF NOT EXISTS fdc_analytics;

-- Set search path
SET search_path TO fdc_core, fdc_data, fdc_analytics, public;

-- Core tables
CREATE TABLE IF NOT EXISTS fdc_core.modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fdc_core.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    module_id UUID REFERENCES fdc_core.modules(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    config JSONB,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fdc_core.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    data JSONB,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data tables
CREATE TABLE IF NOT EXISTS fdc_data.data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(100) NOT NULL,
    config JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    last_collected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fdc_data.raw_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES fdc_data.data_sources(id),
    symbol VARCHAR(50),
    data_type VARCHAR(100),
    raw_data JSONB,
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS fdc_data.processed_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_data_id UUID REFERENCES fdc_data.raw_data(id),
    symbol VARCHAR(50),
    data_type VARCHAR(100),
    processed_data JSONB,
    processing_metadata JSONB,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics tables
CREATE TABLE IF NOT EXISTS fdc_analytics.metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION,
    metric_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fdc_analytics.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    details JSONB,
    response_time DOUBLE PRECISION,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_raw_data_source_id ON fdc_data.raw_data(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_data_symbol ON fdc_data.raw_data(symbol);
CREATE INDEX IF NOT EXISTS idx_raw_data_collected_at ON fdc_data.raw_data(collected_at);
CREATE INDEX IF NOT EXISTS idx_raw_data_data_type ON fdc_data.raw_data(data_type);

CREATE INDEX IF NOT EXISTS idx_processed_data_symbol ON fdc_data.processed_data(symbol);
CREATE INDEX IF NOT EXISTS idx_processed_data_processed_at ON fdc_data.processed_data(processed_at);
CREATE INDEX IF NOT EXISTS idx_processed_data_data_type ON fdc_data.processed_data(data_type);

CREATE INDEX IF NOT EXISTS idx_events_name ON fdc_core.events(name);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON fdc_core.events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source ON fdc_core.events(source);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON fdc_core.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_module_id ON fdc_core.tasks(module_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON fdc_core.tasks(created_at);

CREATE INDEX IF NOT EXISTS idx_metrics_module_name ON fdc_analytics.metrics(module_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON fdc_analytics.metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_metric_name ON fdc_analytics.metrics(metric_name);

CREATE INDEX IF NOT EXISTS idx_health_checks_module_name ON fdc_analytics.health_checks(module_name);
CREATE INDEX IF NOT EXISTS idx_health_checks_timestamp ON fdc_analytics.health_checks(timestamp);
CREATE INDEX IF NOT EXISTS idx_health_checks_status ON fdc_analytics.health_checks(status);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_modules_updated_at BEFORE UPDATE ON fdc_core.modules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON fdc_data.data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data
INSERT INTO fdc_core.modules (name, version, status, config) VALUES
('config_manager', '1.0.0', 'active', '{"auto_reload": true}'),
('web_crawler', '1.0.0', 'active', '{"user_agent": "Financial Data Collector 1.0"}'),
('api_collector', '1.0.0', 'active', '{"rate_limit": 100}'),
('data_processor', '1.0.0', 'active', '{"batch_size": 1000}'),
('task_scheduler', '1.0.0', 'active', '{"max_concurrent_tasks": 10}')
ON CONFLICT (name) DO NOTHING;

INSERT INTO fdc_data.data_sources (name, type, config) VALUES
('yahoo_finance', 'api', '{"base_url": "https://query1.finance.yahoo.com", "rate_limit": 10}'),
('alpha_vantage', 'api', '{"base_url": "https://www.alphavantage.co/query", "rate_limit": 5}'),
('quandl', 'api', '{"base_url": "https://www.quandl.com/api/v3", "rate_limit": 10}'),
('sec_edgar', 'web', '{"base_url": "https://www.sec.gov/edgar", "rate_limit": 10}')
ON CONFLICT (name) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW fdc_analytics.system_status AS
SELECT 
    m.name as module_name,
    m.status,
    m.updated_at as last_updated,
    hc.status as health_status,
    hc.timestamp as last_health_check,
    hc.response_time
FROM fdc_core.modules m
LEFT JOIN LATERAL (
    SELECT status, timestamp, response_time
    FROM fdc_analytics.health_checks hc2
    WHERE hc2.module_name = m.name
    ORDER BY hc2.timestamp DESC
    LIMIT 1
) hc ON true;

CREATE OR REPLACE VIEW fdc_analytics.data_collection_stats AS
SELECT 
    ds.name as source_name,
    ds.type as source_type,
    ds.last_collected_at,
    COUNT(rd.id) as total_records,
    MAX(rd.collected_at) as latest_collection,
    MIN(rd.collected_at) as earliest_collection
FROM fdc_data.data_sources ds
LEFT JOIN fdc_data.raw_data rd ON ds.id = rd.source_id
GROUP BY ds.id, ds.name, ds.type, ds.last_collected_at;

-- Grant permissions
GRANT USAGE ON SCHEMA fdc_core, fdc_data, fdc_analytics TO fdc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA fdc_core, fdc_data, fdc_analytics TO fdc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA fdc_core, fdc_data, fdc_analytics TO fdc_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA fdc_core, fdc_data, fdc_analytics TO fdc_user;
