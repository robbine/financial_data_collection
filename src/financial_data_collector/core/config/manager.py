from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from src.financial_data_collector.core.interfaces import BaseModule

class ConfigManager(BaseModule):
    """Configuration manager for loading and accessing application settings"""
    _instance: Optional['ConfigManager'] = None
    _config: Dict[str, Any] = {}
    _config_paths: Dict[str, str] = {
        'development': 'config/development.yaml',
        'production': 'config/production.yaml',
        'local': 'config/local.yaml'
    }
    
    def __init__(self):
        super().__init__(name="config_manager")  # 调用父类初始化
        self._config = {}
        self._config_paths = {
            'development': 'config/development.yaml',
            'production': 'config/production.yaml',
            'local': 'config/local.yaml'
        }
        self._initialized = False

    async def initialize(self, config=None):
        """模块初始化方法"""
        self.load_config()
        # 添加初始化日志
        import logging
        logging.info("ConfigManager initialized successfully")
        self._initialized = True
        logger.info("ConfigManager initialized successfully")
        return True
    
    def is_initialized(self):
        return self._initialized
    
    def get_name(self):
        return "config_manager"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_config(self):
        """加载配置文件"""
        # 获取环境变量指定的配置环境，默认为development
        env = os.getenv('CONFIG_ENV', 'development')
        # 构建配置文件路径
        config_dir = os.path.join(os.path.dirname(__file__), '../../../../', 'config')
        env_config_path = os.path.join(config_dir, f'{env}.yaml')
        
        # 检查环境配置文件是否存在
        if not os.path.exists(env_config_path):
            raise FileNotFoundError(f"Configuration file not found: {env_config_path}")
        
        # 加载环境特定配置
        self._load_file(env_config_path)
        self.logger.info(f"Loaded configuration from: {env_config_path}")
        self.logger.info(f"ClickHouse config loaded: {self._config.get('clickhouse')}")
        
        # 加载本地覆盖配置（如果存在）
        local_config_path = os.path.join(config_dir, 'local.yaml')
        if os.path.exists(local_config_path):
            self._load_file(local_config_path)
            self.logger.info(f"Loaded local override configuration from: {local_config_path}")
        
        # 合并环境变量
        self._merge_environment_variables()
        
        return self

    def get_config(self) -> Dict[str, Any]:
        """Get the loaded configuration"""
        return self._config

    def _load_file(self, file_path: str) -> None:
        """Load configuration from a single YAML file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            if config_data:
                self._merge_config(self._config, config_data)

    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries"""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value

    def _merge_environment_variables(self) -> None:
        """Merge environment variables into configuration"""
        # Implementation would map environment variables to config keys
        # Example: FDC_DATABASE_URL would map to database.url
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dotted path"""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

# Initialize config manager singleton
config_manager = ConfigManager()