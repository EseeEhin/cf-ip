"""
API Provider模块
提供第三方IP查询API的统一接口和具体实现
"""

import time
import logging
import requests
from typing import Dict, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAPIProvider(ABC):
    """IP查询API基类"""
    
    def __init__(self, name: str, timeout: int = 3):
        """
        初始化API Provider
        
        Args:
            name: API名称
            timeout: 请求超时时间（秒）
        """
        self.name = name
        self.timeout = timeout
        self.enabled = True
        self.failure_count = 0
        self.last_success_time = None
        self.last_failure_time = None
        self.total_requests = 0
        self.successful_requests = 0
    
    @abstractmethod
    def query(self, ip: str) -> Optional[Dict]:
        """
        查询IP信息
        
        Args:
            ip: IP地址
            
        Returns:
            标准化的位置信息字典，失败返回None
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: requests.Response) -> Optional[Dict]:
        """
        解析API响应
        
        Args:
            response: requests响应对象
            
        Returns:
            标准化的位置信息字典，失败返回None
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查API是否可用
        
        Returns:
            bool: API是否可用
        """
        return self.enabled
    
    def mark_success(self):
        """标记成功"""
        self.failure_count = 0
        self.last_success_time = time.time()
        self.successful_requests += 1
        logger.debug(f"API成功: {self.name}")
    
    def mark_failure(self):
        """标记失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.debug(f"API失败: {self.name}, 失败次数: {self.failure_count}")
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        return {
            'name': self.name,
            'enabled': self.enabled,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'success_rate': f"{success_rate:.1f}%",
            'failure_count': self.failure_count,
            'last_success_time': self.last_success_time,
            'last_failure_time': self.last_failure_time
        }


class BaiduAPIProvider(BaseAPIProvider):
    """百度IP查询API"""
    
    def __init__(self, timeout: int = 3):
        super().__init__('baidu_api', timeout)
        self.url_template = 'http://opendata.baidu.com/api.php?query={ip}&resource_id=6006&oe=utf8'
    
    def query(self, ip: str) -> Optional[Dict]:
        """查询IP信息"""
        self.total_requests += 1
        
        try:
            url = self.url_template.format(ip=ip)
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            result = self.parse_response(response)
            
            if result:
                self.mark_success()
                return result
            else:
                self.mark_failure()
                return None
        
        except requests.exceptions.Timeout:
            logger.debug(f"百度API超时: {ip}")
            self.mark_failure()
            return None
        
        except requests.exceptions.RequestException as e:
            logger.debug(f"百度API请求失败: {ip}, {e}")
            self.mark_failure()
            return None
        
        except Exception as e:
            logger.error(f"百度API异常: {ip}, {e}")
            self.mark_failure()
            return None
    
    def parse_response(self, response: requests.Response) -> Optional[Dict]:
        """解析百度API响应"""
        try:
            data = response.json()
            
            if data.get('status') == '0' and 'data' in data and len(data['data']) > 0:
                info = data['data'][0]
                location = info.get('location', '').strip()
                
                if not location:
                    return None
                
                # 解析位置信息: "国家 省份 城市"
                parts = location.split()
                
                country = self._parse_country(parts[0] if len(parts) > 0 else '')
                city = parts[-1] if len(parts) > 0 else 'Unknown'
                
                return {
                    'country': country,
                    'country_name': parts[0] if len(parts) > 0 else 'Unknown',
                    'city': city,
                    'isp': '',
                    'source': 'baidu_api',
                    'confidence': 0.85
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"百度API响应解析失败: {e}")
            return None
    
    def _parse_country(self, country_name: str) -> str:
        """解析国家名称为国家代码"""
        country_map = {
            '中国': 'CN',
            '美国': 'US',
            '日本': 'JP',
            '韩国': 'KR',
            '新加坡': 'SG',
            '香港': 'HK',
            '台湾': 'TW',
            '英国': 'GB',
            '德国': 'DE',
            '法国': 'FR',
            '加拿大': 'CA',
            '澳大利亚': 'AU',
        }
        return country_map.get(country_name, 'Unknown')


