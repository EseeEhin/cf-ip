"""
工具模块
提供数据格式转换、文件操作和日志配置等辅助功能
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime


def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为None则只输出到控制台
    
    Returns:
        logging.Logger: 配置好的日志对象
    """
    # 创建日志目录
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志格式
    log_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(),  # 控制台输出
        ]
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logging.getLogger().addHandler(file_handler)
    
    return logging.getLogger(__name__)


def format_node(ip: str, port: str, country: str = '', city: str = '') -> str:
    """
    格式化单个节点
    
    Args:
        ip: IP地址
        port: 端口号
        country: 国家代码
        city: 城市名称
    
    Returns:
        str: 格式化后的节点字符串
    """
    if country and city:
        # 格式: IP:端口#国家-城市
        return f"{ip}:{port}#{country}-{city}"
    else:
        # 格式: IP:端口
        return f"{ip}:{port}"


def format_node_list(nodes: List[Dict[str, str]], separator: str = ',') -> str:
    """
    格式化节点列表为输出字符串
    
    Args:
        nodes: 节点列表，每个节点是包含ip, port, country, city的字典
        separator: 节点之间的分隔符
    
    Returns:
        str: 格式化后的节点字符串
    """
    formatted_nodes = []
    for node in nodes:
        formatted = format_node(
            node.get('ip', ''),
            node.get('port', ''),
            node.get('country', ''),
            node.get('city', '')
        )
        formatted_nodes.append(formatted)
    
    return separator.join(formatted_nodes)


def filter_by_latency(nodes: List[Dict], max_latency: int) -> List[Dict]:
    """
    根据延迟过滤节点
    
    Args:
        nodes: 节点列表
        max_latency: 最大延迟阈值（毫秒）
    
    Returns:
        List[Dict]: 过滤后的节点列表
    """
    return [node for node in nodes if node.get('latency', float('inf')) <= max_latency]


def filter_by_countries(nodes: List[Dict], countries: List[str]) -> List[Dict]:
    """
    根据国家代码过滤节点
    
    Args:
        nodes: 节点列表
        countries: 允许的国家代码列表
    
    Returns:
        List[Dict]: 过滤后的节点列表
    """
    if not countries:
        return nodes
    
    return [node for node in nodes if node.get('country', '') in countries]


def write_to_file(file_path: str, content: str) -> bool:
    """
    写入内容到文件
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
    
    Returns:
        bool: 是否写入成功
    """
    try:
        # 创建目录（如果不存在）
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        logging.error(f"写入文件失败: {file_path}, 错误: {e}")
        return False


def read_from_file(file_path: str) -> Optional[str]:
    """
    从文件读取内容
    
    Args:
        file_path: 文件路径
    
    Returns:
        Optional[str]: 文件内容，如果读取失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"读取文件失败: {file_path}, 错误: {e}")
        return None


def validate_ip(ip: str) -> bool:
    """
    验证IP地址格式
    
    Args:
        ip: IP地址字符串
    
    Returns:
        bool: 是否为有效的IP地址
    """
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def validate_port(port: str) -> bool:
    """
    验证端口号
    
    Args:
        port: 端口号字符串
    
    Returns:
        bool: 是否为有效的端口号
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False


def get_timestamp() -> str:
    """
    获取当前时间戳字符串
    
    Returns:
        str: 格式化的时间戳
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def parse_latency(latency_str: str) -> int:
    """
    解析延迟字符串
    
    Args:
        latency_str: 延迟字符串，如 "0ms", "100ms"
    
    Returns:
        int: 延迟值（毫秒），解析失败返回999999
    """
    try:
        # 移除 "ms" 后缀并转换为整数
        return int(latency_str.replace('ms', '').strip())
    except (ValueError, AttributeError):
        return 999999  # 返回一个很大的值表示无效