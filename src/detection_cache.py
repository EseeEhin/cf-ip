"""
检测缓存模块
提供IP检测结果的缓存管理功能
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DetectionCache:
    """检测结果缓存管理器"""
    
    def __init__(self, cache_dir: str = 'cache/ip_detection', enabled: bool = True):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            enabled: 是否启用缓存
        """
        self.enabled = enabled
        self.cache_dir = Path(cache_dir)
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self.memory_cache = {}
        
        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'expired': 0
        }
        
        # 默认TTL（秒）
        self.default_ttl = {
            'cf_ray': 86400,      # CF-RAY: 24小时
            'api': 43200,         # API: 12小时
            'geoip': 604800       # GeoIP: 7天
        }
    
    def get(self, ip: str, port: int = 443, cache_type: str = 'cf_ray') -> Optional[Dict]:
        """
        获取缓存
        
        Args:
            ip: IP地址
            port: 端口号
            cache_type: 缓存类型 ('cf_ray', 'api', 'geoip')
            
        Returns:
            缓存的位置信息，未命中返回None
        """
        if not self.enabled:
            return None
        
        key = self._make_key(ip, port, cache_type)
        
        # 先查内存缓存
        if key in self.memory_cache:
            cached = self.memory_cache[key]
            
            if not self._is_expired(cached):
                self.stats['hits'] += 1
                logger.debug(f"内存缓存命中: {ip}:{port}")
                return cached['data']
            else:
                # 过期，删除
                del self.memory_cache[key]
                self.stats['expired'] += 1
        
        # 再查文件缓存
        cache_file = self._get_cache_file(ip, port, cache_type)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                
                if not self._is_expired(cached):
                    # 加载到内存缓存
                    self.memory_cache[key] = cached
                    self.stats['hits'] += 1
                    logger.debug(f"文件缓存命中: {ip}:{port}")
                    return cached['data']
                else:
                    # 过期，删除文件
                    cache_file.unlink()
                    self.stats['expired'] += 1
            
            except Exception as e:
                logger.debug(f"读取缓存文件失败: {cache_file}, {e}")
        
        self.stats['misses'] += 1
        return None
    
    def set(self, ip: str, data: Dict, port: int = 443, 
            cache_type: str = 'cf_ray', ttl: Optional[int] = None):
        """
        设置缓存
        
        Args:
            ip: IP地址
            data: 位置信息数据
            port: 端口号
            cache_type: 缓存类型 ('cf_ray', 'api', 'geoip')
            ttl: 过期时间（秒），None则使用默认值
        """
        if not self.enabled:
            return
        
        if ttl is None:
            ttl = self.default_ttl.get(cache_type, 3600)
        
        key = self._make_key(ip, port, cache_type)
        
        cached = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl,
            'cache_type': cache_type
        }
        
        # 写入内存缓存
        self.memory_cache[key] = cached
        
        # 写入文件缓存
        try:
            cache_file = self._get_cache_file(ip, port, cache_type)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached, f, ensure_ascii=False, indent=2)
            
            self.stats['sets'] += 1
            logger.debug(f"缓存已保存: {ip}:{port}, TTL: {ttl}秒")
        
        except Exception as e:
            logger.error(f"保存缓存文件失败: {ip}:{port}, {e}")
    
    def clear(self, cache_type: Optional[str] = None):
        """
        清除缓存
        
        Args:
            cache_type: 缓存类型，None则清除所有
        """
        if not self.enabled:
            return
        
        # 清除内存缓存
        if cache_type:
            keys_to_delete = [
                k for k, v in self.memory_cache.items() 
                if v.get('cache_type') == cache_type
            ]
            for key in keys_to_delete:
                del self.memory_cache[key]
        else:
            self.memory_cache.clear()
        
        # 清除文件缓存
        try:
            if cache_type:
                pattern = f"*_{cache_type}.json"
            else:
                pattern = "*.json"
            
            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink()
            
            logger.info(f"缓存已清除: {cache_type or '全部'}")
        
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    def clean_expired(self):
        """清理过期缓存"""
        if not self.enabled:
            return
        
        cleaned_count = 0
        
        # 清理内存缓存
        expired_keys = [
            k for k, v in self.memory_cache.items() 
            if self._is_expired(v)
        ]
        for key in expired_keys:
            del self.memory_cache[key]
            cleaned_count += 1
        
        # 清理文件缓存
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached = json.load(f)
                    
                    if self._is_expired(cached):
                        cache_file.unlink()
                        cleaned_count += 1
                
                except Exception as e:
                    logger.debug(f"清理缓存文件失败: {cache_file}, {e}")
            
            if cleaned_count > 0:
                logger.info(f"清理过期缓存: {cleaned_count} 条")
        
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
    
    def get_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'enabled': self.enabled,
            'memory_cache_size': len(self.memory_cache),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.1f}%",
            'sets': self.stats['sets'],
            'expired': self.stats['expired']
        }
    
    def _make_key(self, ip: str, port: int, cache_type: str) -> str:
        """生成缓存键"""
        return f"{ip}:{port}:{cache_type}"
    
    def _get_cache_file(self, ip: str, port: int, cache_type: str) -> Path:
        """获取缓存文件路径"""
        # 使用IP和端口作为文件名，避免特殊字符
        safe_ip = ip.replace('.', '_').replace(':', '_')
        filename = f"{safe_ip}_{port}_{cache_type}.json"
        return self.cache_dir / filename
    
    def _is_expired(self, cached: Dict) -> bool:
        """检查缓存是否过期"""
        age = time.time() - cached['timestamp']
        return age > cached['ttl']