class IPAPIProvider(BaseAPIProvider):
    """IP-API.COM查询API"""
    
    def __init__(self, timeout: int = 3):
        super().__init__('ip_api_com', timeout)
        self.url_template = 'http://ip-api.com/json/{ip}?lang=zh-CN'
        self.rate_limit_requests = []
        self.rate_limit_max = 45  # 45次/分钟
        self.rate_limit_window = 60  # 60秒
    
    def is_available(self) -> bool:
        """检查API是否可用（包括限流检查）"""
        if not self.enabled:
            return False
        
        # 检查限流
        return self._check_rate_limit()
    
    def _check_rate_limit(self) -> bool:
        """检查是否超过限流"""
        now = time.time()
        
        # 清理过期的请求记录
        self.rate_limit_requests = [
            t for t in self.rate_limit_requests 
            if now - t < self.rate_limit_window
        ]
        
        # 检查是否超过限制
        if len(self.rate_limit_requests) >= self.rate_limit_max:
            logger.debug(f"IP-API.COM限流: {len(self.rate_limit_requests)}/{self.rate_limit_max}")
            return False
        
        return True
    
    def query(self, ip: str) -> Optional[Dict]:
        """查询IP信息"""
        if not self._check_rate_limit():
            return None
        
        self.total_requests += 1
        self.rate_limit_requests.append(time.time())
        
        try:
            url = self.url_template.format(ip=ip)
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            result = self.parse_response(response)
            
            if result:
                self.mark_success()
                return result
            else:
                self.mark_failure()
                return None
        
        except requests.exceptions.Timeout:
            logger.debug(f"IP-API.COM超时: {ip}")
            self.mark_failure()
            return None
        
        except requests.exceptions.RequestException as e:
            logger.debug(f"IP-API.COM请求失败: {ip}, {e}")
            self.mark_failure()
            return None
        
        except Exception as e:
            logger.error(f"IP-API.COM异常: {ip}, {e}")
            self.mark_failure()
            return None
    
    def parse_response(self, response: requests.Response) -> Optional[Dict]:
        """解析IP-API.COM响应"""
        try:
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'country': data.get('countryCode', 'Unknown'),
                    'country_name': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', ''),
                    'source': 'ip_api_com',
                    'confidence': 0.95
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"IP-API.COM响应解析失败: {e}")
            return None


class PConlineAPIProvider(BaseAPIProvider):
    """太平洋API"""
    
    def __init__(self, timeout: int = 3):
        super().__init__('pconline_api', timeout)
        self.url_template = 'http://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true'
    
    def query(self, ip: str) -> Optional[Dict]:
        """查询IP信息"""
        self.total_requests += 1
        
        try:
            url = self.url_template.format(ip=ip)
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            result = self.parse_response(response)
            
            if result:
                self.mark_success()
                return result
            else:
                self.mark_failure()
                return None
        
        except requests.exceptions.Timeout:
            logger.debug(f"太平洋API超时: {ip}")
            self.mark_failure()
            return None
        
        except requests.exceptions.RequestException as e:
            logger.debug(f"太平洋API请求失败: {ip}, {e}")
            self.mark_failure()
            return None
        
        except Exception as e:
            logger.error(f"太平洋API异常: {ip}, {e}")
            self.mark_failure()
            return None
    
    def parse_response(self, response: requests.Response) -> Optional[Dict]:
        """解析太平洋API响应"""
        try:
            # 太平洋API返回的是GBK编码
            response.encoding = 'gbk'
            data = response.json()
            
            if 'pro' in data or 'city' in data:
                province = data.get('pro', '')
                city = data.get('city', '')
                
                # 组合省份和城市
                location = f"{province}{city}".strip()
                if not location:
                    return None
                
                return {
                    'country': 'CN',  # 太平洋API主要返回中国IP信息
                    'country_name': '中国',
                    'city': city or province or 'Unknown',
                    'isp': data.get('addr', ''),
                    'source': 'pconline_api',
                    'confidence': 0.80
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"太平洋API响应解析失败: {e}")
            return None


