"""
主程序入口
整合IP获取和GitHub上传功能
"""
import os
import sys
import logging
from typing import Optional

from .config import get_config
from .utils import setup_logging, get_timestamp, write_to_file
from .multi_source_fetcher import MultiSourceFetcher
from .github_uploader import GitHubUploader
from .api_uploader import APIUploader, format_ips_for_api


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
    获取IP数据（使用多数据源）
    
    Args:
        config: 配置对象
        logger: 日志对象
    
    Returns:
        bool: 是否成功
    """
    logger.info("=" * 60)
    logger.info("步骤 1/2: 获取优选IP数据（多数据源模式）")
    logger.info("=" * 60)
    
    try:
        # 初始化多数据源获取器
        fetcher = MultiSourceFetcher()
        
        # 从所有数据源获取节点
        logger.info(f"配置的国家: {', '.join(config.filter_countries)}")
        logger.info(f"每个国家限制: {config.query_limit} 个节点")
        
        all_nodes = fetcher.fetch_all(
            countries=config.filter_countries,
            limit=config.query_limit
        )
        
        if not all_nodes:
            logger.error("未找到任何节点")
            return False
        
        logger.info(f"共获取到 {len(all_nodes)} 个节点")
        
        # 统计各数据源的节点数
        source_stats = {}
        for node in all_nodes:
            source = node.get('source', 'Unknown')
            source_stats[source] = source_stats.get(source, 0) + 1
        
        logger.info("数据源统计:")
        for source, count in source_stats.items():
            logger.info(f"  {source}: {count} 个节点")
        
        # 格式化输出
        output_text = fetcher.format_nodes(all_nodes)
        logger.info(f"生成输出文本，长度: {len(output_text)} 字符")
        
        # 写入文件
        if write_to_file(config.output_file, output_text):
            logger.info(f"成功写入输出文件: {config.output_file}")
            logger.info(f"总节点数量: {len(all_nodes)}")
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


def upload_to_api(config, logger, all_nodes: list) -> bool:
    """
    通过API上传优选IP到订阅项目
    
    Args:
        config: 配置对象
        logger: 日志对象
        all_nodes: 所有节点列表
    
    Returns:
        bool: 是否成功
    """
    logger.info("=" * 60)
    logger.info("步骤 3/3: 上传到订阅项目API")
    logger.info("=" * 60)
    
    # 检查API配置
    if not config.api_upload_enabled:
        logger.info("API上传功能未启用，跳过")
        return True
    
    if not config.subscription_api_url:
        logger.warning("未配置SUBSCRIPTION_API_URL，跳过API上传")
        return True
    
    if not config.subscription_api_path:
        logger.warning("未配置SUBSCRIPTION_API_PATH，跳过API上传")
        return True
    
    try:
        # 初始化API上传器
        uploader = APIUploader(
            api_url=config.subscription_api_url,
            api_path=config.subscription_api_path
        )
        
        # 格式化IP列表
        formatted_ips = format_ips_for_api(all_nodes)
        logger.info(f"准备上传 {len(formatted_ips)} 个优选IP到订阅项目")
        
        # 上传IP
        success = uploader.add_ips(formatted_ips)
        
        if success:
            logger.info("✅ API上传成功")
            return True
        else:
            logger.error("❌ API上传失败")
            return False
            
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return False
    except Exception as e:
        logger.error(f"API上传失败: {e}", exc_info=True)
        return False


def print_summary(logger, fetch_success: bool, upload_success: bool, api_success: bool, start_time: str, end_time: str):
    """
    打印执行摘要
    
    Args:
        logger: 日志对象
        fetch_success: IP获取是否成功
        upload_success: GitHub上传是否成功
        api_success: API上传是否成功
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
    logger.info(f"API上传: {'✓ 成功' if api_success else '✗ 失败'}")
    
    if fetch_success and upload_success and api_success:
        logger.info("状态: 全部完成")
    elif fetch_success:
        logger.info("状态: 部分完成")
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
    all_nodes = []  # 保存所有节点数据
    
    try:
        # 确保必要的目录存在（在任何操作之前）
        for directory in ['logs', 'output', 'cache']:
            os.makedirs(directory, exist_ok=True)
        
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
        logger.info("=" * 60)
        logger.info("步骤 1/3: 获取优选IP数据（多数据源模式）")
        logger.info("=" * 60)
        
        try:
            # 初始化多数据源获取器
            fetcher = MultiSourceFetcher()
            
            # 从所有数据源获取节点
            logger.info(f"配置的国家: {', '.join(config.filter_countries)}")
            logger.info(f"每个国家限制: {config.query_limit} 个节点")
            
            all_nodes = fetcher.fetch_all(
                countries=config.filter_countries,
                limit=config.query_limit
            )
            
            if not all_nodes:
                logger.error("未找到任何节点")
                fetch_success = False
            else:
                logger.info(f"共获取到 {len(all_nodes)} 个节点")
                
                # 统计各数据源的节点数
                source_stats = {}
                for node in all_nodes:
                    source = node.get('source', 'Unknown')
                    source_stats[source] = source_stats.get(source, 0) + 1
                
                logger.info("数据源统计:")
                for source, count in source_stats.items():
                    logger.info(f"  {source}: {count} 个节点")
                
                # 格式化输出
                output_text = fetcher.format_nodes(all_nodes)
                logger.info(f"生成输出文本，长度: {len(output_text)} 字符")
                
                # 写入文件
                if write_to_file(config.output_file, output_text):
                    logger.info(f"成功写入输出文件: {config.output_file}")
                    logger.info(f"总节点数量: {len(all_nodes)}")
                    fetch_success = True
                else:
                    logger.error("写入输出文件失败")
                    fetch_success = False
                    
        except Exception as e:
            logger.error(f"获取IP数据失败: {e}", exc_info=True)
            fetch_success = False
        
        if not fetch_success:
            logger.error("IP数据获取失败，程序终止")
            end_time = get_timestamp()
            print_summary(logger, fetch_success, False, False, start_time, end_time)
            return 1
        
        # 步骤2: 上传到GitHub
        upload_success = upload_to_github(config, logger)
        
        # 步骤3: 上传到订阅项目API
        api_success = upload_to_api(config, logger, all_nodes)
        
        # 打印执行摘要
        end_time = get_timestamp()
        print_summary(logger, fetch_success, upload_success, api_success, start_time, end_time)
        
        # 返回退出码
        if fetch_success:
            # IP获取成功，即使上传失败也返回0（因为主要任务完成）
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