class FailureCache:
    """失败记录缓存 - 记录检测失败的IP，避免重复尝试"""
    
    def __init__(self, retry_delay: int = 3600):
        """
        初始化失败记录缓存
        
        Args:
            retry_delay: 重试延迟（秒），默认1小时
        """
        self.failures = {}  # {ip: {'count': int, 'last_failure': float, 'retry_after': float}}
        self.retry_delay = retry_delay
        self.max_failures = 3  # 失败3次后才记录
    
    def record_failure(self, ip: str):
        """
        记录失败
        
        Args:
            ip: IP地址
        """
        now = time.time()
        
        if ip not in self.failures:
            self.failures[ip] = {
                'count': 1,
                'last_failure': now,
                'retry_after': now + self.retry_delay
            }
        else:
            self.failures[ip]['count'] += 1
            self.failures[ip]['last_failure'] = now
            self.failures[ip]['retry_after'] = now + self.retry_delay
        
        logger.debug(f"记录失败: {ip}, 失败次数: {self.failures[ip]['count']}")
    
    def should_skip(self, ip: str) -> bool:
        """
        检查是否应该跳过此IP
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否应该跳过
        """
        if ip not in self.failures:
            return False
        
        failure = self.failures[ip]
        
        # 失败次数未达到阈值
        if failure['count'] < self.max_failures:
            return False
        
        # 检查是否到了重试时间
        now = time.time()
        if now >= failure['retry_after']:
            # 重置失败记录，允许重试
            del self.failures[ip]
            logger.debug(f"重试时间到，清除失败记录: {ip}")
            return False
        
        logger.debug(f"跳过失败IP: {ip}, 失败次数: {failure['count']}")
        return True
    
    def clear_failure(self, ip: str):
        """
        清除失败记录（检测成功时调用）
        
        Args:
            ip: IP地址
        """
        if ip in self.failures:
            del self.failures[ip]
            logger.debug(f"清除失败记录: {ip}")
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_failures': len(self.failures),
            'failures': {
                ip: {
                    'count': info['count'],
                    'last_failure': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['last_failure'])),
                    'retry_after': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['retry_after']))
                }
                for ip, info in self.failures.items()
            }
        }


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试DetectionCache
    print("测试DetectionCache:")
    cache = DetectionCache(cache_dir='cache/test_detection')
    
    # 设置缓存
    test_data = {
        'country': 'JP',
        'city': 'Tokyo',
        'source': 'cf_ray'
    }
    cache.set('104.16.132.229', test_data, cache_type='cf_ray')
    
    # 获取缓存
    result = cache.get('104.16.132.229', cache_type='cf_ray')
    print(f"缓存结果: {result}")
    
    # 统计信息
    print(f"缓存统计: {cache.get_stats()}")
    
    # 测试FailureCache
    print("\n测试FailureCache:")
    failure_cache = FailureCache(retry_delay=5)
    
    # 记录失败
    test_ip = '1.2.3.4'
    for i in range(4):
        failure_cache.record_failure(test_ip)
        print(f"失败{i+1}次, 是否跳过: {failure_cache.should_skip(test_ip)}")
    
    # 等待重试时间
    print("等待5秒...")
    time.sleep(5)
    print(f"5秒后是否跳过: {failure_cache.should_skip(test_ip)}")