from typing import Dict, Any
from .web_crawler import WebCrawler
from .enhanced_web_crawler import EnhancedWebCrawler

class CrawlerFactory:
    """爬虫工厂类，用于动态创建不同类型的爬虫实例"""
    @staticmethod
    def get_crawler(crawler_type: str, config: Dict[str, Any]) -> WebCrawler:
        """
        获取爬虫实例
        :param crawler_type: 爬虫类型，支持"base"、"enhanced"
        :param config: 爬虫配置字典
        :return: 爬虫实例
        :raises ValueError: 不支持的爬虫类型
        """
        if crawler_type == "base":
            return WebCrawler(config)
        elif crawler_type == "enhanced":
            return EnhancedWebCrawler(config)
        # 未来可扩展其他爬虫类型
        # elif crawler_type == "financial_specialized":
        #     return FinancialWebCrawler(config)
        else:
            raise ValueError(f"不支持的爬虫类型: {crawler_type}")

    @staticmethod
    def get_supported_types() -> list:
        """获取支持的爬虫类型列表"""
        return ["base", "enhanced"]