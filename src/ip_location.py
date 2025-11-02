"""
IP地理位置查询模块
支持多个API源和本地缓存
"""

import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class RateLimiter:
    """API速率限制器"""
    
    def __init__(self, max_requests: int = 40, time_window: int = 60):
        """
        初始化速率限制器
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        """如果达到速率限制，等待直到可以继续"""
        now = time.time()
        
        # 移除时间窗口外的请求记录
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # 如果达到限制，等待
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 1
            if sleep_time > 0:
                logger.warning(f"达到API速率限制，等待 {sleep_time:.1f} 秒...")
                time.sleep(sleep_time)
                self.requests.clear()
        
        # 记录本次请求
        self.requests.append(time.time())


class IPLocationCache:
    """IP地理位置缓存管理器"""
    
    def __init__(self, cache_file: str = 'cache/ip_location_cache.json', cache_days: int = 30):
        """
        初始化缓存管理器
        
        Args:
            cache_file: 缓存文件路径
            cache_days: 缓存有效期（天）
        """
        self.cache_file = Path(cache_file)
        self.cache_days = cache_days
        self.cache = self._load_cache()
        
        # 确保缓存目录存在
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_cache(self) -> Dict:
        """加载缓存文件"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    logger.info(f"加载缓存文件成功，包含 {len(cache_data.get('ips', {}))} 个IP记录")
                    return cache_data
        except Exception as e:
            logger.warning(f"加载缓存文件失败: {e}")
        
        return {
            'cache_version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'ips': {}
        }
    
    def save_cache(self):
        """保存缓存到文件"""
        try:
            self.cache['last_updated'] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"缓存已保存，共 {len(self.cache['ips'])} 个IP记录")
        except Exception as e:
            logger.error(f"保存缓存文件失败: {e}")
    
    def get(self, ip: str) -> Optional[Dict]:
        """
        从缓存获取IP的地理位置
        
        Args:
            ip: IP地址
            
        Returns:
            地理位置信息，如果缓存未命中或已过期则返回None
        """
        if ip not in self.cache['ips']:
            return None
        
        cached_data = self.cache['ips'][ip]
        
        try:
            cached_time = datetime.fromisoformat(cached_data['cached_at'])
            
            # 检查是否过期
            if datetime.now() - cached_time > timedelta(days=self.cache_days):
                logger.debug(f"IP {ip} 的缓存已过期")
                return None
            
            logger.debug(f"缓存命中: {ip} -> {cached_data['country']}-{cached_data['city']}")
            return cached_data
        except Exception as e:
            logger.warning(f"解析缓存数据失败: {e}")
            return None
    
    def set(self, ip: str, location_data: Dict):
        """
        设置IP的地理位置到缓存
        
        Args:
            ip: IP地址
            location_data: 地理位置信息
        """
        self.cache['ips'][ip] = {
            **location_data,
            'cached_at': datetime.now().isoformat(),
            'query_count': self.cache['ips'].get(ip, {}).get('query_count', 0) + 1
        }
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存
        
        Returns:
            清理的记录数
        """
        now = datetime.now()
        expired_ips = []
        
        for ip, data in self.cache['ips'].items():
            try:
                cached_time = datetime.fromisoformat(data['cached_at'])
                if now - cached_time > timedelta(days=self.cache_days):
                    expired_ips.append(ip)
            except:
                expired_ips.append(ip)  # 无效的缓存数据也删除
        
        for ip in expired_ips:
            del self.cache['ips'][ip]
        
        if expired_ips:
            self.save_cache()
            logger.info(f"清理了 {len(expired_ips)} 个过期缓存记录")
        
        return len(expired_ips)
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'total_ips': len(self.cache['ips']),
            'last_updated': self.cache.get('last_updated', 'Unknown'),
            'cache_file': str(self.cache_file),
            'cache_days': self.cache_days
        }


class IPLocationQuery:
    """IP地理位置查询器（支持多个API源）"""
    
    # 多个免费API源
    API_SOURCES = [
        {
            'name': 'ip-api.com',
            'url': 'http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,query',
            'rate_limit': 45,  # 每分钟45次
            'parse': lambda data: {
                'country': data.get('countryCode', 'Unknown'),
                'country_name': data.get('country', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'ip': data.get('query', '')
            } if data.get('status') == 'success' else None
        },
        {
            'name': 'ipapi.co',
            'url': 'https://ipapi.co/{ip}/json/',
            'rate_limit': 30,  # 每分钟30次（保守估计）
            'parse': lambda data: {
                'country': data.get('country_code', 'Unknown'),
                'country_name': data.get('country_name', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'ip': data.get('ip', '')
            } if 'error' not in data else None
        }
    ]
    
    def __init__(self, cache: IPLocationCache, timeout: int = 10):
        """
        初始化查询器
        
        Args:
            cache: 缓存管理器
            timeout: 请求超时时间（秒）
        """
        self.cache = cache
        self.timeout = timeout
        self.rate_limiters = {
            source['name']: RateLimiter(max_requests=source['rate_limit'] - 5)
            for source in self.API_SOURCES
        }
        self.current_source_index = 0
    
    def _query_api(self, ip: str, source: Dict) -> Optional[Dict]:
        """
        查询单个API源
        
        Args:
            ip: IP地址
            source: API源配置
            
        Returns:
            地理位置信息，失败返回None
        """
        try:
            # 速率限制
            rate_limiter = self.rate_limiters[source['name']]
            rate_limiter.wait_if_needed()
            
            # 发送请求
            url = source['url'].format(ip=ip)
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            location = source['parse'](data)
            
            if location:
                logger.info(f"[{source['name']}] 查询成功: {ip} -> {location['country']}-{location['city']}")
                return location
            else:
                logger.warning(f"[{source['name']}] 查询失败: {ip}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"[{source['name']}] 请求超时: {ip}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"[{source['name']}] 请求失败: {ip}, 错误: {e}")
        except Exception as e:
            logger.error(f"[{source['name']}] 查询异常: {ip}, 错误: {e}")
        
        return None
    
    def query(self, ip: str) -> Dict:
        """
        查询IP的地理位置（带缓存和多源轮询）
        
        Args:
            ip: IP地址
            
        Returns:
            地理位置信息
        """
        # 1. 尝试从缓存获取
        cached = self.cache.get(ip)
        if cached:
            return cached
        
        # 2. 缓存未命中，查询API（尝试所有源）
        for i in range(len(self.API_SOURCES)):
            source_index = (self.current_source_index + i) % len(self.API_SOURCES)
            source = self.API_SOURCES[source_index]
            
            location = self._query_api(ip, source)
            if location:
                # 查询成功，更新缓存
                self.cache.set(ip, location)
                self.current_source_index = source_index  # 记住成功的源
                return location
        
        # 3. 所有源都失败，返回默认值
        logger.error(f"所有API源查询失败: {ip}")
        default_location = {
            'country': 'Unknown',
            'country_name': 'Unknown',
            'city': 'Unknown',
            'ip': ip
        }
        self.cache.set(ip, default_location)
        return default_location
    
    def query_batch(self, ips: List[str], save_interval: int = 10) -> Dict[str, Dict]:
        """
        批量查询IP地理位置
        
        Args:
            ips: IP地址列表
            save_interval: 每查询多少个IP保存一次缓存
            
        Returns:
            IP到地理位置的映射
        """
        results = {}
        
        for i, ip in enumerate(ips, 1):
            results[ip] = self.query(ip)
            
            # 定期保存缓存
            if i % save_interval == 0:
                self.cache.save_cache()
                logger.info(f"批量查询进度: {i}/{len(ips)}")
        
        # 最后保存一次
        self.cache.save_cache()
        logger.info(f"批量查询完成: {len(ips)} 个IP")
        
        return results


# 全局实例
_cache = None
_query = None


def get_ip_location(ip: str, use_cache: bool = True) -> Dict:
    """
    获取IP的地理位置（便捷函数）
    
    Args:
        ip: IP地址
        use_cache: 是否使用缓存
        
    Returns:
        地理位置信息
    """
    global _cache, _query
    
    if _cache is None:
        _cache = IPLocationCache()
    
    if _query is None:
        _query = IPLocationQuery(_cache)
    
    if not use_cache:
        # 不使用缓存，直接查询
        for source in IPLocationQuery.API_SOURCES:
            location = _query._query_api(ip, source)
            if location:
                return location
        return {
            'country': 'Unknown',
            'country_name': 'Unknown',
            'city': 'Unknown',
            'ip': ip
        }
    
    return _query.query(ip)


def get_ip_locations_batch(ips: List[str]) -> Dict[str, Dict]:
    """
    批量获取IP的地理位置（便捷函数）
    
    Args:
        ips: IP地址列表
        
    Returns:
        IP到地理位置的映射
    """
    global _cache, _query
    
    if _cache is None:
        _cache = IPLocationCache()
    
    if _query is None:
        _query = IPLocationQuery(_cache)
    
    return _query.query_batch(ips)


def cleanup_cache():
    """清理过期缓存（便捷函数）"""
    global _cache
    
    if _cache is None:
        _cache = IPLocationCache()
    
    return _cache.cleanup_expired()


def get_cache_stats() -> Dict:
    """获取缓存统计信息（便捷函数）"""
    global _cache
    
    if _cache is None:
        _cache = IPLocationCache()
    
    return _cache.get_stats()


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试单个IP查询
    test_ips = [
        '172.64.229.95',
        '162.159.45.47',
        '108.162.198.110'
    ]
    
    print("测试IP地理位置查询:")
    for ip in test_ips:
        location = get_ip_location(ip)
        print(f"{ip} -> {location['country']}-{location['city']}")
    
    # 显示缓存统计
    stats = get_cache_stats()
    print(f"\n缓存统计: {stats}")