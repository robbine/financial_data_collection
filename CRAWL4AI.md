# Crawl4AI 集成指南

本文档详细说明如何在Financial Data Collector系统中使用Crawl4AI进行高级网页爬取。

## 🚀 什么是Crawl4AI

Crawl4AI是一个专为AI应用设计的开源Python库，旨在简化网页抓取和数据提取过程。它提供了：

- **异步爬虫**: 高性能异步网页爬取
- **浏览器配置**: 支持多种浏览器和配置选项
- **智能提取**: 基于LLM的内容提取策略
- **Markdown转换**: 自动将HTML转换为Markdown
- **多种提取策略**: CSS选择器、XPath、LLM等

## 📦 安装和配置

### 1. 安装Crawl4AI
```bash
# 安装crawl4ai
pip install crawl4ai==0.3.70

# 安装playwright依赖
pip install playwright==1.40.0

# 运行设置脚本
crawl4ai-setup
```

### 2. Docker环境
如果使用Docker，crawl4ai已经包含在Dockerfile中：
```bash
# 构建包含crawl4ai的镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 🔧 配置说明

### 基本配置
```yaml
web_crawler:
  config:
    browser:
      browser_type: "chromium"  # chromium, firefox, webkit
      headless: true
      viewport:
        width: 1920
        height: 1080
      user_agent: "Financial Data Collector 1.0"
    
    extraction_strategy: "llm"  # llm, css, xpath
    request_delay: 1.0
    max_concurrent_requests: 5
    timeout: 30
```

### LLM提取策略
```yaml
llm_config:
  provider: "openai"  # openai, anthropic, local
  model: "gpt-4"
  api_token: "${OPENAI_API_KEY}"
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

### CSS提取策略
```yaml
financial_selectors:
  price: [".price", ".quote-price", "[data-testid*='price']"]
  volume: [".volume", ".quote-volume", "[data-testid*='volume']"]
  change: [".change", ".quote-change", "[data-testid*='change']"]
  market_cap: [".market-cap", ".market-value", "[data-testid*='market-cap']"]
  news: [".news-item", ".article", ".story"]
```

## 💻 使用方法

### 基本使用
```python
from financial_data_collector.core.crawler.web_crawler import WebCrawler

# 创建爬虫实例
crawler = WebCrawler("MyCrawler")

# 初始化配置
config = {
    "browser": {"headless": True},
    "extraction_strategy": "llm",
    "llm_config": {
        "provider": "openai",
        "model": "gpt-4",
        "api_token": "your-api-key"
    }
}
crawler.initialize(config)

# 启动爬虫
await crawler.start()

# 爬取网页
result = await crawler.crawl_url(
    "https://finance.yahoo.com/quote/AAPL",
    {
        "extraction_strategy": "llm",
        "wait_for": 3,
        "max_scrolls": 2
    }
)

# 停止爬虫
await crawler.stop()
```

### 高级配置
```python
# 配置浏览器选项
browser_config = {
    "browser_type": "chromium",
    "headless": False,  # 显示浏览器窗口
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Custom User Agent",
    "proxy": "http://proxy:8080",  # 代理设置
    "cookies": [{"name": "session", "value": "abc123"}]
}

# 配置提取策略
extraction_config = {
    "extraction_strategy": "llm",
    "llm_config": {
        "provider": "openai",
        "model": "gpt-4",
        "api_token": "your-api-key",
        "instruction": "Extract financial data including stock prices, volume, and news",
        "schema": {
            "type": "object",
            "properties": {
                "stock_data": {"type": "object"},
                "news": {"type": "array"},
                "company_info": {"type": "object"}
            }
        }
    }
}

# 配置爬取选项
crawl_options = {
    "wait_for": 3,  # 等待页面加载
    "max_scrolls": 5,  # 最大滚动次数
    "word_count_threshold": 100,  # 最小字数阈值
    "cache_mode": "BYPASS"  # 缓存模式
}
```

## 🎯 金融数据爬取示例

### 1. 股票数据爬取
```python
# 爬取Yahoo Finance股票页面
stock_data = await crawler.crawl_url(
    "https://finance.yahoo.com/quote/AAPL",
    {
        "extraction_strategy": "css",
        "css_selectors": {
            "price": "[data-field='regularMarketPrice']",
            "volume": "[data-field='regularMarketVolume']",
            "change": "[data-field='regularMarketChange']",
            "market_cap": "[data-field='marketCap']"
        },
        "wait_for": 2
    }
)
```

### 2. 新闻数据爬取
```python
# 爬取金融新闻
news_data = await crawler.crawl_url(
    "https://finance.yahoo.com/news/",
    {
        "extraction_strategy": "llm",
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4",
            "instruction": "Extract financial news headlines, summaries, and timestamps"
        },
        "wait_for": 3,
        "max_scrolls": 3
    }
)
```

### 3. 批量爬取
```python
# 爬取多个股票页面
urls = [
    "https://finance.yahoo.com/quote/AAPL",
    "https://finance.yahoo.com/quote/MSFT",
    "https://finance.yahoo.com/quote/GOOGL"
]

results = await crawler.crawl_multiple_urls(
    urls,
    {
        "extraction_strategy": "css",
        "css_selectors": {
            "price": "[data-field='regularMarketPrice']",
            "symbol": "[data-field='symbol']"
        }
    }
)
```

