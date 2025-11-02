"""
主程序入口
整合IP获取和GitHub上传功能
"""
import os
import sys
import logging
from typing import Optional

from .config import get_config
from .utils import setup_logging, get_timestamp
from .ip_fetcher import IPFetcher
from .github_uploader import GitHubUploader


def check_file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path: 文件路径
    
    Returns:
        bool: 文件是否存在
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
    
    Returns:
        int: 文件大小（字节）
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def fetch_ip_data(config, logger) -> bool:
    """
    获取IP数据
    
    Args:
        config: 配置对象
        logger: 日志对象
    
    Returns:
        bool: 是否成功
    """
    logger.info("=" * 60)
    logger.info("步骤 1/2: 获取优选IP数据")
    logger.info("=" * 60)
    
    try:
        # 初始化获取器
        fetcher = IPFetcher(config)
        
        # 获取国家列表
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
            logger.error("未找到任何节点")
            return False
        
        # 转换格式并写入文件
        from .utils import format_node_list, write_to_file
        
        output_text = format_node_list(all_nodes)
        logger.info(f"生成输出文本，长度: {len(output_text)} 字符")
        
        if write_to_file(config.output_file, output_text):
            logger.info(f"成功写入输出文件: {config.output_file}")
            logger.info(f"节点数量: {len(all_nodes)}")
            logger.info(f"国家分布: {', '.join(config.filter_countries)}")
            return True
        else:
            logger.error("写入输出文件失败")
            return False
            
    except Exception as e:
        logger.error(f"获取IP数据失败: {e}", exc_info=True)
        return False


def upload_to_github(config, logger) -> bool:
    """
    上传文件到GitHub
    
    Args:
        config: 配置对象
        logger: 日志对象
    
    Returns:
        bool: 是否成功
    """
    logger.info("=" * 60)
    logger.info("步骤 2/2: 上传到GitHub")
    logger.info("=" * 60)
    
    # 检查GitHub配置
    if not config.github_token:
        logger.warning("未配置GITHUB_TOKEN，跳过GitHub上传")
        return True
    
    if not config.github_repo:
        logger.warning("未配置GITHUB_REPO，跳过GitHub上传")
        return True
    
    # 检查输出文件是否存在
    if not check_file_exists(config.output_file):
        logger.error(f"输出文件不存在: {config.output_file}")
        return False
    
    file_size = get_file_size(config.output_file)
    logger.info(f"准备上传文件: {config.output_file}")
    logger.info(f"文件大小: {file_size} 字节")
    
    try:
        # 初始化GitHub上传器
        uploader = GitHubUploader(
            token=config.github_token,
            repo_name=config.github_repo,
            branch=config.github_branch
        )
        
        # 显示API速率限制信息
        rate_limit = uploader.get_rate_limit()
        if rate_limit:
            logger.info(f"GitHub API剩余调用次数: {rate_limit.get('remaining', 'N/A')}/{rate_limit.get('limit', 'N/A')}")
        
        # 上传文件
        success = uploader.upload_file(
            local_path=config.output_file,
            target_path=config.github_file_path
        )
        
        # 关闭连接
        uploader.close()
        
        if success:
            logger.info("文件上传成功")
            return True
        else:
            logger.error("文件上传失败")
            return False
            
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return False
    except Exception as e:
        logger.error(f"上传到GitHub失败: {e}", exc_info=True)
        return False


def print_summary(logger, fetch_success: bool, upload_success: bool, start_time: str, end_time: str):
    """
    打印执行摘要
    
    Args:
        logger: 日志对象
        fetch_success: IP获取是否成功
        upload_success: GitHub上传是否成功
        start_time: 开始时间
        end_time: 结束时间
    """
    logger.info("=" * 60)
    logger.info("执行摘要")
    logger.info("=" * 60)
    logger.info(f"开始时间: {start_time}")
    logger.info(f"结束时间: {end_time}")
    logger.info(f"IP数据获取: {'✓ 成功' if fetch_success else '✗ 失败'}")
    logger.info(f"GitHub上传: {'✓ 成功' if upload_success else '✗ 失败'}")
    
    if fetch_success and upload_success:
        logger.info("状态: 全部完成")
    elif fetch_success:
        logger.info("状态: 部分完成（IP获取成功，GitHub上传失败或跳过）")
    else:
        logger.info("状态: 失败")
    
    logger.info("=" * 60)


def main() -> int:
    """
    主函数
    
    Returns:
        int: 退出码（0表示成功，1表示失败）
    """
    start_time = get_timestamp()
    
    try:
        # 加载配置
        config = get_config()
        
        # 设置日志
        logger = setup_logging(config.log_level, config.log_file)
        logger.info("=" * 60)
        logger.info("优选IP自动更新程序启动")
        logger.info(f"启动时间: {start_time}")
        logger.info("=" * 60)
        logger.info(config)
        
        # 步骤1: 获取IP数据
        fetch_success = fetch_ip_data(config, logger)
        
        if not fetch_success:
            logger.error("IP数据获取失败，程序终止")
            end_time = get_timestamp()
            print_summary(logger, fetch_success, False, start_time, end_time)
            return 1
        
        # 步骤2: 上传到GitHub
        upload_success = upload_to_github(config, logger)
        
        # 打印执行摘要
        end_time = get_timestamp()
        print_summary(logger, fetch_success, upload_success, start_time, end_time)
        
        # 返回退出码
        if fetch_success and upload_success:
            return 0
        elif fetch_success:
            # IP获取成功但上传失败，仍然返回0（因为主要任务完成）
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.warning("程序被用户中断")
        return 130
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.critical(f"程序执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())