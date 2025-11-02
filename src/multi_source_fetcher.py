"""
多数据源IP获取模块
支持从多个来源获取优选IP并统一格式
"""

import logging
import re
import requests
from typing import List, Dict, Optional
from .ip_location import get_ip_locations_batch

logger = logging.getLogger(__name__)


class DataSource:
    """数据源基类"""
    
    def __init__(self, name: str, prefix: str):
        """
        初始化数据源
        
        Args:
            name: 数据源名称
            prefix: 节点名称前缀
        """
        self.name = name
        self.prefix = prefix
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch(self, **kwargs) -> List[Dict]:
        """
        获取IP数据（子类实现）
        
        Returns:
            List[Dict]: 节点列表
        """
        raise NotImplementedError


class SourceA(DataSource):
    """来源A: cfip.wxgqlfx.fun API"""
    
    def __init__(self):
        super().__init__("来源A", "A")
        self.api_query_url = 'https://cfip.wxgqlfx.fun/api/query'
    
    def fetch(self, countries: List[str] = None, limit: int = 10, **kwargs) -> List[Dict]:
        """
        从API获取IP数据
        
        Args:
            countries: 国家代码列表
            limit: 每个国家的数量限制
            
        Returns:
            List[Dict]: 节点列表
        """
        if countries is None:
            countries = ['JP', 'HK', 'US']
        
        all_nodes = []
        
        for country_code in countries:
            try:
                logger.info(f"[{self.name}] 正在查询国家: {country_code}, 限制: {limit}")
                
                payload = {
                    'country': country_code,
                    'port': '',
                    'limit': limit
                }
                
                response = self.session.post(
                    self.api_query_url,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                proxies = data.get('proxies', [])
                
                logger.info(f"[{self.name}] {country_code} 获取到 {len(proxies)} 个节点")
                
                # 转换为统一格式
                for proxy in proxies:
                    node = {
                        'ip': proxy.get('ip', ''),
                        'port': str(proxy.get('port', '')),
                        'country': proxy.get('country', country_code),
                        'city': proxy.get('city', 'Unknown'),
                        'source': self.prefix
                    }
                    all_nodes.append(node)
                    
            except Exception as e:
                logger.error(f"[{self.name}] 查询 {country_code} 失败: {e}")
        
        logger.info(f"[{self.name}] 共获取 {len(all_nodes)} 个节点")
        return all_nodes


class SourceB(DataSource):
    """来源B: qwer-search/bestip"""
    
    def __init__(self):
        super().__init__("来源B", "B")
        self.url = 'https://raw.githubusercontent.com/qwer-search/bestip/refs/heads/main/kejilandbestip.txt'
    
    def fetch(self, **kwargs) -> List[Dict]:
        """
        从txt文件获取IP数据
        
        Returns:
            List[Dict]: 节点列表
        """
        try:
            logger.info(f"[{self.name}] 正在获取数据: {self.url}")
            
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            content = response.text
            lines = content.strip().split('\n')
            
            logger.info(f"[{self.name}] 获取到 {len(lines)} 行数据")
            
            # 解析IP和端口
            nodes = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 尝试解析 IP:端口 格式
                node = self._parse_line(line)
                if node:
                    nodes.append(node)
            
            logger.info(f"[{self.name}] 解析出 {len(nodes)} 个有效节点")
            
            # 批量查询地理位置
            if nodes:
                nodes = self._add_locations(nodes)
            
            return nodes
            
        except Exception as e:
            logger.error(f"[{self.name}] 获取数据失败: {e}")
            return []
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """解析单行数据"""
        # 匹配 IP:端口 或 纯IP
        match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::(\d+))?', line)
        if match:
            ip = match.group(1)
            port = match.group(2) or '443'  # 默认端口443
            
            return {
                'ip': ip,
                'port': port,
                'source': self.prefix
            }
        return None
    
    def _add_locations(self, nodes: List[Dict]) -> List[Dict]:
        """批量添加地理位置信息（支持CF-RAY检测）"""
        try:
            logger.info(f"[{self.name}] 正在查询 {len(nodes)} 个IP的地理位置...")
            
            # 导入get_ip_location以支持端口参数
            from .ip_location import get_ip_location
            
            # 逐个查询（因为需要传递端口信息）
            for node in nodes:
                ip = node['ip']
                port = int(node.get('port', 443))
                
                try:
                    location = get_ip_location(ip, port)
                    node['country'] = location.get('country', 'Unknown')
                    node['city'] = location.get('city', 'Unknown')
                except Exception as e:
                    logger.debug(f"查询 {ip}:{port} 位置失败: {e}")
                    node['country'] = 'Unknown'
                    node['city'] = 'Unknown'
            
            logger.info(f"[{self.name}] 地理位置查询完成")
            return nodes
            
        except Exception as e:
            logger.error(f"[{self.name}] 查询地理位置失败: {e}")
            # 失败时使用默认值
            for node in nodes:
                node['country'] = 'Unknown'
                node['city'] = 'Unknown'
            return nodes


