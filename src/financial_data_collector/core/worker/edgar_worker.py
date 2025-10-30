import logging
from typing import Any, Dict, List, Optional

from ..core.base import FinancialBaseWorker
from ..core.utils.edgar_client import EDGARClient


class EDGARWorker(FinancialBaseWorker):
    """
    EDGAR 数据抓取 Worker，负责从 SEC EDGAR 系统获取公司财务报告元数据与文件链接。
    不包含审计相关逻辑。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.edgar_client = EDGARClient(
            user_agent=config["edgar"]["user_agent"],
            retry_times=config["edgar"].get("retry_times", 3),
            retry_delay=config["edgar"].get("retry_delay", 1),
            timeout=config["edgar"].get("timeout", 30),
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_company_filings(
        self,
        ticker: str,
        form_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取指定公司提交的文件列表。

        :param ticker: 公司股票代码
        :param form_type: 报告类型（如 10-K、10-Q），None 表示全部
        :param start_date: 开始日期，格式 YYYY-MM-DD
        :param end_date: 结束日期，格式 YYYY-MM-DD
        :param limit: 最大返回条数
        :return: 文件元数据列表
        """
        try:
            filings = self.edgar_client.get_submissions(
                ticker=ticker,
                form_type=form_type,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
            self.logger.info(
                "成功获取 %s 的 %d 条 filings", ticker, len(filings)
            )
            return filings
        except Exception as e:
            self.logger.error("获取 %s 的 filings 失败: %s", ticker, e)
            return []

    def fetch_filing_content(self, accession_number: str, ticker: str) -> Optional[str]:
        """
        根据 accession_number 下载并返回原始 filing 文本内容。

        :param accession_number: 报告唯一编号
        :param ticker: 公司股票代码
        :return: 原始文本，失败返回 None
        """
        try:
            content = self.edgar_client.get_filing_text(
                accession_number=accession_number, ticker=ticker
            )
            self.logger.info(
                "成功下载 %s 的 filing %s", ticker, accession_number
            )
            return content
        except Exception as e:
            self.logger.error(
                "下载 %s 的 filing %s 失败: %s", ticker, accession_number, e
            )
            return None

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个任务入口，任务字典需包含：
        - action: "filings" 或 "content"
        - ticker: 股票代码
        可选参数：
        - form_type / start_date / end_date / limit / accession_number

        :param task: 任务描述
        :return: 执行结果
        """
        action = task.get("action")
        ticker = task["ticker"]

        if action == "filings":
            filings = self.fetch_company_filings(
                ticker=ticker,
                form_type=task.get("form_type"),
                start_date=task.get("start_date"),
                end_date=task.get("end_date"),
                limit=task.get("limit", 100),
            )
            return {"status": "success", "data": filings}
        elif action == "content":
            content = self.fetch_filing_content(
                accession_number=task["accession_number"], ticker=ticker
            )
            if content is None:
                return {"status": "failed", "error": "download failed"}
            return {"status": "success", "data": content}
        else:
            return {"status": "failed", "error": f"unknown action: {action}"}
