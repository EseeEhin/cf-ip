"""
IP地理位置查询模块
使用本地GeoIP数据库（MaxMind GeoLite2）进行查询
"""

import json
import logging
import gzip
import shutil
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import ipaddress

logger = logging.getLogger(__name__)


class GeoIPDatabase:
    """本地GeoIP数据库管理器"""
    
    # 使用免费的GeoLite2数据库镜像
    DB_URLS = {
        'country': 'https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb',
        'city': 'https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb'
    }
    
    def __init__(self, db_dir: str = 'cache/geoip'):
        """
        初始化GeoIP数据库管理器
        
        Args:
            db_dir: 数据库文件目录
        """
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        self.country_db_path = self.db_dir / 'GeoLite2-Country.mmdb'
        self.city_db_path = self.db_dir / 'GeoLite2-City.mmdb'
        
        self.reader_country = None
        self.reader_city = None
        
        # 尝试加载数据库
        self._load_databases()
    
    def _load_databases(self):
        """加载GeoIP数据库"""
        try:
            import geoip2.database
            
            # 加载国家数据库
            if self.country_db_path.exists():
                try:
                    self.reader_country = geoip2.database.Reader(str(self.country_db_path))
                    logger.info(f"成功加载国家数据库: {self.country_db_path}")
                except Exception as e:
                    logger.warning(f"加载国家数据库失败: {e}")
            
            # 加载城市数据库
            if self.city_db_path.exists():
                try:
                    self.reader_city = geoip2.database.Reader(str(self.city_db_path))
                    logger.info(f"成功加载城市数据库: {self.city_db_path}")
                except Exception as e:
                    logger.warning(f"加载城市数据库失败: {e}")
                    
        except ImportError:
            logger.error("未安装 geoip2 库，请运行: pip install geoip2")
    
    def download_database(self, db_type: str = 'city') -> bool:
        """
        下载GeoIP数据库
        
        Args:
            db_type: 数据库类型 ('country' 或 'city')
            
        Returns:
            bool: 是否下载成功
        """
        if db_type not in self.DB_URLS:
            logger.error(f"不支持的数据库类型: {db_type}")
            return False
        
        url = self.DB_URLS[db_type]
        db_path = self.country_db_path if db_type == 'country' else self.city_db_path
        
        try:
            logger.info(f"正在下载 {db_type} 数据库: {url}")
            
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # 保存到临时文件
            temp_path = db_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 移动到最终位置
            shutil.move(str(temp_path), str(db_path))
            
            logger.info(f"成功下载 {db_type} 数据库到: {db_path}")
            
            # 重新加载数据库
            self._load_databases()
            
            return True
            
        except Exception as e:
            logger.error(f"下载 {db_type} 数据库失败: {e}")
            return False
    
    def ensure_databases(self) -> bool:
        """
        确保数据库文件存在，如果不存在则下载
        
        Returns:
            bool: 数据库是否可用
        """
        # 检查城市数据库（优先）
        if not self.city_db_path.exists():
            logger.info("城市数据库不存在，开始下载...")
            if not self.download_database('city'):
                logger.warning("城市数据库下载失败，尝试下载国家数据库...")
                if not self.download_database('country'):
                    logger.error("所有数据库下载失败")
                    return False
        
        # 检查国家数据库（备用）
        if not self.country_db_path.exists():
            logger.info("国家数据库不存在，开始下载...")
            self.download_database('country')
        
        return self.reader_city is not None or self.reader_country is not None
    
    def _is_cloudflare_ip(self, ip: str) -> bool:
        """
        检查是否为Cloudflare IP段
        Cloudflare使用Anycast，这些IP在全球多个位置都有
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Cloudflare的主要IP段
            cloudflare_ranges = [
                '173.245.48.0/20',
                '103.21.244.0/22',
                '103.22.200.0/22',
                '103.31.4.0/22',
                '141.101.64.0/18',
                '108.162.192.0/18',
                '190.93.240.0/20',
                '188.114.96.0/20',
                '197.234.240.0/22',
                '198.41.128.0/17',
                '162.158.0.0/15',
                '104.16.0.0/13',
                '104.24.0.0/14',
                '172.64.0.0/13',
                '131.0.72.0/22',
            ]
            
            for cidr in cloudflare_ranges:
                if ip_obj in ipaddress.ip_network(cidr):
                    return True
            
            return False
        except:
            return False
    
    def query(self, ip: str) -> Optional[Dict]:
        """
        查询IP的地理位置
        
        Args:
            ip: IP地址
            
        Returns:
            地理位置信息，失败返回None
        """
        try:
            # 验证IP地址
            ipaddress.ip_address(ip)
            
            # 检查是否为Cloudflare IP
            # Cloudflare使用Anycast，地理位置数据库通常无法准确定位
            # 我们标记为CF（Cloudflare）而不是具体国家
            if self._is_cloudflare_ip(ip):
                logger.debug(f"检测到Cloudflare IP: {ip}")
                return {
                    'country': 'CF',
                    'country_name': 'Cloudflare',
                    'city': 'Anycast',
                    'ip': ip,
                    'source': 'Cloudflare-Detection'
                }
            
            # 优先使用城市数据库
            if self.reader_city:
                try:
                    response = self.reader_city.city(ip)
                    country_code = response.country.iso_code
                    country_name = response.country.name
                    city_name = response.city.name
                    
                    # 如果有有效数据则返回
                    if country_code:
                        return {
                            'country': country_code,
                            'country_name': country_name or 'Unknown',
                            'city': city_name or 'Unknown',
                            'ip': ip,
                            'source': 'GeoLite2-City'
                        }
                except Exception as e:
                    logger.debug(f"城市数据库查询失败: {ip}, {e}")
            
            # 备用：使用国家数据库
            if self.reader_country:
                try:
                    response = self.reader_country.country(ip)
                    country_code = response.country.iso_code
                    country_name = response.country.name
                    
                    if country_code:
                        return {
                            'country': country_code,
                            'country_name': country_name or 'Unknown',
                            'city': 'Unknown',
                            'ip': ip,
                            'source': 'GeoLite2-Country'
                        }
                except Exception as e:
                    logger.debug(f"国家数据库查询失败: {ip}, {e}")
            
            logger.warning(f"无可用数据库查询IP: {ip}")
            return None
            
        except ValueError:
            logger.error(f"无效的IP地址: {ip}")
            return None
        except Exception as e:
            logger.error(f"查询IP地理位置失败: {ip}, {e}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        if self.reader_city:
            self.reader_city.close()
        if self.reader_country:
            self.reader_country.close()


class IPLocationQuery:
    """IP地理位置查询器（使用本地数据库）"""
    
    def __init__(self, db_dir: str = 'cache/geoip'):
        """
        初始化查询器
        
        Args:
            db_dir: 数据库文件目录
        """
        self.geoip_db = GeoIPDatabase(db_dir)
        
        # 确保数据库可用
        if not self.geoip_db.ensure_databases():
            logger.warning("GeoIP数据库不可用，将返回Unknown")
    
    def query(self, ip: str) -> Dict:
        """
        查询IP的地理位置
        
        Args:
            ip: IP地址
            
        Returns:
            地理位置信息
        """
        result = self.geoip_db.query(ip)
        
        if result:
            logger.debug(f"查询成功: {ip} -> {result['country']}-{result['city']}")
            return result
        
        # 查询失败，返回默认值
        logger.warning(f"查询失败，返回默认值: {ip}")
        return {
            'country': 'Unknown',
            'country_name': 'Unknown',
            'city': 'Unknown',
            'ip': ip,
            'source': 'fallback'
        }
    
    def query_batch(self, ips: List[str]) -> Dict[str, Dict]:
        """
        批量查询IP地理位置
        
        Args:
            ips: IP地址列表
            
        Returns:
            IP到地理位置的映射
        """
        results = {}
        
        for i, ip in enumerate(ips, 1):
            results[ip] = self.query(ip)
            
            if i % 100 == 0:
                logger.info(f"批量查询进度: {i}/{len(ips)}")
        
        logger.info(f"批量查询完成: {len(ips)} 个IP")
        return results
    
    def close(self):
        """关闭数据库连接"""
        self.geoip_db.close()


# 全局实例
_query = None


def get_ip_location(ip: str) -> Dict:
    """
    获取IP的地理位置（便捷函数）
    
    Args:
        ip: IP地址
        
    Returns:
        地理位置信息
    """
    global _query
    
    if _query is None:
        _query = IPLocationQuery()
    
    return _query.query(ip)


def get_ip_locations_batch(ips: List[str]) -> Dict[str, Dict]:
    """
    批量获取IP的地理位置（便捷函数）
    
    Args:
        ips: IP地址列表
        
    Returns:
        IP到地理位置的映射
    """
    global _query
    
    if _query is None:
        _query = IPLocationQuery()
    
    return _query.query_batch(ips)


def download_geoip_database(db_type: str = 'city') -> bool:
    """
    下载GeoIP数据库（便捷函数）
    
    Args:
        db_type: 数据库类型 ('country' 或 'city')
        
    Returns:
        bool: 是否下载成功
    """
    db = GeoIPDatabase()
    return db.download_database(db_type)


def close_database():
    """关闭数据库连接（便捷函数）"""
    global _query
    
    if _query is not None:
        _query.close()
        _query = None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试单个IP查询
    test_ips = [
        '172.64.229.95',  # Cloudflare IP
        '162.159.45.47',  # Cloudflare IP
        '108.162.198.110',  # Cloudflare IP
        '8.8.8.8',  # Google DNS (US)
        '1.1.1.1',  # Cloudflare DNS
    ]
    
    print("测试IP地理位置查询:")
    for ip in test_ips:
        location = get_ip_location(ip)
        print(f"{ip} -> {location['country']}-{location['city']} (来源: {location.get('source', 'unknown')})")
    
    # 关闭数据库
    close_database()