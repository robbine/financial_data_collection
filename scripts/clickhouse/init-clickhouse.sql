-- Create database if not exists
CREATE DATABASE IF NOT EXISTS financial_data;

-- Switch to the target database
USE financial_data;

-- ============================================================
-- 1️⃣ 分钟级 K 线表（源数据）
-- ============================================================
CREATE TABLE IF NOT EXISTS tv_klines_minute (
    symbol String COMMENT '股票代码',
    timestamp DateTime COMMENT 'K线时间戳',
    open Float64 COMMENT '开盘价',
    high Float64 COMMENT '最高价',
    low Float64 COMMENT '最低价',
    close Float64 COMMENT '收盘价',
    volume Float64 COMMENT '成交量',
    turnover Float64 COMMENT '成交额',
    update_time DateTime DEFAULT now() COMMENT '数据更新时间',
    create_time DateTime DEFAULT now() COMMENT '数据创建时间'
)
ENGINE = ReplacingMergeTree(update_time)
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol, timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS storage_policy = 'default', index_granularity = 8192;

-- ============================================================
-- 2️⃣ 股票元数据表
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_symbols (
    symbol String COMMENT '股票代码',
    name String COMMENT '股票名称',
    exchange String COMMENT '交易所',
    is_active Bool DEFAULT 1 COMMENT '是否活跃',
    update_time DateTime DEFAULT now() COMMENT '更新时间'
)
ENGINE = ReplacingMergeTree(update_time)
ORDER BY symbol
SETTINGS index_granularity = 1024;

-- ============================================================
-- 3️⃣ 日级聚合视图（物化视图）
-- ============================================================
-- 从分钟线自动汇总为日线
CREATE MATERIALIZED VIEW IF NOT EXISTS tv_klines_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMMDD(day_timestamp)
ORDER BY (symbol, day_timestamp)
AS
SELECT
    symbol,
    toStartOfDay(timestamp) AS day_timestamp,
    anyLast(open) AS open,
    max(high) AS high,
    min(low) AS low,
    anyLast(close) AS close,
    sum(volume) AS volume,
    sum(turnover) AS turnover,
    max(update_time) AS update_time
FROM tv_klines_minute
GROUP BY
    symbol,
    toStartOfDay(timestamp);




-- ============================================================
-- ✅ 使用说明
-- 读取日线聚合结果时，请用 finalizeAggregation() 函数，例如：
-- SELECT
--     symbol,
--     toDate(timestamp) AS trading_day,
--     finalizeAggregation(open) AS open,
--     finalizeAggregation(high) AS high,
--     finalizeAggregation(low) AS low,
--     finalizeAggregation(close) AS close,
--     finalizeAggregation(volume) AS volume,
--     finalizeAggregation(turnover) AS turnover,
--     finalizeAggregation(update_time) AS update_time
-- FROM tv_klines_daily
-- ORDER BY symbol, trading_day;
-- ============================================================