class APIManager:
    """API管理器 - 管理多个API Provider并实现轮询"""
    
    def __init__(self):
        """初始化API管理器"""
        self.providers: List[tuple] = []  # (provider, priority)
        self.api_status = {}  # API状态缓存
        self.disable_threshold = 3  # 连续失败3次后禁用
        self.disable_duration = 600  # 禁用10分钟
    
    def register_api(self, provider: BaseAPIProvider, priority: int):
        """
        注册API Provider
        
        Args:
            provider: API Provider实例
            priority: 优先级（数字越小优先级越高）
        """
        self.providers.append((provider, priority))
        self.providers.sort(key=lambda x: x[1])  # 按优先级排序
        logger.info(f"注册API: {provider.name}, 优先级: {priority}")
    
    def query(self, ip: str) -> Optional[Dict]:
        """
        轮询查询IP信息
        
        Args:
            ip: IP地址
            
        Returns:
            位置信息字典，失败返回None
        """
        for provider, priority in self.providers:
            # 检查API是否可用
            if not self._is_api_available(provider):
                logger.debug(f"跳过不可用的API: {provider.name}")
                continue
            
            # 尝试查询
            try:
                result = provider.query(ip)
                
                if result:
                    logger.info(f"API查询成功: {provider.name} -> {ip}")
                    self._mark_api_success(provider)
                    return result
                else:
                    logger.debug(f"API查询失败: {provider.name} -> {ip}")
                    self._mark_api_failure(provider)
            
            except Exception as e:
                logger.error(f"API查询异常: {provider.name} -> {ip}, {e}")
                self._mark_api_failure(provider)
        
        # 所有API都失败
        logger.warning(f"所有API查询失败: {ip}")
        return None
    
    def _is_api_available(self, provider: BaseAPIProvider) -> bool:
        """检查API是否可用"""
        # 检查Provider自身状态
        if not provider.is_available():
            return False
        
        # 检查状态缓存
        if provider.name in self.api_status:
            status = self.api_status[provider.name]
            
            # 检查是否在禁用期
            if not status['enabled']:
                if time.time() < status['disabled_until']:
                    return False
                else:
                    # 禁用期结束，重新启用
                    status['enabled'] = True
                    status['failure_count'] = 0
                    logger.info(f"API重新启用: {provider.name}")
        
        return True
    
    def _mark_api_success(self, provider: BaseAPIProvider):
        """标记API成功"""
        if provider.name in self.api_status:
            status = self.api_status[provider.name]
            status['failure_count'] = 0
            status['enabled'] = True
    
    def _mark_api_failure(self, provider: BaseAPIProvider):
        """标记API失败"""
        if provider.name not in self.api_status:
            self.api_status[provider.name] = {
                'enabled': True,
                'failure_count': 0,
                'disabled_until': 0
            }
        
        status = self.api_status[provider.name]
        status['failure_count'] += 1
        
        # 连续失败达到阈值，禁用API
        if status['failure_count'] >= self.disable_threshold:
            status['enabled'] = False
            status['disabled_until'] = time.time() + self.disable_duration
            logger.warning(
                f"API已禁用: {provider.name}, "
                f"将在{self.disable_duration}秒后重新启用"
            )
    
    def get_stats(self) -> Dict:
        """
        获取所有API的统计信息
        
        Returns:
            统计信息字典
        """
        stats = {}
        for provider, priority in self.providers:
            stats[provider.name] = provider.get_stats()
        return stats
    
    def health_check(self):
        """健康检查 - 重置长时间禁用的API"""
        now = time.time()
        
        for provider, _ in self.providers:
            if provider.name in self.api_status:
                status = self.api_status[provider.name]
                
                # 如果禁用时间已过，重新启用
                if not status['enabled'] and now >= status['disabled_until']:
                    status['enabled'] = True
                    status['failure_count'] = 0
                    logger.info(f"健康检查: API重新启用 - {provider.name}")