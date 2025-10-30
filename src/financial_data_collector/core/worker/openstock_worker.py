class OpenStockWorker(FinancialBaseWorker):
    def __init__(self, app_name: str, queue_name: str):
        super().__init__(app_name, queue_name)        # 本地部署配置
        self.base_url = "http://localhost:8000"  # 假设本地 openstock 服务端口为 8000
        self.session = requests.Session()
        self.session.timeout = 30  # 统一超时 30 秒
