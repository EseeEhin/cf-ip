"""
优选IP获取和转换主脚本
从 https://cfip.wxgqlfx.fun/ 通过API获取优选IP数据并转换格式
"""
import re
import logging
import time
from typing import List, Dict, Optional
import requests

from .config import get_config
from .utils import (
    setup_logging,
    format_node_list,
    write_to_file,
    validate_ip,
    validate_port,
    get_timestamp
)


class IPFetcher:
    """IP数据获取器 - 使用API方式"""
    
    def __init__(self, config):
        """
        初始化IP获取器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json'
        })
    
    def fetch_countries(self, retry: int = 0) -> List[Dict[str, str]]:
        """
        获取可用国家列表
        
        Args:
            retry: 当前重试次数
        
        Returns:
            List[Dict]: 国家列表
        """
        try:
            self.logger.info(f"正在获取国家列表: {self.config.api_countries_url}")
            response = self.session.get(
                self.config.api_countries_url,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            countries = response.json()
            self.logger.info(f"成功获取 {len(countries)} 个国家")
            return countries
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取国家列表失败 (尝试 {retry + 1}/{self.config.max_retries}): {e}")
            
            if retry < self.config.max_retries - 1:
                wait_time = (retry + 1) * 2
                self.logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return self.fetch_countries(retry + 1)
            
            return []
    
    def fetch_proxies(self, country_code: str, port: str = '', limit: int = 100, retry: int = 0) -> List[Dict[str, str]]:
        """
        查询代理IP
        
        Args:
            country_code: 国家代码 (如: JP, US, SG)
            port: 端口号 (可选)
            limit: 返回数量限制
            retry: 当前重试次数
        
        Returns:
            List[Dict]: 代理列表
        """
        try:
            payload = {
                'country': country_code,
                'port': port,
                'limit': limit
            }
            
            self.logger.info(f"正在查询代理: 国家={country_code}, 端口={port or '任意'}, 限制={limit}")
            response = self.session.post(
                self.config.api_query_url,
                json=payload,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            data = response.json()
            proxies = data.get('proxies', [])
            total = data.get('totalProxies', 0)
            
            self.logger.info(f"查询成功: 总数={total}, 返回={len(proxies)}")
            
            # 转换为统一格式
            nodes = []
            for proxy in proxies:
                node = {
                    'ip': proxy.get('ip', ''),
                    'port': str(proxy.get('port', '')),
                    'country': proxy.get('country', ''),
                    'city': proxy.get('city', 'N/A'),
                    'latency': 0  # API不提供延迟，设为0
                }
                
                # 验证数据
                if validate_ip(node['ip']) and validate_port(node['port']):
                    nodes.append(node)
            
            self.logger.info(f"有效节点数: {len(nodes)}")
            return nodes
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"查询代理失败 (尝试 {retry + 1}/{self.config.max_retries}): {e}")
            
            if retry < self.config.max_retries - 1:
                wait_time = (retry + 1) * 2
                self.logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return self.fetch_proxies(country_code, port, limit, retry + 1)
            
            return []


def main():
    """主函数"""
    # 加载配置
    config = get_config()
    
    # 设置日志
    logger = setup_logging(config.log_level, config.log_file)
    logger.info("=" * 60)
    logger.info("优选IP获取程序启动 (API模式)")
    logger.info(f"启动时间: {get_timestamp()}")
    logger.info(config)
    
    try:
        # 初始化获取器
        fetcher = IPFetcher(config)
        
        # 获取国家列表（用于验证配置的国家代码）
        countries = fetcher.fetch_countries()
        if not countries:
            logger.warning("无法获取国家列表，但继续执行")
        
        # 收集所有节点
        all_nodes = []
        
        # 按配置的国家查询代理
        for country_code in config.filter_countries:
            logger.info(f"正在查询国家: {country_code}")
            nodes = fetcher.fetch_proxies(
                country_code=country_code,
                port='',
                limit=config.query_limit
            )
            
            if nodes:
                logger.info(f"从 {country_code} 获取到 {len(nodes)} 个节点")
                all_nodes.extend(nodes)
            else:
                logger.warning(f"从 {country_code} 未获取到节点")
        
        logger.info(f"共获取到 {len(all_nodes)} 个节点")
        
        if not all_nodes:
            logger.warning("未找到任何节点")
            return 1
        
        # 注意: API返回的数据没有延迟信息，所以不进行延迟过滤
        # 如果需要延迟过滤，需要在客户端测试每个IP的延迟
        logger.info(f"跳过延迟过滤 (API不提供延迟数据)")
        
        filtered_nodes = all_nodes
        
        # 转换格式
        output_text = format_node_list(filtered_nodes)
        logger.info(f"生成输出文本，长度: {len(output_text)} 字符")
        logger.debug(f"输出内容预览: {output_text[:200]}...")
        
        # 写入文件
        if write_to_file(config.output_file, output_text):
            logger.info(f"成功写入输出文件: {config.output_file}")
            logger.info(f"节点数量: {len(filtered_nodes)}")
            logger.info(f"国家分布: {', '.join(config.filter_countries)}")
        else:
            logger.error("写入输出文件失败")
            return 1
        
        logger.info("程序执行完成")
        logger.info("=" * 60)
        return 0
        
    except Exception as e:
        logger.critical(f"程序执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())