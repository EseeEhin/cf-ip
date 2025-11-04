"""
IP检测器V2 - 改进版
实现三层检测策略：CF-RAY → 第三方API → GeoIP数据库

API优先级（根据用户反馈优化）：
1. IPInfo.IO Widget - 主要API（速度最快0.71s，CF识别率80%）
2. IP-API.COM - 备用API（用户确认准确）
3. IPWhois - 备用API（稳定可靠）
4. IP2Location - 辅助API
"""

import time
import logging
import ipaddress
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入现有模块
from .cf_ray_detector import get_cloudflare_colo
from .ip_location import GeoIPDatabase

# 导入新模块
from .api_providers import (
    IPInfoProvider,
    IPAPIProvider,
    IPWhoisProvider,
    IP2LocationProvider,
    APIManager
)
from .detection_cache import DetectionCache, FailureCache

logger = logging.getLogger(__name__)

# Cloudflare的主要IP段
CLOUDFLARE_IP_RANGES = [
    '104.16.0.0/12',    # 104.16.0.0 - 104.31.255.255 (合并官方范围)
    '172.64.0.0/13',    # 172.64.0.0 - 172.71.255.255
    '162.159.0.0/16',   # 162.159.0.0 - 162.159.255.255
    '108.162.192.0/18', # 108.162.192.0 - 108.162.255.255
    '198.41.128.0/17',  # 198.41.128.0 - 198.41.255.255
    '173.245.48.0/20',  # 173.245.48.0 - 173.245.63.255
    '188.114.96.0/20',  # 188.114.96.0 - 188.114.111.255
    '190.93.240.0/20',  # 190.93.240.0 - 190.93.255.255
    '197.234.240.0/22', # 197.234.240.0 - 197.234.243.255
    '131.0.72.0/22',    # 131.0.72.0 - 131.0.75.255
]


