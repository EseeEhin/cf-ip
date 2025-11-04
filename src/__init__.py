"""
优选IP获取和转换模块
提供从网页获取优选IP并转换格式的功能
"""

__version__ = '1.0.0'
__author__ = 'Clash CF Updater'
__description__ = 'Cloudflare优选IP自动获取和转换工具'

from .config import Config, get_config
from .utils import (
    setup_logging,
    format_node,
    format_node_list,
    filter_by_latency,
    filter_by_countries,
    write_to_file,
    read_from_file,
    validate_ip,
    validate_port,
    get_timestamp,
    parse_latency
)
from .ip_fetcher import IPFetcher, main

__all__ = [
    'Config',
    'get_config',
    'IPFetcher',
    'main',
    'setup_logging',
    'format_node',
    'format_node_list',
    'filter_by_latency',
    'filter_by_countries',
    'write_to_file',
    'read_from_file',
    'validate_ip',
    'validate_port',
    'get_timestamp',
    'parse_latency'
]