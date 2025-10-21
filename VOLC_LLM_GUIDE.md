# 火山引擎LLM集成指南

本文档详细说明如何在Financial Data Collector系统中使用火山引擎API进行LLM驱动的数据提取。

## 🚀 火山引擎API配置

### 1. **获取API凭证**

首先，您需要从火山引擎控制台获取API凭证：

```bash
# 在您的.env文件中配置
VOLC_API_KEY=your_volc_api_key_here
VOLC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

### 2. **支持的模型**

火山引擎支持多种模型，推荐用于金融数据提取：

- **ep-20250725215501-7zrfm**: 您的自定义模型端点，专为金融数据提取优化
- **doubao-pro-4k**: 高性能模型，适合复杂金融数据提取
- **doubao-pro-32k**: 长文本处理，适合大量金融报告
- **doubao-lite**: 轻量级模型，适合简单数据提取

## 🔧 配置方法

### 方法1: 直接配置

```python
from financial_data_collector.core.crawler.volc_llm_config import VolcLLMConfig

# 创建火山引擎配置
volc_config = VolcLLMConfig(
    api_key="your_volc_api_key",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    model="ep-20250725215501-7zrfm"
)

# 获取LLM配置
llm_config = volc_config.get_llm_config()

# 获取提取策略
extraction_strategy = volc_config.get_extraction_strategy(
    instruction="Extract financial data from the webpage",
    schema={"type": "object", "properties": {"financial_data": {"type": "object"}}}
)
```

### 方法2: 环境变量配置

```python
from financial_data_collector.core.crawler.volc_llm_config import get_volc_llm_config_from_env

# 从环境变量获取配置
volc_config = get_volc_llm_config_from_env()

if volc_config:
    llm_config = volc_config.get_llm_config()
    extraction_strategy = volc_config.get_extraction_strategy()
```

### 方法3: 配置文件配置

```yaml
# config/volc_llm.yaml
web_crawler:
  config:
    llm_config:
      provider: "volc"
      api_key: "${VOLC_API_KEY}"
      base_url: "${VOLC_BASE_URL}"
      model: "doubao-pro-4k"
      instruction: "Extract financial data from the webpage"
      schema:
        type: "object"
        properties:
          stock_data:
            type: "object"
            properties:
              symbol: {"type": "string"}
              price: {"type": "number"}
              volume: {"type": "number"}
```

## 💻 使用示例

### 基本使用

```python
from financial_data_collector.core.crawler.web_crawler import WebCrawler

# 创建爬虫
crawler = WebCrawler("VolcLLMCrawler")

# 配置火山引擎LLM
config = {
    "browser": {"headless": True},
    "extraction_strategy": "llm",
    "llm_config": {
        "provider": "volc",
        "api_key": "your_volc_api_key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-20250725215501-7zrfm",
        "instruction": "Extract financial data from the webpage",
        "schema": {
            "type": "object",
            "properties": {
                "stock_data": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "price": {"type": "number"},
                        "volume": {"type": "number"}
                    }
                }
            }
        }
    }
}

crawler.initialize(config)
await crawler.start()

# 爬取金融数据
result = await crawler.crawl_url(
    "https://finance.yahoo.com/quote/AAPL",
    {"extraction_strategy": "llm", "wait_for": 3}
)

print(f"提取的数据: {result.get('financial_data')}")
```

### 高级配置

```python
# 创建火山引擎LLM策略
from financial_data_collector.core.crawler.volc_llm_config import create_volc_llm_strategy

# 自定义提取策略
extraction_strategy = create_volc_llm_strategy(
    api_key="your_volc_api_key",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    model="doubao-pro-4k",
    instruction="""
    Extract financial data from the webpage. Focus on:
    1. Stock prices, volume, and market data
    2. Company information and financial metrics
    3. News articles and financial reports
    4. Market trends and analysis
    
    Return structured data with clear categorization.
    """,
    schema={
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
                        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]}
                    }
                }
            }
        }
    }
)
```

## 📊 金融数据提取示例

### 股票数据提取

```python
# 股票数据提取配置
stock_config = {
    "llm_config": {
        "provider": "volc",
        "api_key": "your_volc_api_key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-20250725215501-7zrfm",
        "instruction": "Extract stock price, volume, and market data",
        "schema": {
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
                        "market_cap": {"type": "number"},
                        "pe_ratio": {"type": "number"},
                        "dividend_yield": {"type": "number"}
                    }
                }
            }
        }
    }
}

# 爬取股票数据
result = await crawler.crawl_url(
    "https://finance.yahoo.com/quote/AAPL",
    stock_config
)
```

### 新闻数据提取

```python
# 新闻数据提取配置
news_config = {
    "llm_config": {
        "provider": "volc",
        "api_key": "your_volc_api_key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-20250725215501-7zrfm",
        "instruction": "Extract financial news headlines, summaries, and sentiment",
        "schema": {
            "type": "object",
            "properties": {
                "news": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "url": {"type": "string"},
                            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                            "relevance": {"type": "number", "minimum": 0, "maximum": 1}
                        }
                    }
                }
            }
        }
    }
}

