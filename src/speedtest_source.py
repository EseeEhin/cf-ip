"""
CloudflareSpeedTest 测速工具数据源模块
从测速工具生成的 result.csv 文件读取IP数据
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class SpeedTestSource:
    """yx-tools 测速工具数据源"""
    
    # 机场码到地区的映射
    AIRPORT_LOCATIONS = {
        'HKG': {'country': 'HK', 'city': '香港'},
        'NRT': {'country': 'JP', 'city': '东京'},
        'LAX': {'country': 'US', 'city': '洛杉矶'}
    }
    
    def __init__(self, result_file: str = 'result.csv'):
        """
        初始化测速工具数据源
        
        Args:
            result_file: 测速结果文件路径（相对于项目根目录）
        """
        self.name = "测速工具"
        self.prefix = "C"  # 前缀改为C，替换原来源C
        self.result_file = Path(result_file)
        
        logger.info(f"[{self.name}] 初始化完成，结果文件: {self.result_file}")
    
    def fetch(self, **kwargs) -> List[Dict]:
        """
        从 yx-tools 测速结果读取IP数据
        
        yx-tools 输出的 result.csv 格式：
        IP地址,端口,延迟平均值,下载速度,上传速度,机场码
        
        Returns:
            List[Dict]: 节点列表，每个节点包含以下字段：
                - ip: IP地址
                - port: 端口号
                - country: 国家代码
                - city: 城市名称
                - latency: 延迟（毫秒）
                - speed: 下载速度（MB/s）
                - source: 数据源标识（C）
                - airport: 机场码
        """
        # 检查文件是否存在
        if not self.result_file.exists():
            logger.warning(f"[{self.name}] 结果文件不存在: {self.result_file}")
            logger.info(f"[{self.name}] 请先运行 yx-tools 测速工具生成 result.csv 文件")
            return []
        
        try:
            logger.info(f"[{self.name}] 正在读取 yx-tools 测速结果: {self.result_file}")
            
            nodes = []
            with open(self.result_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # 提取机场码
                        airport_code = row.get('机场码', '').strip()
                        location_info = self.AIRPORT_LOCATIONS.get(airport_code, {})
                        
                        # 构建节点信息
                        node = {
                            'ip': row.get('IP地址', '').strip(),
                            'port': row.get('端口', '443').strip(),
                            'country': location_info.get('country', 'Unknown'),
                            'city': location_info.get('city', 'Unknown'),
                            'latency': float(row.get('延迟平均值', 0)),
                            'speed': float(row.get('下载速度', 0)),
                            'source': self.prefix,
                            'airport': airport_code
                        }
                        
                        # 验证必要字段
                        if node['ip'] and node['latency'] > 0:
                            nodes.append(node)
                    except Exception as e:
                        logger.debug(f"[{self.name}] 解析行数据失败: {e}")
                        continue
            
            logger.info(f"[{self.name}] 从测速工具获取到 {len(nodes)} 个节点")
            return nodes
            
        except Exception as e:
            logger.error(f"[{self.name}] 解析测速结果失败: {e}")
            return []
    
    def _parse_csv(self) -> List[Dict]:
        """
        解析CSV文件
        
        Returns:
            List[Dict]: 解析出的节点列表（不含地理位置信息）
        """
        nodes = []
        
        try:
            with open(self.result_file, 'r', encoding='utf-8') as f:
                # 使用csv.DictReader自动处理表头
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是表头）
                    try:
                        node = self._parse_row(row)
                        if node:
                            nodes.append(node)
                    except Exception as e:
                        logger.warning(f"[{self.name}] 解析第 {row_num} 行失败: {e}")
                        continue
            
            return nodes
            
        except Exception as e:
            logger.error(f"[{self.name}] 读取CSV文件失败: {e}")
            return []
    
    def _parse_row(self, row: Dict[str, str]) -> Optional[Dict]:
        """
        解析CSV的单行数据
        
        Args:
            row: CSV行数据（字典格式）
            
        Returns:
            Optional[Dict]: 解析出的节点信息，失败返回None
        """
        try:
            # CloudflareSpeedTest 的 result.csv 通常包含以下列：
            # IP地址, 已发送, 已接收, 丢包率, 平均延迟, 下载速度 (MB/s)
            # 或者：IP 地址, 端口, 数据中心, 地区, 城市, 网络延迟, 下载速度, 上传速度
            
            # 尝试获取IP地址（支持多种列名）
            ip = None
            for key in ['IP地址', 'IP 地址', 'IP', 'ip', 'IP Address']:
                if key in row and row[key]:
                    ip = row[key].strip()
                    break
            
            if not ip:
                return None
            
            # 获取端口（如果有）
            port = '443'  # 默认端口
            for key in ['端口', '端口号', 'Port', 'port']:
                if key in row and row[key]:
                    port = row[key].strip()
                    break
            
            # 获取延迟
            latency = None
            for key in ['平均延迟', '网络延迟', '延迟', 'Latency', 'latency', '平均延迟 (ms)']:
                if key in row and row[key]:
                    try:
                        latency_str = row[key].strip().replace('ms', '').strip()
                        latency = float(latency_str)
                        break
                    except (ValueError, AttributeError):
                        continue
            
            # 获取下载速度
            speed = None
            for key in ['下载速度', '下载速度 (MB/s)', 'Download Speed', 'Speed', 'speed']:
                if key in row and row[key]:
                    try:
                        speed_str = row[key].strip().replace('MB/s', '').strip()
                        speed = float(speed_str)
                        break
                    except (ValueError, AttributeError):
                        continue
            
            # 构建节点信息
            node = {
                'ip': ip,
                'port': port,
                'source': self.prefix
            }
            
            # 添加可选字段
            if latency is not None:
                node['latency'] = latency
            if speed is not None:
                node['speed'] = speed
            
            return node
            
        except Exception as e:
            logger.debug(f"[{self.name}] 解析行数据失败: {e}")
            return None
    
    def _add_locations(self, nodes: List[Dict]) -> List[Dict]:
        """
        批量添加地理位置信息（支持CF-RAY检测）
        
        Args:
            nodes: 节点列表
            
        Returns:
            List[Dict]: 添加了地理位置信息的节点列表
        """
        try:
            logger.info(f"[{self.name}] 正在查询 {len(nodes)} 个IP的地理位置...")
            
            # 导入地理位置检测模块
            from .ip_location import get_ip_location
            from .config import Config
            
            # 获取并发配置
            config = Config()
            max_workers = getattr(config, 'cf_ray_max_workers', 5)
            
            # 使用线程池并发查询
            def query_location(node):
                """查询单个节点的地理位置"""
                ip = node['ip']
                port = int(node.get('port', 443))
                try:
                    location = get_ip_location(ip, port)
                    return (node, location.get('country', 'Unknown'), location.get('city', 'Unknown'))
                except Exception as e:
                    logger.debug(f"查询 {ip}:{port} 位置失败: {e}")
                    return (node, 'Unknown', 'Unknown')
            
            # 并发查询所有节点
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(query_location, node): node for node in nodes}
                
                for future in as_completed(futures):
                    try:
                        node, country, city = future.result()
                        node['country'] = country
                        node['city'] = city
                    except Exception as e:
                        node = futures[future]
                        logger.error(f"查询 {node['ip']} 异常: {e}")
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


# 测试代码
if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建数据源实例
    source = SpeedTestSource()
    
    # 获取节点
    nodes = source.fetch()
    
    # 显示结果
    print(f"\n获取到 {len(nodes)} 个节点:")
    for i, node in enumerate(nodes[:10], 1):  # 只显示前10个
        latency = node.get('latency', 'N/A')
        speed = node.get('speed', 'N/A')
        print(f"{i}. {node['ip']}:{node['port']} - "
              f"{node['source']}-{node['country']}-{node['city']} - "
              f"延迟: {latency}ms, 速度: {speed}MB/s")