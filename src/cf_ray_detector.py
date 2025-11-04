"""
CF-RAY检测模块
通过实际连接Cloudflare节点，从CF-RAY响应头获取真实的数据中心位置
"""

import logging
import requests
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Cloudflare数据中心机场代码映射表
# 参考: https://www.cloudflarestatus.com/
COLO_MAP = {
    # 日本
    'NRT': {'country': 'JP', 'city': 'Tokyo'},
    'HND': {'country': 'JP', 'city': 'Tokyo'},
    'KIX': {'country': 'JP', 'city': 'Osaka'},
    
    # 美国
    'LAX': {'country': 'US', 'city': 'Los Angeles'},
    'SJC': {'country': 'US', 'city': 'San Jose'},
    'SEA': {'country': 'US', 'city': 'Seattle'},
    'ORD': {'country': 'US', 'city': 'Chicago'},
    'DFW': {'country': 'US', 'city': 'Dallas'},
    'IAD': {'country': 'US', 'city': 'Ashburn'},
    'ATL': {'country': 'US', 'city': 'Atlanta'},
    'MIA': {'country': 'US', 'city': 'Miami'},
    'EWR': {'country': 'US', 'city': 'Newark'},
    'DEN': {'country': 'US', 'city': 'Denver'},
    'PHX': {'country': 'US', 'city': 'Phoenix'},
    
    # 香港
    'HKG': {'country': 'HK', 'city': 'Hong Kong'},
    
    # 新加坡
    'SIN': {'country': 'SG', 'city': 'Singapore'},
    
    # 韩国
    'ICN': {'country': 'KR', 'city': 'Seoul'},
    
    # 台湾
    'TPE': {'country': 'TW', 'city': 'Taipei'},
    
    # 英国
    'LHR': {'country': 'GB', 'city': 'London'},
    'MAN': {'country': 'GB', 'city': 'Manchester'},
    
    # 德国
    'FRA': {'country': 'DE', 'city': 'Frankfurt'},
    
    # 法国
    'CDG': {'country': 'FR', 'city': 'Paris'},
    
    # 荷兰
    'AMS': {'country': 'NL', 'city': 'Amsterdam'},
    
    # 澳大利亚
    'SYD': {'country': 'AU', 'city': 'Sydney'},
    'MEL': {'country': 'AU', 'city': 'Melbourne'},
    
    # 加拿大
    'YYZ': {'country': 'CA', 'city': 'Toronto'},
    'YVR': {'country': 'CA', 'city': 'Vancouver'},
    
    # 印度
    'BOM': {'country': 'IN', 'city': 'Mumbai'},
    'DEL': {'country': 'IN', 'city': 'Delhi'},
    
    # 巴西
    'GRU': {'country': 'BR', 'city': 'Sao Paulo'},
    
    # 南非
    'JNB': {'country': 'ZA', 'city': 'Johannesburg'},
    
    # 阿联酋
    'DXB': {'country': 'AE', 'city': 'Dubai'},
    
    # 泰国
    'BKK': {'country': 'TH', 'city': 'Bangkok'},
    
    # 马来西亚
    'KUL': {'country': 'MY', 'city': 'Kuala Lumpur'},
    
    # 菲律宾
    'MNL': {'country': 'PH', 'city': 'Manila'},
    
    # 越南
    'SGN': {'country': 'VN', 'city': 'Ho Chi Minh City'},
    'HAN': {'country': 'VN', 'city': 'Hanoi'},
    
    # 印度尼西亚
    'CGK': {'country': 'ID', 'city': 'Jakarta'},
    
    # 西班牙
    'MAD': {'country': 'ES', 'city': 'Madrid'},
    
    # 意大利
    'MXP': {'country': 'IT', 'city': 'Milan'},
    
    # 瑞典
    'ARN': {'country': 'SE', 'city': 'Stockholm'},
    
    # 波兰
    'WAW': {'country': 'PL', 'city': 'Warsaw'},
    
    # 俄罗斯
    'DME': {'country': 'RU', 'city': 'Moscow'},
    
    # 土耳其
    'IST': {'country': 'TR', 'city': 'Istanbul'},
    
    # 以色列
    'TLV': {'country': 'IL', 'city': 'Tel Aviv'},
    
    # 新西兰
    'AKL': {'country': 'NZ', 'city': 'Auckland'},
    
    # 智利
    'SCL': {'country': 'CL', 'city': 'Santiago'},
    
    # 阿根廷
    'EZE': {'country': 'AR', 'city': 'Buenos Aires'},
}