## 🔍 数据提取策略

### 1. LLM提取策略
适用于复杂的内容提取，需要AI理解：
```python
llm_strategy = {
    "extraction_strategy": "llm",
    "llm_config": {
        "provider": "openai",
        "model": "gpt-4",
        "instruction": "Extract all financial metrics and news from the page",
        "schema": {
            "type": "object",
            "properties": {
                "stock_metrics": {
                    "type": "object",
                    "properties": {
                        "price": {"type": "number"},
                        "volume": {"type": "number"},
                        "market_cap": {"type": "number"}
                    }
                },
                "news_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "timestamp": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}
```

### 2. CSS提取策略
适用于结构化数据提取：
```python
css_strategy = {
    "extraction_strategy": "css",
    "css_selectors": {
        "price": ".quote-price, [data-testid*='price']",
        "volume": ".quote-volume, [data-testid*='volume']",
        "news": ".news-item, .article",
        "company_name": ".company-name, h1"
    }
}
```

### 3. 混合策略
结合多种提取方法：
```python
mixed_strategy = {
    "extraction_strategy": "css",  # 基础CSS提取
    "css_selectors": {
        "basic_data": ".quote-data"
    },
    "llm_config": {  # 对提取的内容进行AI分析
        "provider": "openai",
        "model": "gpt-4",
        "instruction": "Analyze the extracted financial data and provide insights"
    }
}
```

## ⚡ 性能优化

### 1. 并发控制
```python
config = {
    "max_concurrent_requests": 10,  # 最大并发请求数
    "request_delay": 1.0,  # 请求间隔
    "timeout": 30  # 请求超时
}
```

### 2. 缓存策略
```python
cache_options = {
    "cache_mode": "BYPASS",  # 绕过缓存
    "cache_ttl": 3600  # 缓存生存时间
}
```

### 3. 资源管理
```python
browser_config = {
    "headless": True,  # 无头模式节省资源
    "viewport": {"width": 1920, "height": 1080},
    "memory_limit": "2GB"  # 内存限制
}
```

## 🛠️ 故障排除

### 常见问题

#### 1. 浏览器启动失败
```bash
# 重新安装浏览器依赖
crawl4ai-setup

# 检查系统依赖
apt-get update && apt-get install -y chromium-browser
```

#### 2. LLM API调用失败
```python
# 检查API密钥
config = {
    "llm_config": {
        "provider": "openai",
        "api_token": "your-valid-api-key",
        "model": "gpt-4"
    }
}
```

#### 3. 页面加载超时
```python
# 增加等待时间
options = {
    "wait_for": 5,  # 增加等待时间
    "timeout": 60,  # 增加超时时间
    "max_scrolls": 0  # 减少滚动次数
}
```

#### 4. 内存不足
```python
# 优化浏览器配置
browser_config = {
    "headless": True,
    "memory_limit": "1GB",
    "disable_images": True,  # 禁用图片加载
    "disable_css": True  # 禁用CSS加载
}
```

### 调试技巧

#### 1. 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 保存页面截图
```python
options = {
    "screenshot": True,
    "screenshot_path": "/tmp/screenshot.png"
}
```

#### 3. 保存HTML内容
```python
result = await crawler.crawl_url(url, options)
print("HTML content:", result.html)
print("Markdown content:", result.markdown)
```

## 📊 监控和指标

### 健康检查
```python
health = await crawler.health_check()
print(f"Status: {health['status']}")
print(f"Details: {health['details']}")
```

### 性能指标
```python
# 获取爬取统计
stats = crawler.get_crawl_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']}")
print(f"Average response time: {stats['avg_response_time']}")
```

## 🔒 安全和合规

### 1. 遵守robots.txt
```python
config = {
    "respect_robots_txt": True,
    "user_agent": "Financial Data Collector 1.0"
}
```

### 2. 请求频率控制
```python
config = {
    "request_delay": 2.0,  # 2秒间隔
    "max_concurrent_requests": 3  # 限制并发
}
```

### 3. 代理使用
```python
browser_config = {
    "proxy": "http://proxy:8080",
    "proxy_auth": {"username": "user", "password": "pass"}
}
```

## 📚 最佳实践

1. **合理使用LLM**: 只在需要复杂理解时使用LLM提取
2. **缓存策略**: 对不经常变化的数据使用缓存
3. **错误处理**: 实现完善的错误处理和重试机制
4. **资源管理**: 及时关闭浏览器实例释放资源
5. **合规性**: 遵守网站的robots.txt和使用条款

## 🚀 高级功能

### 1. 自定义提取器
```python
class CustomExtractor:
    def extract(self, html, url):
        # 自定义提取逻辑
        return extracted_data
```

### 2. 数据后处理
```python
def post_process_data(data):
    # 数据清洗和转换
    return cleaned_data
```

### 3. 实时监控
```python
# 设置监控回调
def on_crawl_complete(result):
    print(f"Crawl completed: {result.url}")

crawler.set_callback("complete", on_crawl_complete)
```

通过以上配置和使用方法，您可以在Financial Data Collector系统中充分利用Crawl4AI的强大功能，实现高效、智能的金融数据爬取。