# 爬取新闻数据
result = await crawler.crawl_url(
    "https://finance.yahoo.com/news/",
    news_config
)
```

### 公司信息提取

```python
# 公司信息提取配置
company_config = {
    "llm_config": {
        "provider": "volc",
        "api_key": "your_volc_api_key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-20250725215501-7zrfm",
        "instruction": "Extract company information and financial metrics",
        "schema": {
            "type": "object",
            "properties": {
                "company_info": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "sector": {"type": "string"},
                        "industry": {"type": "string"},
                        "description": {"type": "string"},
                        "employees": {"type": "number"},
                        "headquarters": {"type": "string"},
                        "founded": {"type": "string"},
                        "ceo": {"type": "string"}
                    }
                },
                "financial_metrics": {
                    "type": "object",
                    "properties": {
                        "market_cap": {"type": "number"},
                        "enterprise_value": {"type": "number"},
                        "revenue": {"type": "number"},
                        "profit": {"type": "number"},
                        "debt_to_equity": {"type": "number"},
                        "price_to_earnings": {"type": "number"}
                    }
                }
            }
        }
    }
}

# 爬取公司信息
result = await crawler.crawl_url(
    "https://finance.yahoo.com/quote/AAPL/profile",
    company_config
)
```

## 🔄 批量处理

```python
# 批量爬取多个股票
stocks = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
results = []

for symbol in stocks:
    result = await crawler.crawl_url(
        f"https://finance.yahoo.com/quote/{symbol}",
        stock_config
    )
    results.append({
        "symbol": symbol,
        "data": result.get("financial_data", {})
    })

print(f"批量处理完成，共处理 {len(results)} 个股票")
```

## 🚀 性能优化

### 1. **模型选择**

```python
# 根据任务复杂度选择模型
models = {
    "simple": "doubao-lite",      # 简单数据提取
    "complex": "doubao-pro-4k",   # 复杂金融数据
    "long_text": "doubao-pro-32k" # 长文本处理
}

# 选择合适模型
model = models["complex"] if complex_task else models["simple"]
```

### 2. **并发控制**

```python
# 控制并发请求
config = {
    "max_concurrent_requests": 3,  # 限制并发数
    "request_delay": 2.0,          # 请求间隔
    "timeout": 30                  # 超时时间
}
```

### 3. **缓存策略**

```python
# 启用缓存
config = {
    "cache_mode": "BYPASS",  # 绕过缓存获取最新数据
    "cache_ttl": 3600        # 缓存生存时间
}
```

## 🛠️ 故障排除

### 常见问题

#### 1. **API密钥错误**
```python
# 检查API密钥
if not volc_config.api_key:
    raise ValueError("Volcano Engine API key is required")
```

#### 2. **网络连接问题**
```python
# 检查网络连接
import requests
try:
    response = requests.get(volc_config.base_url, timeout=10)
    print("✅ 网络连接正常")
except Exception as e:
    print(f"❌ 网络连接失败: {e}")
```

#### 3. **模型不可用**
```python
# 检查模型可用性
available_models = ["doubao-pro-4k", "doubao-pro-32k", "doubao-lite"]
if model not in available_models:
    print(f"❌ 模型 {model} 不可用，请选择: {available_models}")
```

### 调试技巧

#### 1. **启用详细日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. **测试API连接**
```python
# 测试火山引擎API
async def test_volc_api():
    try:
        result = await crawler.crawl_url(
            "https://httpbin.org/get",
            {"extraction_strategy": "llm", "llm_config": volc_config}
        )
        print("✅ API连接正常")
        return True
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False
```

#### 3. **监控性能**
```python
# 监控提取性能
import time

start_time = time.time()
result = await crawler.crawl_url(url, config)
end_time = time.time()

print(f"提取耗时: {end_time - start_time:.2f}秒")
print(f"提取成功率: {result.get('success_rate', 0):.2%}")
```

## 📚 最佳实践

### 1. **指令设计**
```python
# 好的指令示例
good_instruction = """
Extract financial data from the webpage. Focus on:
1. Stock prices, volume, and market data
2. Company information and financial metrics
3. News articles and financial reports
4. Market trends and analysis

Return structured data with clear categorization.
"""

# 避免的指令示例
bad_instruction = "Extract data"  # 太简单
```

### 2. **Schema设计**
```python
# 好的Schema示例
good_schema = {
    "type": "object",
    "properties": {
        "stock_data": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "price": {"type": "number"},
                "volume": {"type": "number"}
            },
            "required": ["symbol", "price"]
        }
    }
}
```

### 3. **错误处理**
```python
# 完善的错误处理
try:
    result = await crawler.crawl_url(url, config)
    if result.get("success"):
        return result.get("financial_data", {})
    else:
        logger.warning(f"提取失败: {result.get('error')}")
        return {}
except Exception as e:
    logger.error(f"爬取异常: {e}")
    return {}
```

## 🎯 总结

通过以上配置和使用方法，您可以充分利用火山引擎API的强大能力进行金融数据提取。关键要点：

1. **正确配置API凭证**: 确保API密钥和base_url正确
2. **选择合适的模型**: 根据任务复杂度选择合适模型
3. **设计清晰的指令**: 提供明确的提取指令
4. **定义结构化Schema**: 确保输出数据格式一致
5. **实施错误处理**: 处理各种异常情况
6. **监控性能**: 跟踪提取成功率和性能指标

这样，您就可以在Financial Data Collector系统中高效地使用火山引擎API进行LLM驱动的金融数据提取了。
