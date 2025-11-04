#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试CF-RAY检测修复
"""

import sys
import logging
from src.cf_ray_detector import get_cloudflare_colo
from src.ip_detector_v2 import detect_ip_location

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_cf_ray_direct():
    """直接测试CF-RAY检测"""
    print("\n" + "="*60)
    print("测试CF-RAY检测（直接调用）")
    print("="*60)
    
    test_ips = [
        ('104.18.35.42', 443),
        ('104.17.48.0', 443),
        ('172.64.229.95', 443),
    ]
    
    for ip, port in test_ips:
        print(f"\n测试: {ip}:{port}")
        result = get_cloudflare_colo(ip, port, timeout=10)
        
        if result.get('success'):
            print(f"  ✓ 成功: {result['colo']} - {result['city']}, {result['country']}")
        else:
            print(f"  ✗ 失败")

def test_ip_detector():
    """测试完整的IP检测流程"""
    print("\n" + "="*60)
    print("测试完整IP检测流程")
    print("="*60)
    
    test_ips = [
        '104.18.35.42',   # Cloudflare IP
        '104.17.48.0',    # Cloudflare IP
        '8.8.8.8',        # Google DNS (非CF)
    ]
    
    for ip in test_ips:
        print(f"\n测试: {ip}")
        result = detect_ip_location(ip, 443)
        
        if result:
            print(f"  ✓ 成功")
            print(f"    国家: {result.get('country', 'Unknown')}")
            print(f"    城市: {result.get('city', 'Unknown')}")
            print(f"    来源: {result.get('source', 'Unknown')}")
            if 'colo' in result:
                print(f"    数据中心: {result.get('colo', '')}")
        else:
            print(f"  ✗ 失败")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("CF-RAY检测修复测试")
    print("="*60)
    
    # 测试1：直接CF-RAY检测
    test_cf_ray_direct()
    
    # 测试2：完整检测流程
    test_ip_detector()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)