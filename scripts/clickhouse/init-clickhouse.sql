-- ClickHouse initialization script for Financial Data Collector
-- This script creates the necessary database, tables, and views

-- Create database
CREATE DATABASE IF NOT EXISTS financial_data;

-- Use the database
USE financial_data;

-- Create financial_data table for storing market data
CREATE TABLE IF NOT EXISTS financial_data (
    symbol String,
    data_type String,
    price Nullable(Float64),
    open_price Nullable(Float64),
    high_price Nullable(Float64),
    low_price Nullable(Float64),
    close_price Nullable(Float64),
    volume Nullable(UInt64),
    market_cap Nullable(Float64),
    change Nullable(Float64),
    change_percent Nullable(Float64),
    timestamp DateTime,
    source String,
    metadata String,
    task_id Nullable(String)
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp)
PARTITION BY toYYYYMM(timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- Create latest_prices table for fast price lookups
CREATE TABLE IF NOT EXISTS latest_prices (
    symbol String,
    price Nullable(Float64),
    change Nullable(Float64),
    change_percent Nullable(Float64),
    volume Nullable(UInt64),
    timestamp DateTime,
    data_type String DEFAULT 'stock'
) ENGINE = ReplacingMergeTree(timestamp)
ORDER BY symbol
SETTINGS index_granularity = 8192;

-- Create news_data table for storing financial news
CREATE TABLE IF NOT EXISTS news_data (
    title String,
    content Nullable(String),
    url String,
    symbols Array(String),
    sentiment Nullable(String),
    category Nullable(String),
    published_at Nullable(DateTime),
    source String,
    author Nullable(String),
    language String DEFAULT 'en',
    timestamp DateTime,
    metadata String,
    task_id Nullable(String)
) ENGINE = MergeTree()
ORDER BY (source, timestamp)
PARTITION BY toYYYYMM(timestamp)
TTL timestamp + INTERVAL 6 MONTH
SETTINGS index_granularity = 8192;

-- Create crawl_tasks table for storing task information
CREATE TABLE IF NOT EXISTS crawl_tasks (
    task_id String,
    url String,
    status String,
    crawler_type String,
    priority UInt8,
    config String,
    created_at DateTime,
    started_at Nullable(DateTime),
    completed_at Nullable(DateTime),
    result Nullable(String),
    error Nullable(String),
    retry_count UInt8 DEFAULT 0,
    max_retries UInt8 DEFAULT 3,
    metadata String
) ENGINE = MergeTree()
ORDER BY (created_at, task_id)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 1 MONTH
SETTINGS index_granularity = 8192;

-- Temporarily disabled materialized view for debugging
-- CREATE MATERIALIZED VIEW IF NOT EXISTS latest_prices_mv
-- TO latest_prices AS
-- SELECT 
--     symbol,
--     price,
--     change,
--     change_percent,
--     volume,
--     timestamp,
--     data_type
-- FROM financial_data
-- ORDER BY symbol, timestamp DESC;

-- Absolute minimal initialization script
CREATE DATABASE IF NOT EXISTS financial_data;

CREATE TABLE IF NOT EXISTS financial_data.simple_test (
    id UInt64,
    value String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY id;

SELECT 'Minimal initialization completed successfully' as status;