def get_cloudflare_colo(ip: str, port: int = 443, timeout: int = 5) -> Dict:
    """
    通过CF-RAY头获取Cloudflare数据中心位置
    
    Args:
        ip: Cloudflare IP地址
        port: 端口号，默认443
        timeout: 超时时间（秒），默认5秒
    
    Returns:
        dict: 包含以下字段的字典
            - colo: 机场代码（如 "NRT"）
            - country: 国家代码（如 "JP"）
            - city: 城市名（如 "Tokyo"）
            - success: 是否成功获取
    """
    try:
        # 构造请求URL
        url = f"https://{ip}:{port}"
        
        # 设置请求头
        headers = {
            'Host': 'speed.cloudflare.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 发起请求
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=False,  # 禁用SSL验证
<<<<<<< HEAD
            allow_redirects=True,
            proxies={'http': None, 'https': None}  # 绕过代理直接连接
=======
            allow_redirects=True
>>>>>>> 8fbb685c5af779c3b93a258593411d2902c91c49
        )
        
        # 获取CF-RAY响应头
        cf_ray = response.headers.get('CF-RAY', '')
        
        if not cf_ray:
            logger.debug(f"未找到CF-RAY头: {ip}:{port}")
            return {'success': False}
        
        # 解析CF-RAY格式: "8xxxxx-NRT"
        # 提取最后的机场代码（最后3个字母）
        parts = cf_ray.split('-')
        if len(parts) < 2:
            logger.debug(f"CF-RAY格式异常: {cf_ray}")
            return {'success': False}
        
        colo = parts[-1].upper()
        
        # 查找机场代码对应的位置信息
        if colo in COLO_MAP:
            location = COLO_MAP[colo]
            result = {
                'colo': colo,
                'country': location['country'],
                'city': location['city'],
                'success': True
            }
            logger.debug(f"CF-RAY检测成功: {ip}:{port} -> {colo} ({location['city']}, {location['country']})")
            return result
        else:
            # 未知的机场代码，但仍然返回成功
            logger.warning(f"未知的机场代码: {colo} (IP: {ip}:{port})")
            return {
                'colo': colo,
                'country': 'CF',
                'city': f'Unknown-{colo}',
                'success': True
            }
    
    except requests.exceptions.Timeout:
        logger.debug(f"CF-RAY检测超时: {ip}:{port}")
        return {'success': False}
    
    except requests.exceptions.ConnectionError:
        logger.debug(f"CF-RAY检测连接失败: {ip}:{port}")
        return {'success': False}
    
    except requests.exceptions.SSLError:
        logger.debug(f"CF-RAY检测SSL错误: {ip}:{port}")
        return {'success': False}
    
    except Exception as e:
        logger.debug(f"CF-RAY检测异常: {ip}:{port}, 错误: {e}")
        return {'success': False}


def get_cloudflare_colo_batch(
    ip_port_list: List[tuple],
    max_workers: int = 10,
    timeout: int = 5
) -> Dict[str, Dict]:
    """
    批量检测Cloudflare数据中心位置
    
    Args:
        ip_port_list: IP和端口的元组列表 [(ip, port), ...]
        max_workers: 最大并发数，默认10
        timeout: 单个请求超时时间（秒），默认5秒
    
    Returns:
        dict: IP:端口 -> 位置信息的映射
    """
    results = {}
    success_count = 0
    total_count = len(ip_port_list)
    
    logger.info(f"开始批量CF-RAY检测: {total_count} 个节点")
    
    # 使用线程池并发检测
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_ip = {
            executor.submit(get_cloudflare_colo, ip, port, timeout): (ip, port)
            for ip, port in ip_port_list
        }
        
        # 收集结果
        for future in as_completed(future_to_ip):
            ip, port = future_to_ip[future]
            key = f"{ip}:{port}"
            
            try:
                result = future.result()
                results[key] = result
                
                if result.get('success'):
                    success_count += 1
                    logger.info(
                        f"CF-RAY检测成功: {key} -> {result['colo']} "
                        f"({result['city']}, {result['country']})"
                    )
                else:
                    logger.debug(f"CF-RAY检测失败: {key}")
            
            except Exception as e:
                logger.error(f"CF-RAY检测异常: {key}, 错误: {e}")
                results[key] = {'success': False}
    
    logger.info(f"CF-RAY检测完成: 成功 {success_count}/{total_count}")
    
    return results


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试单个IP
    print("测试单个IP:")
    test_ips = [
        ('172.64.229.95', 443),
        ('162.159.45.47', 443),
        ('108.162.198.110', 443),
    ]
    
    for ip, port in test_ips:
        result = get_cloudflare_colo(ip, port)
        if result['success']:
            print(f"{ip}:{port} -> {result['colo']} ({result['city']}, {result['country']})")
        else:
            print(f"{ip}:{port} -> 检测失败")
    
    # 测试批量检测
    print("\n测试批量检测:")
    batch_results = get_cloudflare_colo_batch(test_ips, max_workers=3)
    for key, result in batch_results.items():
        if result['success']:
            print(f"{key} -> {result['colo']} ({result['city']}, {result['country']})")
        else:
            print(f"{key} -> 检测失败")