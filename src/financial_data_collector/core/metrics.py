from typing import Dict, Optional, Any
import time
from prometheus_client import Counter, Histogram, Gauge, Info
import threading

class MetricsCollector:
    """金融数据采集系统指标收集器，符合SEC 17a-4审计要求"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式确保指标收集器全局唯一性"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize_metrics()
        return cls._instance

    def _initialize_metrics(self):
        """初始化金融级监控指标"""
        # 数据采集指标
        self.data_collection_total = Counter(
            'financial_data_collection_total',
            'Total number of financial data collection tasks',
            ['source', 'data_type', 'status']
        )

        # 采集延迟指标（微秒级）- 量化系统关键指标
        self.data_collection_latency = Histogram(
            'financial_data_collection_latency_us',
            'Latency of financial data collection in microseconds',
            ['source', 'data_type'],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000, 500000]
        )

        # 存储性能指标
        self.storage_operation_latency = Histogram(
            'financial_storage_operation_latency_us',
            'Latency of storage operations in microseconds',
            ['operation', 'storage_type', 'status']
        )

        # 系统健康指标
        self.active_collectors = Gauge(
            'financial_active_collectors',
            'Number of active data collectors',
            ['source']
        )

        # 数据质量指标
        self.data_validation_errors = Counter(
            'financial_data_validation_errors',
            'Number of financial data validation errors',
            ['source', 'error_type']
        )

        # 系统信息指标
        self.system_info = Info(
            'financial_data_system',
            'Financial data collection system information'
        )

    def record_collection_start(self, source: str, data_type: str) -> Dict[str, Any]:
        """记录数据采集开始"""
        self.active_collectors.labels(source=source).inc()
        return {
            'start_time': time.perf_counter_ns(),
            'source': source,
            'data_type': data_type
        }

    def record_collection_complete(self, context: Dict[str, Any], success: bool = True, error_type: Optional[str] = None):
        """记录数据采集完成"""
        # 计算微秒级延迟 (ns -> us)
        latency_us = (time.perf_counter_ns() - context['start_time']) // 1000
        self.data_collection_latency.labels(
            source=context['source'],
            data_type=context['data_type']
        ).observe(latency_us)

        # 记录采集状态
        status = 'success' if success else 'failure'
        self.data_collection_total.labels(
            source=context['source'],
            data_type=context['data_type'],
            status=status
        ).inc()

        # 减少活跃采集器计数
        self.active_collectors.labels(source=context['source']).dec()

        # 记录验证错误（如适用）
        if not success and error_type:
            self.data_validation_errors.labels(
                source=context['source'],
                error_type=error_type
            ).inc()

    def record_storage_operation(self, operation: str, storage_type: str, status: str, latency_us: int):
        """记录存储操作性能"""
        self.storage_operation_latency.labels(
            operation=operation,
            storage_type=storage_type,
            status=status
        ).observe(latency_us)

    def set_system_info(self, info: Dict[str, str]):
        """设置系统信息"""
        self.system_info.info(info)

    async def start(self) -> None:
        """启动指标收集器"""
        # MetricsCollector 使用单例模式，在 __new__ 中已经初始化
        # 这里可以添加启动逻辑，比如启动 Prometheus 服务器等
        # 目前 Prometheus 指标是自动暴露的，无需额外启动逻辑
        pass

    async def stop(self) -> None:
        """停止指标收集器"""
        # 清理资源
        # 目前 Prometheus 指标无需特殊清理
        pass

    def get_instance() -> 'MetricsCollector':
        """获取单例实例"""
        if MetricsCollector._instance is None:
            MetricsCollector()
        return MetricsCollector._instance