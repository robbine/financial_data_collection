import logging
import sys
from typing import Dict, Optional
from pythonjsonlogger import jsonlogger

def setup_structured_logging(
    log_level: str = "INFO",
    service_name: str = "financial_data_collector",
    extra_fields: Optional[Dict[str, str]] = None
) -> None:
    """初始化金融级结构化日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: 服务名称，用于日志标识
        extra_fields: 附加到所有日志记录的额外字段
    """
    # 配置基础日志格式
    log_format = (
        f"%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d"
        f" {' '.join([f'%({k})s' for k in extra_fields.keys()]) if extra_fields else ''} %(message)s"
    )

    # 创建JSON格式化器（符合金融系统日志规范）
    formatter = jsonlogger.JsonFormatter(
        fmt=log_format,
        rename_fields={
            "levelname": "level",
            "asctime": "timestamp",
            "module": "source_module",
            "funcName": "function"
        },
        timestamp=True
    )

    # 配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 获取根日志器并配置
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.propagate = False

    # 添加服务标识和额外字段到所有日志
    if extra_fields:
        class ExtraFieldsFilter(logging.Filter):
            def filter(self, record):
                for k, v in extra_fields.items():
                    setattr(record, k, v)
                setattr(record, "service", service_name)
                return True
        root_logger.addFilter(ExtraFieldsFilter())

    # 设置第三方库日志级别
    for library in ["requests", "urllib3", "pymongo"]:
        logging.getLogger(library).setLevel(logging.WARNING)

    logging.info(f"金融级结构化日志系统初始化完成，服务名称: {service_name}，日志级别: {log_level}")