class IPDetectorV2:
    """IP检测器V2 - 主检测器类"""
    
    def __init__(self, config=None):
        """
        初始化检测器
        
        Args:
            config: 配置对象，None则使用默认配置
        """
        # 加载配置
        if config is None:
            from .config import Config
            config = Config()
        
        self.config = config
        
        # 初始化缓存
        cache_enabled = getattr(config, 'cache_enabled', True)
        self.cache = DetectionCache(enabled=cache_enabled)
        self.failure_cache = FailureCache(
            retry_delay=getattr(config, 'failure_retry_delay', 3600)
        )
        
        # 初始化API管理器
        self.api_manager = self._init_api_manager()
        
        # 初始化GeoIP数据库
        self.geoip_db = GeoIPDatabase()
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'cf_ray_success': 0,
            'api_success': 0,
            'geoip_success': 0,
            'failed': 0,
            'cached': 0,
            'response_times': []
        }
        
        self.start_time = time.time()
        
        logger.info("IPDetectorV2初始化完成")
    
    def _init_api_manager(self) -> APIManager:
        """
        初始化API管理器
        
        按优先级顺序注册API：
        1. IPInfo.IO Widget（主要）- 速度最快，准确度高
        2. IP-API.COM（备用）- 用户确认准确
        3. IPWhois（备用）- 稳定可靠
        4. IP2Location（辅助）- 按需使用
        """
        manager = APIManager()
        
        # 获取API配置
        api_enabled = getattr(self.config, 'api_enabled', True)
        if not api_enabled:
            logger.info("第三方API已禁用")
            return manager
        
        api_timeout = getattr(self.config, 'api_timeout', 5)
        
        # 注册IPInfo.IO（备用API - 优先级2，因为对CF IP不准确）
        if getattr(self.config, 'api_ipinfo_enabled', True):
            ipinfo = IPInfoProvider(timeout=api_timeout)
            priority = getattr(self.config, 'api_ipinfo_priority', 2)
            manager.register_api(ipinfo, priority)
            logger.info(f"已注册IPInfo.IO API（优先级: {priority}）")
        
        # 注册IP-API.COM（主要API - 优先级1，对CF IP更准确）
        if getattr(self.config, 'api_ipapi_enabled', True):
            ipapi = IPAPIProvider(timeout=api_timeout)
            priority = getattr(self.config, 'api_ipapi_priority', 1)
            manager.register_api(ipapi, priority)
            logger.info(f"已注册IP-API.COM（优先级: {priority}）")
        
        # 注册IPWhois（备用API - 优先级3）
        if getattr(self.config, 'api_ipwhois_enabled', True):
            ipwhois = IPWhoisProvider(timeout=api_timeout)
            priority = getattr(self.config, 'api_ipwhois_priority', 3)
            manager.register_api(ipwhois, priority)
            logger.info(f"已注册IPWhois API（优先级: {priority}）")
        
        # 注册IP2Location（辅助API - 优先级4）
        if getattr(self.config, 'api_ip2location_enabled', False):
            ip2location = IP2LocationProvider(timeout=api_timeout)
            priority = getattr(self.config, 'api_ip2location_priority', 4)
            manager.register_api(ip2location, priority)
            logger.info(f"已注册IP2Location API（优先级: {priority}）")
        
        return manager
    
    def is_cloudflare_ip(self, ip: str) -> bool:
        """
        判断IP是否属于Cloudflare
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否为Cloudflare IP
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            for range_str in CLOUDFLARE_IP_RANGES:
                if ip_obj in ipaddress.ip_network(range_str):
                    return True
            return False
        except Exception as e:
            logger.debug(f"判断Cloudflare IP失败: {ip}, {e}")
            return False
    
    def detect(self, ip: str, port: int = 443) -> Optional[Dict]:
        """
        检测单个IP的位置信息
        
        Args:
            ip: IP地址
            port: 端口号，默认443
            
        Returns:
            位置信息字典，失败返回None
        """
        start_time = time.time()
        self.stats['total'] += 1
        
        try:
            # 第0层：检查缓存
            cached = self.cache.get(ip, port)
            if cached:
                self.stats['cached'] += 1
                self.stats['success'] += 1
                logger.debug(f"缓存命中: {ip}:{port}")
                return cached
            
            # 检查失败记录
            if self.failure_cache.should_skip(ip):
                logger.debug(f"跳过失败IP: {ip}")
                self.stats['failed'] += 1
                return None
            
            # 判断是否为Cloudflare IP
            is_cf = self.is_cloudflare_ip(ip)
            
            if is_cf:
                # Cloudflare IP：必须优先使用CF-RAY检测
                logger.info(f"检测到Cloudflare IP: {ip}，优先使用CF-RAY检测")
                result = self._try_cf_ray(ip, port)
                if result:
                    response_time = time.time() - start_time
                    self._cache_and_record(ip, port, result, 'cf_ray', response_time)
                    return result
                
                # CF-RAY失败，记录警告
                logger.warning(f"CF-RAY检测失败: {ip}:{port}，尝试备用方法")
                
                # 尝试GeoIP数据库（优先，因为可能比第三方API准确）
                result = self._try_geoip(ip)
                if result:
                    response_time = time.time() - start_time
                    logger.warning(f"使用GeoIP检测CF IP: {ip} -> {result['city']}, {result['country']}（可能不准确）")
                    self._cache_and_record(ip, port, result, 'geoip', response_time)
                    return result
                
                # GeoIP也失败，最后尝试第三方API（会返回旧金山，但总比没有好）
                result = self._try_api(ip)
                if result:
                    response_time = time.time() - start_time
                    logger.warning(f"使用第三方API检测CF IP: {ip}，结果可能不准确（可能显示旧金山） -> {result['city']}, {result['country']}")
                    self._cache_and_record(ip, port, result, 'api', response_time)
                    return result
            else:
                # 非Cloudflare IP：先尝试第三方API
                result = self._try_api(ip)
                if result:
                    response_time = time.time() - start_time
                    self._cache_and_record(ip, port, result, 'api', response_time)
                    return result
                
                # API失败，尝试CF-RAY（可能是未知的CF IP段）
                result = self._try_cf_ray(ip, port)
                if result:
                    response_time = time.time() - start_time
                    logger.info(f"非CF IP段但CF-RAY检测成功: {ip}:{port}")
                    self._cache_and_record(ip, port, result, 'cf_ray', response_time)
                    return result
            
            # 第三层：GeoIP数据库
            result = self._try_geoip(ip)
            if result:
                response_time = time.time() - start_time
                self._cache_and_record(ip, port, result, 'geoip', response_time)
                return result
            
            # 所有方法都失败
            self.failure_cache.record_failure(ip)
            self.stats['failed'] += 1
            logger.warning(f"所有检测方法都失败: {ip}:{port}")
            return None
        
        except Exception as e:
            logger.error(f"检测异常: {ip}:{port}, {e}")
            self.stats['failed'] += 1
            return None
    
    def detect_batch(self, ip_list: List[str], port: int = 443, 
                     max_workers: Optional[int] = None) -> Dict[str, Optional[Dict]]:
        """
        批量检测IP位置信息
        
        Args:
            ip_list: IP地址列表
            port: 端口号，默认443
            max_workers: 最大并发数，None则使用配置值
            
        Returns:
            IP到位置信息的映射字典
        """
        if max_workers is None:
            max_workers = getattr(self.config, 'detection_max_workers', 10)
        
        results = {}
        total = len(ip_list)
        
        logger.info(f"开始批量检测: {total} 个IP, 并发数: {max_workers}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_ip = {
                executor.submit(self.detect, ip, port): ip
                for ip in ip_list
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                
                try:
                    result = future.result()
                    results[ip] = result
                    completed += 1
                    
                    # 每10个IP报告一次进度
                    if completed % 10 == 0 or completed == total:
                        logger.info(f"检测进度: {completed}/{total}")
                
                except Exception as e:
                    logger.error(f"检测异常: {ip}, {e}")
                    results[ip] = None
        
        # 输出统计摘要
        logger.info(self.get_summary())
        
        return results
    
    def _try_cf_ray(self, ip: str, port: int) -> Optional[Dict]:
        """尝试CF-RAY检测"""
        cf_ray_enabled = getattr(self.config, 'cf_ray_detection_enabled', True)
        if not cf_ray_enabled:
            return None
        
        try:
            timeout = getattr(self.config, 'cf_ray_timeout', 5)
            result = get_cloudflare_colo(ip, port, timeout)
            
            if result.get('success'):
                self.stats['cf_ray_success'] += 1
                logger.info(
                    f"CF-RAY检测成功: {ip}:{port} -> "
                    f"{result['colo']} ({result['city']}, {result['country']})"
                )
                
                return {
                    'country': result['country'],
                    'country_name': result['country'],
                    'city': result['city'],
                    'ip': ip,
                    'source': 'cf_ray',
                    'colo': result['colo']
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"CF-RAY检测失败: {ip}:{port}, {e}")
            return None
    
    def _try_api(self, ip: str) -> Optional[Dict]:
        """尝试第三方API检测"""
        try:
            result = self.api_manager.query(ip)
            
            if result:
                self.stats['api_success'] += 1
                logger.info(
                    f"API检测成功: {ip} -> "
                    f"{result['city']}, {result['country']} "
                    f"(来源: {result['source']})"
                )
                
                # 添加IP字段
                result['ip'] = ip
                return result
            
            return None
        
        except Exception as e:
            logger.debug(f"API检测失败: {ip}, {e}")
            return None
    
    def _try_geoip(self, ip: str) -> Optional[Dict]:
        """尝试GeoIP数据库检测"""
        try:
            result = self.geoip_db.query(ip)
            
            if result:
                self.stats['geoip_success'] += 1
                logger.info(
                    f"GeoIP检测成功: {ip} -> "
                    f"{result['city']}, {result['country']}"
                )
                return result
            
            return None
        
        except Exception as e:
            logger.debug(f"GeoIP检测失败: {ip}, {e}")
            return None
    
    def _cache_and_record(self, ip: str, port: int, result: Dict, 
                          cache_type: str, response_time: float):
        """缓存结果并记录统计"""
        # 缓存结果
        self.cache.set(ip, result, port, cache_type)
        
        # 清除失败记录
        self.failure_cache.clear_failure(ip)
        
        # 记录统计
        self.stats['success'] += 1
        self.stats['response_times'].append(response_time)
    
    def get_summary(self) -> str:
        """
        获取统计摘要
        
        Returns:
            统计摘要字符串
        """
        total = self.stats['total']
        if total == 0:
            return "暂无统计数据"
        
        success_rate = (self.stats['success'] / total) * 100
        avg_response_time = (
            sum(self.stats['response_times']) / len(self.stats['response_times'])
            if self.stats['response_times'] else 0
        )
        elapsed_time = time.time() - self.start_time
        
        summary = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
检测统计摘要:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总检测数: {total}
成功数: {self.stats['success']} ({success_rate:.1f}%)
失败数: {self.stats['failed']}
缓存命中: {self.stats['cached']}

检测来源分布:
  - CF-RAY: {self.stats['cf_ray_success']} ({self.stats['cf_ray_success']/total*100:.1f}%)
  - 第三方API: {self.stats['api_success']} ({self.stats['api_success']/total*100:.1f}%)
  - GeoIP库: {self.stats['geoip_success']} ({self.stats['geoip_success']/total*100:.1f}%)

性能指标:
  - 平均响应时间: {avg_response_time:.2f}秒
  - 总耗时: {elapsed_time:.2f}秒
  - 检测速率: {total/elapsed_time:.2f} IP/秒

缓存统计:
"""
        
        # 添加缓存统计
        cache_stats = self.cache.get_stats()
        summary += f"  - 缓存命中率: {cache_stats['hit_rate']}\n"
        summary += f"  - 内存缓存大小: {cache_stats['memory_cache_size']}\n"
        
        # 添加API统计
        api_stats = self.api_manager.get_stats()
        if api_stats:
            summary += "\nAPI统计:\n"
            for api_name, stats in api_stats.items():
                summary += f"  - {api_name}: {stats['successful_requests']}/{stats['total_requests']} ({stats['success_rate']})\n"
        
        summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return summary
    
    def get_stats(self) -> Dict:
        """
        获取详细统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'detection': self.stats,
            'cache': self.cache.get_stats(),
            'api': self.api_manager.get_stats(),
            'failure': self.failure_cache.get_stats()
        }
    
    def close(self):
        """关闭检测器，释放资源"""
        if self.geoip_db:
            self.geoip_db.close()
        logger.info("IPDetectorV2已关闭")


# 便捷函数
_detector = None


def get_detector(config=None) -> IPDetectorV2:
    """
    获取全局检测器实例
    
    Args:
        config: 配置对象
        
    Returns:
        IPDetectorV2实例
    """
    global _detector
    
    if _detector is None:
        _detector = IPDetectorV2(config)
    
    return _detector


def detect_ip_location(ip: str, port: int = 443) -> Optional[Dict]:
    """
    检测IP位置（便捷函数）
    
    Args:
        ip: IP地址
        port: 端口号
        
    Returns:
        位置信息字典
    """
    detector = get_detector()
    return detector.detect(ip, port)


def detect_ip_locations_batch(ip_list: List[str], port: int = 443) -> Dict[str, Optional[Dict]]:
    """
    批量检测IP位置（便捷函数）
    
    Args:
        ip_list: IP地址列表
        port: 端口号
        
    Returns:
        IP到位置信息的映射
    """
    detector = get_detector()
    return detector.detect_batch(ip_list, port)


def close_detector():
    """关闭全局检测器"""
    global _detector
    
    if _detector is not None:
        _detector.close()
        _detector = None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试单个IP
    print("测试单个IP检测:")
    test_ips = [
        '172.64.229.95',   # Cloudflare IP
        '104.16.132.229',  # Cloudflare IP
        '8.8.8.8',         # Google DNS
    ]
    
    detector = IPDetectorV2()
    
    for ip in test_ips:
        result = detector.detect(ip)
        if result:
            print(f"{ip} -> {result['country']}-{result['city']} (来源: {result['source']})")
        else:
            print(f"{ip} -> 检测失败")
    
    # 测试批量检测
    print("\n测试批量检测:")
    batch_results = detector.detect_batch(test_ips)
    
    for ip, location in batch_results.items():
        if location:
            print(f"{ip} -> {location['country']}-{location['city']} (来源: {location['source']})")
        else:
            print(f"{ip} -> 检测失败")
    
    # 输出统计
    print(detector.get_summary())
    
    # 关闭检测器
    detector.close()