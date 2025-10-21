# 测试套件说明

## 概述

本测试套件为金融数据收集系统的消息队列功能提供全面的测试覆盖，包括单元测试、集成测试、端到端测试和性能测试。

## 测试结构

```
tests/
├── conftest.py                    # Pytest配置和公共fixtures
├── test_message_queue.py          # 消息队列单元测试
├── test_api_integration.py        # API集成测试
├── test_e2e_message_queue.py      # 端到端测试
├── test_performance.py            # 性能测试
├── test_webcrawler.py             # WebCrawler测试
└── README.md                      # 本文档
```

## 测试类型

### 1. 单元测试 (`test_message_queue.py`)

**测试范围：**
- TaskManager 功能测试
- Celery 任务函数测试
- 消息队列集成测试
- 错误处理和重试机制

**运行命令：**
```bash
make test-unit
# 或
docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_message_queue.py -v
```

### 2. API集成测试 (`test_api_integration.py`)

**测试范围：**
- REST API 端点测试
- 请求/响应验证
- 错误处理测试
- 并发请求测试

**运行命令：**
```bash
make test-api
# 或
docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_api_integration.py -v
```

### 3. 端到端测试 (`test_e2e_message_queue.py`)

**测试范围：**
- 完整任务生命周期测试
- 批量任务处理测试
- 优先级处理测试
- 延迟任务执行测试
- LLM提取集成测试

**运行命令：**
```bash
make test-e2e
# 或
docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_e2e_message_queue.py -v -m integration
```

### 4. 性能测试 (`test_performance.py`)

**测试范围：**
- 负载测试
- 内存使用测试
- 吞吐量测试
- 延迟测试
- 压力测试

**运行命令：**
```bash
make test-performance
# 或
docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_performance.py -v -s
```

## 测试命令

### 基础测试命令

```bash
# 运行所有测试
make test-all

# 运行单元测试
make test-unit

# 运行API测试
make test-api

# 运行端到端测试
make test-e2e

# 运行性能测试
make test-performance
```

### 组件特定测试

```bash
# 测试爬虫组件
make test-crawler

# 测试任务管理
make test-tasks

# 测试Celery任务
make test-celery
```

### 性能测试

```bash
# 负载测试
make test-load

# 压力测试
make test-stress
```

### 测试报告

```bash
# 生成覆盖率报告
make test-coverage

# 生成HTML测试报告
make test-report

# 清理测试文件
make clean-tests
```

## 测试配置

### 环境变量

```bash
# 运行端到端测试
export RUN_E2E_TESTS=1

# 运行性能测试
export RUN_PERFORMANCE_TESTS=1

# 设置测试环境
export TEST_ENV=development
```

### 测试标记

```bash
# 运行集成测试
make test-integration

# 运行慢速测试
make test-slow

# 运行特定标记的测试
docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ -m "integration and not slow"
```

## 测试数据

### Fixtures

测试套件提供了丰富的fixtures：

- `mock_redis`: Redis连接模拟
- `mock_celery_app`: Celery应用模拟
- `test_config`: 测试配置
- `test_urls`: 测试URL列表
- `mock_crawl_result`: 模拟爬取结果
- `mock_llm_config`: LLM配置模拟
- `sample_financial_data`: 示例金融数据

### 测试数据示例

```python
# 使用fixtures
def test_crawl_task(mock_webcrawler, test_config):
    # 测试代码
    pass

# 自定义测试数据
def test_batch_processing():
    urls = ["https://httpbin.org/html", "https://httpbin.org/json"]
    config = {"extraction_strategy": "css"}
    # 测试代码
```

## 测试最佳实践

### 1. 测试隔离

每个测试都应该独立运行，不依赖其他测试的状态。

```python
def test_task_submission():
    # 使用fixtures确保测试隔离
    task_manager = TaskManager()
    # 测试代码
```

### 2. 模拟外部依赖

使用Mock对象模拟外部服务：

```python
@patch('src.financial_data_collector.core.tasks.task_manager.celery_app')
def test_task_submission(mock_celery):
    # 测试代码
```

### 3. 异步测试

正确处理异步测试：

```python
@pytest.mark.asyncio
async def test_async_crawl():
    result = await crawler.collect_data("web", config)
    assert result["success"] is True
```

### 4. 性能测试

性能测试应该包含：

- 基准性能指标
- 内存使用监控
- 并发处理能力
- 错误率统计

## 持续集成

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: make test-all
```

### 本地开发

```bash
# 开发时运行快速测试
make test-unit

# 提交前运行完整测试
make test-all

# 性能回归测试
make test-performance
```

## 故障排除

### 常见问题

1. **测试超时**
   - 检查网络连接
   - 增加超时时间
   - 使用Mock对象

2. **内存泄漏**
   - 检查fixtures清理
   - 监控内存使用
   - 使用内存分析工具

3. **并发问题**
   - 使用线程安全的数据结构
   - 避免共享状态
   - 使用适当的同步机制

### 调试技巧

```bash
# 详细输出
make test-debug

# 只运行失败的测试
make test-failed

# 特定测试类
docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_message_queue.py::TestTaskManager -v
```

## 测试覆盖率

目标覆盖率：
- 单元测试：> 90%
- 集成测试：> 80%
- 端到端测试：> 70%

查看覆盖率报告：
```bash
make test-coverage
```

## 贡献指南

1. 为新功能编写测试
2. 保持测试独立性
3. 使用描述性的测试名称
4. 添加适当的文档
5. 遵循测试最佳实践

## 参考资料

- [Pytest文档](https://docs.pytest.org/)
- [FastAPI测试](https://fastapi.tiangolo.com/tutorial/testing/)
- [Celery测试](https://docs.celeryproject.org/en/stable/userguide/testing.html)
- [异步测试](https://pytest-asyncio.readthedocs.io/)


