"""
CF-RAY检测功能测试脚本
"""

import logging
import sys
import os
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cf_ray_detector import get_cloudflare_colo, get_cloudflare_colo_batch
from src.ip_location import get_ip_location

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_ip():
    """测试单个IP的CF-RAY检测"""
    print("=" * 60)
    print("测试1: 单个IP的CF-RAY检测")
    print("=" * 60)
    
    test_ips = [
        ('172.64.229.95', 443),
        ('162.159.45.47', 443),
        ('108.162.198.110', 443),
        ('104.16.132.229', 443),
    ]
    
    for ip, port in test_ips:
        print(f"\n测试IP: {ip}:{port}")
        result = get_cloudflare_colo(ip, port)
        
        if result.get('success'):
            print(f"  [OK] 检测成功")
            print(f"  机场代码: {result['colo']}")
            print(f"  国家: {result['country']}")
            print(f"  城市: {result['city']}")
        else:
            print(f"  [FAIL] 检测失败")


def test_batch_detection():
    """测试批量CF-RAY检测"""
    print("\n" + "=" * 60)
    print("测试2: 批量CF-RAY检测")
    print("=" * 60)
    
    test_ips = [
        ('172.64.229.95', 443),
        ('162.159.45.47', 443),
        ('108.162.198.110', 443),
        ('104.16.132.229', 443),
        ('104.24.0.1', 443),
    ]
    
    print(f"\n批量检测 {len(test_ips)} 个IP...")
    results = get_cloudflare_colo_batch(test_ips, max_workers=3)
    
    print(f"\n检测结果:")
    for key, result in results.items():
        if result.get('success'):
            print(f"  {key}: {result['colo']} ({result['city']}, {result['country']})")
        else:
            print(f"  {key}: 检测失败")


def test_ip_location_integration():
    """测试IP位置查询集成"""
    print("\n" + "=" * 60)
    print("测试3: IP位置查询集成（含CF-RAY检测）")
    print("=" * 60)
    
    test_cases = [
        ('172.64.229.95', 443, 'Cloudflare IP'),
        ('8.8.8.8', 443, 'Google DNS'),
        ('162.159.45.47', 443, 'Cloudflare IP'),
    ]
    
    for ip, port, description in test_cases:
        print(f"\n测试: {description} ({ip}:{port})")
        location = get_ip_location(ip, port)
        
        print(f"  国家: {location.get('country', 'Unknown')}")
        print(f"  城市: {location.get('city', 'Unknown')}")
        print(f"  来源: {location.get('source', 'Unknown')}")
        if 'colo' in location:
            print(f"  机场代码: {location['colo']}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("CF-RAY检测功能测试")
    print("=" * 60)
    
    try:
        # 测试1: 单个IP检测
        test_single_ip()
        
        # 测试2: 批量检测
        test_batch_detection()
        
        # 测试3: 集成测试
        test_ip_location_integration()
        
        print("\n" + "=" * 60)
        print("所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())