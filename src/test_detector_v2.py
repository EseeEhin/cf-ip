"""
IP检测器V2测试脚本
用于验证改进的IP地区检测系统
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ip_detector_v2 import IPDetectorV2
from src.config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_ip():
    """测试单个IP检测"""
    print("\n" + "="*60)
    print("测试1: 单个IP检测")
    print("="*60)
    
    # 创建检测器
    detector = IPDetectorV2()
    
    # 测试IP列表
    test_ips = [
        ('172.64.229.95', 443, 'Cloudflare IP - 应该通过CF-RAY检测'),
        ('104.16.132.229', 443, 'Cloudflare IP - 应该通过CF-RAY检测'),
        ('8.8.8.8', 443, '非Cloudflare IP - 应该通过API或GeoIP检测'),
    ]
    
    for ip, port, description in test_ips:
        print(f"\n测试IP: {ip}:{port}")
        print(f"说明: {description}")
        
        result = detector.detect(ip, port)
        
        if result:
            print(f"✓ 检测成功:")
            print(f"  - 国家: {result['country']}")
            print(f"  - 城市: {result['city']}")
            print(f"  - 来源: {result['source']}")
            if 'colo' in result:
                print(f"  - 数据中心: {result['colo']}")
        else:
            print(f"✗ 检测失败")
    
    # 输出统计
    print("\n" + detector.get_summary())
    
    # 关闭检测器
    detector.close()


def test_batch_detection():
    """测试批量检测"""
    print("\n" + "="*60)
    print("测试2: 批量IP检测")
    print("="*60)
    
    # 创建检测器
    detector = IPDetectorV2()
    
    # 测试IP列表
    test_ips = [
        '172.64.229.95',
        '104.16.132.229',
        '162.159.45.47',
        '108.162.198.110',
        '8.8.8.8',
    ]
    
    print(f"\n批量检测 {len(test_ips)} 个IP...")
    
    results = detector.detect_batch(test_ips, max_workers=3)
    
    print("\n检测结果:")
    for ip, location in results.items():
        if location:
            print(f"  {ip} -> {location['country']}-{location['city']} (来源: {location['source']})")
        else:
            print(f"  {ip} -> 检测失败")
    
    # 输出统计
    print("\n" + detector.get_summary())
    
    # 关闭检测器
    detector.close()


def test_cache():
    """测试缓存功能"""
    print("\n" + "="*60)
    print("测试3: 缓存功能")
    print("="*60)
    
    # 创建检测器
    detector = IPDetectorV2()
    
    test_ip = '172.64.229.95'
    
    # 第一次检测
    print(f"\n第一次检测 {test_ip}...")
    result1 = detector.detect(test_ip)
    if result1:
        print(f"✓ 检测成功: {result1['country']}-{result1['city']} (来源: {result1['source']})")
    
    # 第二次检测（应该命中缓存）
    print(f"\n第二次检测 {test_ip} (应该命中缓存)...")
    result2 = detector.detect(test_ip)
    if result2:
        print(f"✓ 检测成功: {result2['country']}-{result2['city']} (来源: {result2['source']})")
    
    # 输出缓存统计
    cache_stats = detector.cache.get_stats()
    print(f"\n缓存统计:")
    print(f"  - 缓存命中: {cache_stats['hits']}")
    print(f"  - 缓存未命中: {cache_stats['misses']}")
    print(f"  - 缓存命中率: {cache_stats['hit_rate']}")
    
    # 关闭检测器
    detector.close()


def test_api_fallback():
    """测试API降级功能"""
    print("\n" + "="*60)
    print("测试4: API降级功能")
    print("="*60)
    
    # 创建配置，禁用CF-RAY以测试API降级
    config = Config()
    config.cf_ray_detection_enabled = False
    config.api_enabled = True
    
    # 创建检测器
    detector = IPDetectorV2(config)
    
    test_ip = '8.8.8.8'
    
    print(f"\n检测 {test_ip} (CF-RAY已禁用，应该使用API)...")
    result = detector.detect(test_ip)
    
    if result:
        print(f"✓ 检测成功:")
        print(f"  - 国家: {result['country']}")
        print(f"  - 城市: {result['city']}")
        print(f"  - 来源: {result['source']}")
        
        if result['source'].startswith('api_') or result['source'] in ['baidu_api', 'ip_api_com', 'pconline_api']:
            print(f"✓ API降级成功")
        else:
            print(f"⚠ 未使用API，来源: {result['source']}")
    else:
        print(f"✗ 检测失败")
    
    # 输出API统计
    api_stats = detector.api_manager.get_stats()
    if api_stats:
        print(f"\nAPI统计:")
        for api_name, stats in api_stats.items():
            print(f"  - {api_name}: {stats['successful_requests']}/{stats['total_requests']} ({stats['success_rate']})")
    
    # 关闭检测器
    detector.close()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("IP检测器V2 测试套件")
    print("="*60)
    
    try:
        # 运行所有测试
        test_single_ip()
        test_batch_detection()
        test_cache()
        test_api_fallback()
        
        print("\n" + "="*60)
        print("所有测试完成!")
        print("="*60)
    
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        print(f"\n✗ 测试失败: {e}")


if __name__ == '__main__':
    main()