# Financial Data Collector

一个模块化的金融数据采集、处理和存储系统，支持多种数据源和实时处理。

## 特性

### 🏗️ 模块化架构
- **依赖注入系统**: 松耦合的模块依赖管理
- **事件驱动架构**: 异步事件处理和通信
- **插件系统**: 动态加载和卸载功能模块
- **中间件管道**: 数据处理链式操作
- **模块生命周期管理**: 统一的启动、停止、重启机制

### 📊 数据采集
- **Web爬虫**: 基于Crawl4AI的高级网页爬取，支持LLM智能提取
- **API数据源**: RESTful API数据获取，支持多种金融API
- **数据库连接**: 直接数据库查询，支持多种数据库类型
- **文件处理**: 多种格式文件读取和处理

### 🔄 数据处理
- **数据清洗**: 去重、填充缺失值、异常值处理
- **AI处理**: 智能数据分析和处理
- **PIT转换**: 点对点数据转换
- **实时处理**: 流式数据处理

### 📈 任务调度
- **定时任务**: 基于cron表达式的任务调度
- **任务管理**: 任务状态跟踪和重试机制
- **并发控制**: 多任务并行执行

### 💾 存储管理
- **数据库存储**: 关系型数据库支持
- **缓存系统**: 高性能缓存存储
- **PIT存储**: 专用数据格式存储

### 🔍 监控和健康检查
- **实时监控**: 系统状态实时监控
- **健康检查**: 模块健康状态检查
- **告警系统**: 异常情况自动告警

## 架构设计

### 核心模块

```
src/financial_data_collector/
├── core/                    # 核心模块
│   ├── config/              # 配置管理
│   ├── crawler/             # 数据采集
│   ├── processor/           # 数据处理
│   ├── scheduler/           # 任务调度
│   ├── storage/             # 存储管理
│   ├── di/                  # 依赖注入
│   ├── events/              # 事件系统
│   ├── middleware/          # 中间件系统
│   ├── plugins/             # 插件系统
│   ├── module_manager.py   # 模块管理器
│   ├── health_checker.py    # 健康检查
│   └── interfaces.py        # 接口定义
├── api/                     # API模块
├── models/                   # 数据模型
├── utils/                    # 工具函数
└── web/                      # Web界面
```

### 模块化特性

#### 1. 依赖注入容器
```python
from src.financial_data_collector.core.di import DIContainer

container = DIContainer()
container.register_singleton(ConfigManager, ConfigManager)
container.register_factory(DataProcessor, lambda: DataProcessor())

# 自动解析依赖
processor = container.get(DataProcessor)
```

#### 2. 事件系统
```python
from src.financial_data_collector.core.events import EventBus, DataCollectedEvent

event_bus = EventBus()

# 订阅事件
def handle_data_collected(event):
    print(f"Data collected: {event.data}")

event_bus.subscribe("data_collected", handle_data_collected)

# 发布事件
event = DataCollectedEvent(data={"test": "data"}, source="crawler")
event_bus.publish(event)
```

#### 3. 中间件系统
```python
from src.financial_data_collector.core.middleware import (
    MiddlewarePipeline, LoggingMiddleware, ValidationMiddleware
)

pipeline = MiddlewarePipeline("DataProcessing")
pipeline.add_middleware(LoggingMiddleware())
pipeline.add_middleware(ValidationMiddleware(required_fields=["id", "name"]))

result = await pipeline.process(data)
```

#### 4. 插件系统
```python
from src.financial_data_collector.core.plugins import PluginRegistry, SentimentAnalysisPlugin

registry = PluginRegistry()
registry.register_plugin("sentiment", SentimentAnalysisPlugin)

plugin = registry.create_plugin_instance("sentiment")
plugin.initialize({"sensitivity_threshold": 0.1})
result = plugin.execute("This is positive financial news")
```

#### 5. 模块管理
```python
from src.financial_data_collector.core.module_manager import ModuleManager, ModuleConfig

module_manager = ModuleManager(di_container, event_bus)

# 注册模块
config = ModuleConfig(
    name="data_collector",
    dependencies=["config_manager"],
    startup_order=1
)
module_manager.register_module("data_collector", WebCrawler, config)

# 启动所有模块
await module_manager.start_all_modules()
```

## 安装和配置

### 环境要求
- Python 3.8+ (本地开发)
- Docker & Docker Compose (推荐)
- pip 或 conda

### 🐳 Docker 安装 (推荐)

#### 快速开始
```bash
# 克隆项目
git clone <repository-url>
cd financial_data_collection

# 运行初始设置
make setup

# 启动开发环境
make dev

# 或使用脚本
./scripts/docker-setup.sh
```

