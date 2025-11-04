"""
测试Cloudflare IP优先检测策略
验证CF IP是否优先使用CF-RAY检测
"""

import logging
import sys
from .ip_detector_v2 import IPDetectorV2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_cf_priority():
    """测试Cloudflare IP优先检测策略"""
    
    print("=" * 80)
    print("测试Cloudflare IP优先检测策略")
    print("=" * 80)
    
    # 测试IP列表
    test_ips = [
        ('104.16.132.229', 'Cloudflare IP - 日本节点'),
        ('172.64.229.95', 'Cloudflare IP - 日本节点'),
        ('108.162.198.110', 'Cloudflare IP - 日本节点'),
        ('162.159.45.47', 'Cloudflare IP'),
        ('8.8.8.8', '非Cloudflare IP - Google DNS'),
        ('1.1.1.1', 'Cloudflare DNS'),
    ]
    
    # 创建检测器
    detector = IPDetectorV2()
    
    print("\n开始测试...\n")
    
    for ip, description in test_ips:
        print(f"\n{'=' * 80}")
        print(f"测试IP: {ip} ({description})")
        print(f"{'=' * 80}")
        
        # 检查是否为Cloudflare IP
        is_cf = detector.is_cloudflare_ip(ip)
        print(f"是否为Cloudflare IP: {'是' if is_cf else '否'}")
        
        # 检测IP位置
        result = detector.detect(ip, 443)
        
        if result:
            print(f"\n检测结果:")
            print(f"  - 国家: {result.get('country', 'N/A')}")
            print(f"  - 城市: {result.get('city', 'N/A')}")
            print(f"  - 来源: {result.get('source', 'N/A')}")
            if 'colo' in result:
                print(f"  - 数据中心: {result['colo']}")
            
            # 验证检测策略
            if is_cf:
                if result.get('source') == 'cf_ray':
                    print(f"\n✓ 正确：Cloudflare IP使用CF-RAY检测")
                else:
                    print(f"\n✗ 警告：Cloudflare IP未使用CF-RAY检测，使用了{result.get('source')}")
            else:
                print(f"\n✓ 非Cloudflare IP，使用{result.get('source')}检测")
        else:
            print(f"\n✗ 检测失败")
    
    # 输出统计信息
    print(f"\n{'=' * 80}")
    print("检测统计:")
    print(f"{'=' * 80}")
    print(detector.get_summary())
    
    # 关闭检测器
    detector.close()


def test_cf_ip_ranges():
    """测试Cloudflare IP段识别"""
    
    print("\n" + "=" * 80)
    print("测试Cloudflare IP段识别")
    print("=" * 80)
    
    detector = IPDetectorV2()
    
    # 测试已知的Cloudflare IP
    cf_ips = [
        '104.16.0.1',
        '104.24.0.1',
        '172.64.0.1',
        '162.159.0.1',
        '108.162.192.1',
        '198.41.128.1',
        '173.245.48.1',
    ]
    
    # 测试非Cloudflare IP
    non_cf_ips = [
        '8.8.8.8',
        '1.2.3.4',
        '192.168.1.1',
        '10.0.0.1',
    ]
    
    print("\nCloudflare IP段测试:")
    for ip in cf_ips:
        is_cf = detector.is_cloudflare_ip(ip)
        status = "✓" if is_cf else "✗"
        print(f"  {status} {ip}: {'Cloudflare' if is_cf else '非Cloudflare'}")
    
    print("\n非Cloudflare IP测试:")
    for ip in non_cf_ips:
        is_cf = detector.is_cloudflare_ip(ip)
        status = "✓" if not is_cf else "✗"
        print(f"  {status} {ip}: {'非Cloudflare' if not is_cf else 'Cloudflare'}")
    
    detector.close()


if __name__ == '__main__':
    try:
        # 测试IP段识别
        test_cf_ip_ranges()
        
        # 测试优先检测策略
        test_cf_priority()
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)