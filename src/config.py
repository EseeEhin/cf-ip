"""
配置管理模块
负责从环境变量读取配置并提供默认值
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置"""
        # 数据源配置
        self.source_url: str = os.getenv('SOURCE_URL', 'https://cfip.wxgqlfx.fun/')
        self.api_countries_url: str = os.getenv('API_COUNTRIES_URL', 'https://cfip.wxgqlfx.fun/api/countries')
        self.api_query_url: str = os.getenv('API_QUERY_URL', 'https://cfip.wxgqlfx.fun/api/query')
        
        # 过滤配置
        self.max_latency: int = int(os.getenv('MAX_LATENCY', '100'))
        
        # 国家过滤列表（逗号分隔）- 默认改为JP,HK,US
        filter_countries = os.getenv('FILTER_COUNTRIES', 'JP,HK,US')
        self.filter_countries: List[str] = [c.strip() for c in filter_countries.split(',') if c.strip()]
        
        # 查询限制 - 默认改为10
        self.query_limit: int = int(os.getenv('QUERY_LIMIT', '10'))
        
        # 缓存配置
        self.cache_enabled: bool = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_days: int = int(os.getenv('CACHE_DAYS', '30'))
        
        # 输出配置
        self.output_file: str = os.getenv('OUTPUT_FILE', 'output/optimal-ips.txt')
        
        # GitHub配置
        self.github_token: Optional[str] = os.getenv('GITHUB_TOKEN')
        self.github_repo: Optional[str] = os.getenv('GITHUB_REPO')
        self.github_branch: str = os.getenv('GITHUB_BRANCH', 'main')
        self.github_file_path: str = os.getenv('GITHUB_FILE_PATH', 'optimal-ips.txt')
        
        # 订阅项目API配置
        self.subscription_api_url: Optional[str] = os.getenv('SUBSCRIPTION_API_URL')
        self.subscription_api_path: Optional[str] = os.getenv('SUBSCRIPTION_API_PATH')
        self.api_upload_enabled: bool = os.getenv('API_UPLOAD_ENABLED', 'false').lower() == 'true'
        
        # 请求配置
        self.request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
        
        # CF-RAY检测配置（用于获取Cloudflare节点真实位置）
        self.cf_ray_detection_enabled: bool = os.getenv('CF_RAY_DETECTION_ENABLED', 'true').lower() == 'true'
        self.cf_ray_timeout: int = int(os.getenv('CF_RAY_TIMEOUT', '20'))  # 增加到20秒
        self.cf_ray_max_workers: int = int(os.getenv('CF_RAY_MAX_WORKERS', '5'))  # 减少到5个并发
        self.cf_ray_max_retries: int = int(os.getenv('CF_RAY_MAX_RETRIES', '3'))  # CF-RAY重试次数
        
        # Cloudflare IP优先级配置
        self.prefer_cfray_for_cf_ips: bool = os.getenv('PREFER_CFRAY_FOR_CF_IPS', 'true').lower() == 'true'
        
        # ==================== IP检测V2配置 ====================
        # 第三方API配置
        self.api_enabled: bool = os.getenv('ENABLE_API_FALLBACK', 'true').lower() == 'true'
        
        # IPInfo.IO Widget API（主要 - 速度最快0.71s，准确度高）
        self.api_ipinfo_widget_enabled: bool = os.getenv('ENABLE_IPINFO_WIDGET', 'true').lower() == 'true'
        
        # IP-API.COM（备用 - 用户确认准确）
        self.api_ipapi_enabled: bool = os.getenv('ENABLE_IPAPI_COM', 'true').lower() == 'true'
        
        # IPWhois API（备用 - 稳定可靠）
        self.api_ipwhois_enabled: bool = os.getenv('ENABLE_IPWHOIS', 'true').lower() == 'true'
        
        # IP2Location.IO API（辅助）
        self.api_ip2location_enabled: bool = os.getenv('ENABLE_IP2LOCATION', 'false').lower() == 'true'
        
        # API超时和重试配置
        self.api_timeout: int = int(os.getenv('API_TIMEOUT', '5'))
        self.api_max_retries: int = int(os.getenv('API_MAX_RETRIES', '2'))
        
        # API优先级配置（数字越小优先级越高）
        self.api_ipinfo_widget_priority: int = int(os.getenv('API_IPINFO_WIDGET_PRIORITY', '1'))
        self.api_ipapi_priority: int = int(os.getenv('API_IPAPI_PRIORITY', '2'))
        self.api_ipwhois_priority: int = int(os.getenv('API_IPWHOIS_PRIORITY', '3'))
        self.api_ip2location_priority: int = int(os.getenv('API_IP2LOCATION_PRIORITY', '4'))
        
        # 缓存过期时间配置（秒）
        self.cache_ttl_cf_ray: int = int(os.getenv('CACHE_EXPIRE_CFRAY', '86400'))  # 24小时
        self.cache_ttl_api: int = int(os.getenv('CACHE_EXPIRE_API', '43200'))  # 12小时
        self.cache_ttl_geoip: int = int(os.getenv('CACHE_EXPIRE_GEOIP', '604800'))  # 7天
        
        # 失败处理配置
        self.failure_retry_delay: int = int(os.getenv('FAILURE_RETRY_DELAY', '3600'))  # 1小时
        self.api_disable_threshold: int = int(os.getenv('API_DISABLE_THRESHOLD', '3'))
        self.api_disable_duration: int = int(os.getenv('API_DISABLE_DURATION', '600'))  # 10分钟
        
        # 性能配置
        self.detection_max_workers: int = int(os.getenv('DETECTION_MAX_WORKERS', '10'))
        self.detection_timeout: int = int(os.getenv('DETECTION_TIMEOUT', '10'))
        
        # 日志配置
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file: str = os.getenv('LOG_FILE', 'logs/ip_fetcher.log')
        self.log_detection_details: bool = os.getenv('LOG_DETECTION_DETAILS', 'true').lower() == 'true'
    
    def validate(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        if not self.source_url:
            raise ValueError("SOURCE_URL 不能为空")
        
        if self.max_latency <= 0:
            raise ValueError("MAX_LATENCY 必须大于0")
        
        if not self.filter_countries:
            raise ValueError("FILTER_COUNTRIES 不能为空")
        
        if not self.output_file:
            raise ValueError("OUTPUT_FILE 不能为空")
        
        return True
    
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        return f"""
配置信息:
  数据源: {self.source_url}
  最大延迟: {self.max_latency}ms
  过滤国家: {', '.join(self.filter_countries)}
  输出文件: {self.output_file}
  GitHub仓库: {self.github_repo or '未配置'}
  日志级别: {self.log_level}
"""


def get_config() -> Config:
    """
    获取配置实例
    
    Returns:
        Config: 配置对象
    """
    config = Config()
    config.validate()
    return config


# 导出常用配置供其他模块使用
_config = get_config()

# 订阅项目API配置
SUBSCRIPTION_API_URL = _config.subscription_api_url
SUBSCRIPTION_API_PATH = _config.subscription_api_path
API_UPLOAD_ENABLED = _config.api_upload_enabled
API_TIMEOUT = _config.request_timeout

# CF-RAY检测配置
CF_RAY_DETECTION_ENABLED = _config.cf_ray_detection_enabled
CF_RAY_TIMEOUT = _config.cf_ray_timeout
CF_RAY_MAX_WORKERS = _config.cf_ray_max_workers
CF_RAY_MAX_RETRIES = _config.cf_ray_max_retries
PREFER_CFRAY_FOR_CF_IPS = _config.prefer_cfray_for_cf_ips