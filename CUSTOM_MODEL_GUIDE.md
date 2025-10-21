# 自定义模型使用指南

本文档详细说明如何使用您的自定义模型端点"ep-20250725215501-7zrfm"进行金融数据提取。

## 🎯 您的自定义模型

**模型端点**: `ep-20250725215501-7zrfm`
**特点**: 专为金融数据提取优化
**优势**: 针对金融领域的专业训练，提取准确度更高

## 🔧 配置方法

### 1. **环境变量配置**

在您的`.env`文件中添加：

```bash
# 火山引擎API配置
VOLC_API_KEY=your_volc_api_key_here
VOLC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLC_MODEL=ep-20250725215501-7zrfm
```

### 2. **直接配置**

```python
from financial_data_collector.core.crawler.volc_llm_config import VolcLLMConfig

# 使用您的自定义模型
volc_config = VolcLLMConfig(
    api_key="your_volc_api_key",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    model="ep-20250725215501-7zrfm"  # 您的自定义模型
)
```

### 3. **配置文件配置**

使用`config/custom_model.yaml`配置文件：

```yaml
web_crawler:
  config:
    llm_config:
      provider: "volc"
      api_key: "${VOLC_API_KEY}"
      base_url: "${VOLC_BASE_URL}"
      model: "ep-20250725215501-7zrfm"
```

## 💻 使用示例

### 基本使用

```python
from financial_data_collector.core.crawler.web_crawler import WebCrawler

# 创建爬虫
crawler = WebCrawler("CustomModelCrawler")

# 配置您的自定义模型
config = {
    "browser": {"headless": True},
    "extraction_strategy": "llm",
    "llm_config": {
        "provider": "volc",
        "api_key": "your_volc_api_key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-20250725215501-7zrfm",  # 您的自定义模型
        "instruction": "Extract financial data from the webpage using your specialized knowledge",
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
# 创建专门的金融数据提取策略
from financial_data_collector.core.crawler.volc_llm_config import create_volc_llm_strategy

extraction_strategy = create_volc_llm_strategy(
    api_key="your_volc_api_key",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    model="ep-20250725215501-7zrfm",  # 您的自定义模型
    instruction="""
    You are a specialized financial data extraction AI. Extract financial data from the webpage with high accuracy.
    
    Your expertise includes:
    - Stock market data analysis
    - Company financial metrics
    - Market trends and indicators
    - News sentiment analysis
    - Earnings and financial statements
    
    Return structured, accurate financial data with clear categorization.
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
                    "market_cap": {"type": "number"},
                    "pe_ratio": {"type": "number"},
                    "dividend_yield": {"type": "number"}
                }
            },
            "news": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                        "relevance": {"type": "number", "minimum": 0, "maximum": 1}
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
        "model": "ep-20250725215501-7zrfm",  # 您的自定义模型
        "instruction": "Extract comprehensive stock market data including prices, volume, and market metrics",
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
                        "dividend_yield": {"type": "number"},
                        "high_52w": {"type": "number"},
                        "low_52w": {"type": "number"}
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
        "model": "ep-20250725215501-7zrfm",  # 您的自定义模型
        "instruction": "Extract financial news with sentiment analysis and relevance scoring",
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
        "model": "ep-20250725215501-7zrfm",  # 您的自定义模型
        "instruction": "Extract comprehensive company information and financial metrics",
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
        {
            "extraction_strategy": "llm",
            "llm_config": {
                "provider": "volc",
                "api_key": "your_volc_api_key",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "ep-20250725215501-7zrfm"  # 您的自定义模型
            }
        }
    )
    results.append({
        "symbol": symbol,
        "data": result.get("financial_data", {})
    })

print(f"批量处理完成，共处理 {len(results)} 个股票")
```

## 🚀 性能优化

### 1. **模型优势**

您的自定义模型`ep-20250725215501-7zrfm`具有以下优势：

- **专业训练**: 针对金融数据提取优化
- **高准确度**: 在金融领域表现更佳
- **快速响应**: 优化的推理速度
- **结构化输出**: 更好的数据格式控制

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

#### 1. **模型端点不可用**
```python
# 检查模型端点
if model != "ep-20250725215501-7zrfm":
    print("❌ 请使用正确的模型端点")
```

#### 2. **API密钥错误**
```python
# 检查API密钥
if not volc_config.api_key:
    raise ValueError("火山引擎API密钥是必需的")
```

#### 3. **网络连接问题**
```python
# 检查网络连接
import requests
try:
    response = requests.get(volc_config.base_url, timeout=10)
    print("✅ 网络连接正常")
except Exception as e:
    print(f"❌ 网络连接失败: {e}")
```

### 调试技巧

#### 1. **启用详细日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. **测试模型连接**
```python
# 测试自定义模型
async def test_custom_model():
    try:
        result = await crawler.crawl_url(
            "https://httpbin.org/get",
            {"extraction_strategy": "llm", "llm_config": volc_config}
        )
        print("✅ 自定义模型连接正常")
        return True
    except Exception as e:
        print(f"❌ 自定义模型连接失败: {e}")
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
You are a specialized financial data extraction AI. Extract financial data from the webpage with high accuracy.

Your expertise includes:
- Stock market data analysis
- Company financial metrics
- Market trends and indicators
- News sentiment analysis
- Earnings and financial statements

Return structured, accurate financial data with clear categorization.
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

通过使用您的自定义模型`ep-20250725215501-7zrfm`，您可以获得：

1. **更高的准确度**: 专为金融数据提取优化
2. **更好的性能**: 针对您的用例优化
3. **更快的响应**: 优化的推理速度
4. **更稳定的输出**: 专业训练的结果

### 快速开始

```bash
# 1. 配置环境变量
echo "VOLC_API_KEY=your_actual_api_key" >> .env
echo "VOLC_BASE_URL=your_actual_base_url" >> .env
echo "VOLC_MODEL=ep-20250725215501-7zrfm" >> .env

# 2. 运行演示
make demo-custom-model

# 3. 测试自定义模型
make test-custom-model
```

现在您可以在Financial Data Collector系统中充分利用您的自定义模型进行高效、准确的金融数据提取了！