#### 使用 Docker Compose
```bash
# 启动所有服务
docker-compose up -d

# 启动开发环境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 服务访问地址
- **应用**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **pgAdmin**: http://localhost:5050 (admin@fdc.local/admin)
- **Redis Commander**: http://localhost:8081
- **Jupyter**: http://localhost:8888 (token: dev_token_123)

### 🕷️ Crawl4AI 集成

#### 安装Crawl4AI
```bash
# 安装Crawl4AI
make install-crawl4ai

# 或手动安装
pip install crawl4ai==0.3.70
python -m crawl4ai.setup
```

#### 使用Crawl4AI
```python
from financial_data_collector.core.crawler.web_crawler import WebCrawler

# 创建爬虫
crawler = WebCrawler()
crawler.initialize({
    "extraction_strategy": "llm",
    "llm_config": {
        "provider": "openai",
        "model": "gpt-4",
        "api_token": "your-api-key"
    }
})

# 爬取金融数据
result = await crawler.crawl_url(
    "https://finance.yahoo.com/quote/AAPL",
    {"extraction_strategy": "llm", "wait_for": 3}
)
```

#### 测试Crawl4AI
```bash
# 运行演示
make test-crawl4ai

# 或直接运行
python examples/crawl4ai_demo.py
```

### 🐍 本地安装

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置文件
系统使用YAML配置文件，默认配置文件为 `config.yaml`：

```yaml
# 应用设置
app:
  name: "Financial Data Collector"
  version: "1.0.0"
  debug: false

# 模块配置
modules:
  web_crawler:
    class: "src.financial_data_collector.core.crawler.web_crawler.WebCrawler"
    enabled: true
    dependencies: ["config_manager"]
    config:
      user_agent: "Financial Data Collector 1.0"
      request_delay: 1.0
```

## 使用方法

### 启动应用
```bash
python -m src.financial_data_collector.main
```

### 编程接口
```python
from src.financial_data_collector.main import FinancialDataCollectorApp

app = FinancialDataCollectorApp()
await app.initialize(config)
await app.start()
```

### API接口
系统提供RESTful API接口：

- `GET /api/v1/status` - 获取系统状态
- `GET /api/v1/modules` - 获取模块列表
- `POST /api/v1/tasks` - 创建任务
- `GET /api/v1/health` - 健康检查

## 开发指南

### 创建自定义模块
```python
from src.financial_data_collector.core.interfaces import BaseModule

class CustomDataProcessor(BaseModule):
    async def process_data(self, data):
        # 自定义处理逻辑
        return processed_data
    
    async def health_check(self):
        return {"status": "healthy"}
```

### 创建自定义插件
```python
from src.financial_data_collector.core.plugins.base import DataProcessorPlugin

class CustomPlugin(DataProcessorPlugin):
    def process_data(self, data):
        # 自定义处理逻辑
        return result
```

### 创建自定义中间件
```python
from src.financial_data_collector.core.middleware.base import Middleware

class CustomMiddleware(Middleware):
    async def process(self, data, next_middleware):
        # 处理前逻辑
        result = await next_middleware()
        # 处理后逻辑
        return result
```

## 测试

### 运行测试
```bash
pytest tests/ -v
```

### 集成测试
```bash
pytest tests/test_modular_system.py -v
```

## 监控和运维

### 健康检查
系统提供多种健康检查方式：

1. **模块级健康检查**: 每个模块实现自己的健康检查逻辑
2. **系统级健康检查**: 整体系统状态监控
3. **API健康检查**: HTTP接口健康检查

### 日志监控
系统使用结构化日志，支持多种日志级别：
- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 性能监控
- 内存使用监控
- CPU使用监控
- 网络I/O监控
- 数据库连接监控

## 扩展性

### 添加新的数据源
1. 实现 `DataCollectorInterface` 接口
2. 注册到依赖注入容器
3. 配置模块启动参数

### 添加新的数据处理
1. 实现 `DataProcessorInterface` 接口
2. 配置中间件管道
3. 设置处理规则

### 添加新的存储后端
1. 实现 `StorageInterface` 接口
2. 配置连接参数
3. 注册到模块管理器

## 故障排除

### 常见问题

1. **模块启动失败**
   - 检查依赖关系
   - 验证配置参数
   - 查看日志信息

2. **数据采集失败**
   - 检查网络连接
   - 验证数据源配置
   - 查看错误日志

3. **性能问题**
   - 调整并发参数
   - 优化数据处理逻辑
   - 监控资源使用

### 调试模式
启用调试模式获取详细日志：
```yaml
app:
  debug: true
  log_level: "DEBUG"
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 文档: [Documentation]
