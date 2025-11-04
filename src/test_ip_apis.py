#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP归属地查询API接口测试脚本

测试多个IP归属地查询API接口对Cloudflare节点IP的检测效果
"""

import requests
import time
import json
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime


@dataclass
class APITestResult:
    """API测试结果数据类"""
    api_name: str
    success: bool
    response_time: float
    status_code: Optional[int]
    country: str
    province: str
    city: str
    isp: str
    error_msg: str
    raw_data: Optional[dict]


class IPAPITester:
    """IP归属地API测试器"""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def load_test_ips(self, filepath: str = 'optimal-ips.txt', limit: int = 10) -> List[str]:
        """
        从文件中加载测试IP地址
        
        Args:
            filepath: IP文件路径
            limit: 限制加载的IP数量
            
        Returns:
            IP地址列表
        """
        ips = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 提取IP地址（格式：IP:端口#标签）
                        ip = line.split(':')[0]
                        if ip and ip not in ips:
                            ips.append(ip)
                        if len(ips) >= limit:
                            break
        except FileNotFoundError:
            print(f"❌ 文件未找到: {filepath}")
        except Exception as e:
            print(f"❌ 读取文件出错: {e}")
        
        return ips
    
    def test_baidu_api(self, ip: str) -> APITestResult:
        """测试百度IP地址归属地查询API"""
        api_name = "百度API"
        url = f"http://opendata.baidu.com/api.php?query={ip}&co=&resource_id=6006&oe=utf8"
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '0' and 'data' in data and len(data['data']) > 0:
                    info = data['data'][0]
                    location = info.get('location', '')
                    # 解析位置信息
                    parts = location.split()
                    country = parts[0] if len(parts) > 0 else ''
                    province = parts[1] if len(parts) > 1 else ''
                    city = parts[2] if len(parts) > 2 else ''
                    
                    return APITestResult(
                        api_name=api_name,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        country=country,
                        province=province,
                        city=city,
                        isp='',
                        error_msg='',
                        raw_data=data
                    )
            
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=response_time,
                status_code=response.status_code,
                country='', province='', city='', isp='',
                error_msg=f"状态码: {response.status_code}",
                raw_data=None
            )
            
        except Exception as e:
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=0,
                status_code=None,
                country='', province='', city='', isp='',
                error_msg=str(e),
                raw_data=None
            )
    
    def test_pconline_api(self, ip: str) -> APITestResult:
        """测试太平洋IP地址归属地查询API"""
        api_name = "太平洋API"
        url = f"http://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true"
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # 设置正确的编码
                response.encoding = 'gbk'
                data = response.json()
                
                return APITestResult(
                    api_name=api_name,
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    country=data.get('pro', ''),
                    province=data.get('city', ''),
                    city=data.get('region', ''),
                    isp=data.get('addr', ''),
                    error_msg='',
                    raw_data=data
                )
            
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=response_time,
                status_code=response.status_code,
                country='', province='', city='', isp='',
                error_msg=f"状态码: {response.status_code}",
                raw_data=None
            )
            
        except Exception as e:
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=0,
                status_code=None,
                country='', province='', city='', isp='',
                error_msg=str(e),
                raw_data=None
            )
    
    def test_ipcn_api(self, ip: str) -> APITestResult:
        """测试www.ip.cn API"""
        api_name = "IP.CN API"
        url = f"https://www.ip.cn/api/index?ip={ip}&type=0"
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', '')
                
                return APITestResult(
                    api_name=api_name,
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    country='',
                    province='',
                    city='',
                    isp=address,
                    error_msg='',
                    raw_data=data
                )
            
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=response_time,
                status_code=response.status_code,
                country='', province='', city='', isp='',
                error_msg=f"状态码: {response.status_code}",
                raw_data=None
            )
            
        except Exception as e:
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=0,
                status_code=None,
                country='', province='', city='', isp='',
                error_msg=str(e),
                raw_data=None
            )
    
    def test_ipapi_com(self, ip: str) -> APITestResult:
        """测试ip-api.com API"""
        api_name = "IP-API.COM"
        url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    return APITestResult(
                        api_name=api_name,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        country=data.get('country', ''),
                        province=data.get('regionName', ''),
                        city=data.get('city', ''),
                        isp=data.get('isp', ''),
                        error_msg='',
                        raw_data=data
                    )
            
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=response_time,
                status_code=response.status_code,
                country='', province='', city='', isp='',
                error_msg=data.get('message', f"状态码: {response.status_code}"),
                raw_data=None
            )
            
        except Exception as e:
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=0,
                status_code=None,
                country='', province='', city='', isp='',
                error_msg=str(e),
                raw_data=None
            )
    
    def test_csdn_api(self, ip: str) -> APITestResult:
        """测试CSDN API"""
        api_name = "CSDN API"
        url = f"https://searchplugin.csdn.net/api/v1/ip/get?ip={ip}"
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 200:
                    info = data.get('data', {})
                    address = info.get('address', '')
                    
                    return APITestResult(
                        api_name=api_name,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        country='',
                        province='',
                        city='',
                        isp=address,
                        error_msg='',
                        raw_data=data
                    )
            
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=response_time,
                status_code=response.status_code,
                country='', province='', city='', isp='',
                error_msg=f"状态码: {response.status_code}",
                raw_data=None
            )
            
        except Exception as e:
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=0,
                status_code=None,
                country='', province='', city='', isp='',
                error_msg=str(e),
                raw_data=None
            )
    
    def test_useragentinfo_api(self, ip: str) -> APITestResult:
        """测试ip.useragentinfo.com API"""
        api_name = "UserAgentInfo"
        url = f"https://ip.useragentinfo.com/json?ip={ip}"
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                return APITestResult(
                    api_name=api_name,
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    country=data.get('country', ''),
                    province=data.get('province', ''),
                    city=data.get('city', ''),
                    isp=data.get('isp', ''),
                    error_msg='',
                    raw_data=data
                )
            
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=response_time,
                status_code=response.status_code,
                country='', province='', city='', isp='',
                error_msg=f"状态码: {response.status_code}",
                raw_data=None
            )
            
        except Exception as e:
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=0,
                status_code=None,
                country='', province='', city='', isp='',
                error_msg=str(e),
                raw_data=None
            )
    
    def test_ping0cc_api(self, ip: str) -> APITestResult:
        """测试ping0.cc API（通过X-Forwarded-For header传递IP）"""
        api_name = "Ping0.CC"
        url = "https://ping0.cc/geo"
        
        try:
            headers = self.headers.copy()
            headers['X-Forwarded-For'] = ip
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                return APITestResult(
                    api_name=api_name,
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    country=data.get('country', ''),
                    province=data.get('region', ''),
                    city=data.get('city', ''),
                    isp=data.get('isp', ''),
                    error_msg='',
                    raw_data=data
                )
            
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=response_time,
                status_code=response.status_code,
                country='', province='', city='', isp='',
                error_msg=f"状态码: {response.status_code}",
                raw_data=None
            )
            
        except Exception as e:
            return APITestResult(
                api_name=api_name,
                success=False,
                response_time=0,
                status_code=None,
                country='', province='', city='', isp='',
                error_msg=str(e),
                raw_data=None
            )
    
    def test_all_apis(self, ip: str) -> List[APITestResult]:
        """测试所有API接口"""
        results = []
        
        # 按顺序测试每个API
        results.append(self.test_baidu_api(ip))
        results.append(self.test_pconline_api(ip))
        results.append(self.test_ipcn_api(ip))
        results.append(self.test_ipapi_com(ip))
        results.append(self.test_csdn_api(ip))
        results.append(self.test_useragentinfo_api(ip))
        results.append(self.test_ping0cc_api(ip))
        
        return results
    
    def print_result_table(self, ip: str, results: List[APITestResult]):
        """打印单个IP的测试结果表格"""
        print(f"\n测试IP: {ip}")
        print("━" * 120)
        print(f"{'API接口':<18} | {'状态':<4} | {'响应时间':<8} | {'国家':<12} | {'省份/州':<12} | {'城市':<12} | {'ISP/备注':<20}")
        print("━" * 120)
        
        for result in results:
            status = "✓" if result.success else "✗"
            response_time = f"{result.response_time:.2f}s" if result.success else "N/A"
            
            # 检测是否识别为Cloudflare
            is_cf = False
            cf_keywords = ['cloudflare', 'cf', 'cloud flare']
            check_fields = [result.country, result.province, result.city, result.isp]
            for field in check_fields:
                if field and any(keyword in field.lower() for keyword in cf_keywords):
                    is_cf = True
                    break
            
            note = result.isp if result.isp else ''
            if is_cf:
                note = f"🎯 {note}" if note else "🎯 识别为Cloudflare"
            elif not result.success:
                note = result.error_msg[:20] if result.error_msg else ''
            
            print(f"{result.api_name:<18} | {status:<4} | {response_time:<8} | "
                  f"{result.country:<12} | {result.province:<12} | {result.city:<12} | {note:<20}")
        
        print("━" * 120)
    
    def generate_summary_report(self, all_results: Dict[str, List[APITestResult]]):
        """生成汇总报告"""
        print("\n" + "=" * 120)
        print("测试汇总报告".center(120))
        print("=" * 120)
        
        # 统计每个API的成功率和平均响应时间
        api_stats = {}
        
        for ip, results in all_results.items():
            for result in results:
                if result.api_name not in api_stats:
                    api_stats[result.api_name] = {
                        'total': 0,
                        'success': 0,
                        'response_times': [],
                        'cf_detected': 0
                    }
                
                api_stats[result.api_name]['total'] += 1
                if result.success:
                    api_stats[result.api_name]['success'] += 1
                    api_stats[result.api_name]['response_times'].append(result.response_time)
                    
                    # 检测是否识别为Cloudflare
                    cf_keywords = ['cloudflare', 'cf', 'cloud flare']
                    check_fields = [result.country, result.province, result.city, result.isp]
                    for field in check_fields:
                        if field and any(keyword in field.lower() for keyword in cf_keywords):
                            api_stats[result.api_name]['cf_detected'] += 1
                            break
        
        # 打印统计表格
        print(f"\n{'API接口':<18} | {'成功率':<10} | {'平均响应时间':<12} | {'CF识别率':<10} | {'推荐度':<8}")
        print("━" * 120)
        
        recommendations = []
        
        for api_name, stats in sorted(api_stats.items(), key=lambda x: x[1]['success'], reverse=True):
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_response_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
            cf_rate = (stats['cf_detected'] / stats['success'] * 100) if stats['success'] > 0 else 0
            
            # 计算推荐度（基于成功率、响应时间和CF识别率）
            if success_rate >= 80 and avg_response_time < 2.0:
                recommendation = "⭐⭐⭐"
            elif success_rate >= 60 and avg_response_time < 3.0:
                recommendation = "⭐⭐"
            elif success_rate >= 40:
                recommendation = "⭐"
            else:
                recommendation = ""
            
            if recommendation:
                recommendations.append((api_name, success_rate, avg_response_time, cf_rate))
            
            print(f"{api_name:<18} | {success_rate:>6.1f}%   | {avg_response_time:>8.2f}s    | "
                  f"{cf_rate:>6.1f}%   | {recommendation:<8}")
        
        print("━" * 120)
        
        # 推荐使用的API
        if recommendations:
            print("\n推荐使用的API接口（按优先级排序）：")
            for i, (api_name, success_rate, avg_time, cf_rate) in enumerate(recommendations, 1):
                print(f"  {i}. {api_name} - 成功率: {success_rate:.1f}%, 平均响应: {avg_time:.2f}s, CF识别率: {cf_rate:.1f}%")
        
        print("\n" + "=" * 120)
        print(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 120)


def main():
    """主函数"""
    print("=" * 120)
    print("IP归属地查询API接口测试工具".center(120))
    print("=" * 120)
    
    # 创建测试器实例
    tester = IPAPITester(timeout=5)
    
    # 加载测试IP（默认取前10个）
    print("\n正在加载测试IP...")
    test_ips = tester.load_test_ips('optimal-ips.txt', limit=10)
    
    if not test_ips:
        print("❌ 未能加载任何测试IP，请检查optimal-ips.txt文件是否存在")
        return
    
    print(f"✓ 已加载 {len(test_ips)} 个测试IP")
    print(f"测试IP列表: {', '.join(test_ips[:5])}{'...' if len(test_ips) > 5 else ''}")
    
    # 测试所有IP
    all_results = {}
    
    for i, ip in enumerate(test_ips, 1):
        print(f"\n[{i}/{len(test_ips)}] 正在测试 {ip}...")
        results = tester.test_all_apis(ip)
        all_results[ip] = results
        tester.print_result_table(ip, results)
        
        # 避免请求过快，稍作延迟
        if i < len(test_ips):
            time.sleep(0.5)
    
    # 生成汇总报告
    tester.generate_summary_report(all_results)


if __name__ == '__main__':
    main()