class SourceC(DataSource):
    """来源C: tianshipapa/cfipcaiji"""
    
    def __init__(self):
        super().__init__("来源C", "C")
        self.url = 'https://raw.githubusercontent.com/tianshipapa/cfipcaiji/main/ip.txt'
    
    def fetch(self, **kwargs) -> List[Dict]:
        """
        从txt文件获取IP数据
        
        Returns:
            List[Dict]: 节点列表
        """
        try:
            logger.info(f"[{self.name}] 正在获取数据: {self.url}")
            
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            content = response.text
            lines = content.strip().split('\n')
            
            logger.info(f"[{self.name}] 获取到 {len(lines)} 行数据")
            
            # 解析IP和端口
            nodes = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 尝试解析 IP:端口 格式
                node = self._parse_line(line)
                if node:
                    nodes.append(node)
            
            logger.info(f"[{self.name}] 解析出 {len(nodes)} 个有效节点")
            
            # 批量查询地理位置
            if nodes:
                nodes = self._add_locations(nodes)
            
            return nodes
            
        except Exception as e:
            logger.error(f"[{self.name}] 获取数据失败: {e}")
            return []
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """解析单行数据"""
        # 匹配 IP:端口 或 纯IP
        match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::(\d+))?', line)
        if match:
            ip = match.group(1)
            port = match.group(2) or '443'  # 默认端口443
            
            return {
                'ip': ip,
                'port': port,
                'source': self.prefix
            }
        return None
    
    def _add_locations(self, nodes: List[Dict]) -> List[Dict]:
        """批量添加地理位置信息（支持CF-RAY检测）"""
        try:
            logger.info(f"[{self.name}] 正在查询 {len(nodes)} 个IP的地理位置...")
            
            # 导入get_ip_location以支持端口参数
            from .ip_location import get_ip_location
            
            # 逐个查询（因为需要传递端口信息）
            for node in nodes:
                ip = node['ip']
                port = int(node.get('port', 443))
                
                try:
                    location = get_ip_location(ip, port)
                    node['country'] = location.get('country', 'Unknown')
                    node['city'] = location.get('city', 'Unknown')
                except Exception as e:
                    logger.debug(f"查询 {ip}:{port} 位置失败: {e}")
                    node['country'] = 'Unknown'
                    node['city'] = 'Unknown'
            
            logger.info(f"[{self.name}] 地理位置查询完成")
            return nodes
            
        except Exception as e:
            logger.error(f"[{self.name}] 查询地理位置失败: {e}")
            # 失败时使用默认值
            for node in nodes:
                node['country'] = 'Unknown'
                node['city'] = 'Unknown'
            return nodes


class MultiSourceFetcher:
    """多数据源获取器"""
    
    def __init__(self):
        """初始化多数据源获取器"""
        self.sources = [
            SourceA(),
            SourceB(),
            SourceC()
        ]
    
    def fetch_all(self, countries: List[str] = None, limit: int = 10) -> List[Dict]:
        """
        从所有数据源获取IP
        
        Args:
            countries: 国家代码列表（仅用于来源A）
            limit: 每个国家的数量限制（仅用于来源A）
            
        Returns:
            List[Dict]: 所有节点列表
        """
        if countries is None:
            countries = ['JP', 'HK', 'US']
        
        all_nodes = []
        
        for source in self.sources:
            try:
                logger.info(f"正在从 {source.name} 获取数据...")
                nodes = source.fetch(countries=countries, limit=limit)
                
                if nodes:
                    logger.info(f"{source.name} 获取到 {len(nodes)} 个节点")
                    all_nodes.extend(nodes)
                else:
                    logger.warning(f"{source.name} 未获取到节点")
                    
            except Exception as e:
                logger.error(f"{source.name} 获取失败: {e}")
        
        logger.info(f"所有数据源共获取 {len(all_nodes)} 个节点")
        return all_nodes
    
    def format_nodes(self, nodes: List[Dict]) -> str:
        """
        格式化节点列表为输出文本
        
        Args:
            nodes: 节点列表
            
        Returns:
            str: 格式化后的文本
        """
        formatted = []
        
        for node in nodes:
            ip = node.get('ip', '')
            port = node.get('port', '')
            source = node.get('source', '')
            country = node.get('country', 'Unknown')
            city = node.get('city', 'Unknown')
            
            # 格式: IP:端口#来源-国家-城市
            node_str = f"{ip}:{port}#{source}-{country}-{city}"
            formatted.append(node_str)
        
        return '\n'.join(formatted)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    fetcher = MultiSourceFetcher()
    nodes = fetcher.fetch_all(countries=['JP'], limit=5)
    
    print(f"\n获取到 {len(nodes)} 个节点:")
    for node in nodes[:10]:  # 只显示前10个
        print(f"  {node['ip']}:{node['port']} - {node['source']}-{node['country']}-{node['city']}")
    
    output = fetcher.format_nodes(nodes)
    print(f"\n格式化输出 (前200字符):\n{output[:200]}...")