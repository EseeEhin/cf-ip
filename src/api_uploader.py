#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优选IP API上传模块
直接通过API将优选IP写入到订阅项目的管理后台
"""

import requests
import json
from typing import List, Dict, Optional
from config import (
    SUBSCRIPTION_API_URL,
    SUBSCRIPTION_API_PATH,
    API_TIMEOUT
)


class APIUploader:
    """API上传器"""
    
    def __init__(self, api_url: str = None, api_path: str = None):
        """
        初始化API上传器
        
        Args:
            api_url: 订阅项目的基础URL (例如: https://your-worker.workers.dev)
            api_path: API路径 (例如: /your-uuid 或 /your-custom-path)
        """
        self.api_url = api_url or SUBSCRIPTION_API_URL
        self.api_path = api_path or SUBSCRIPTION_API_PATH
        
        if not self.api_url:
            raise ValueError("必须提供订阅项目的URL (SUBSCRIPTION_API_URL)")
        if not self.api_path:
            raise ValueError("必须提供API路径 (SUBSCRIPTION_API_PATH)")
        
        # 构建完整的API端点
        self.api_endpoint = f"{self.api_url.rstrip('/')}{self.api_path}/api/preferred-ips"
        
        print(f"[API上传器] 初始化完成")
        print(f"[API上传器] API端点: {self.api_endpoint}")
    
    def get_current_ips(self) -> Optional[List[Dict]]:
        """
        获取当前的优选IP列表
        
        Returns:
            优选IP列表，失败返回None
        """
        try:
            print(f"[API上传器] 正在获取当前优选IP列表...")
            response = requests.get(
                self.api_endpoint,
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    ips = data.get('data', [])
                    print(f"[API上传器] 成功获取 {len(ips)} 个优选IP")
                    return ips
                else:
                    print(f"[API上传器] 获取失败: {data.get('error', '未知错误')}")
                    return None
            elif response.status_code == 403:
                print(f"[API上传器] ⚠️ API功能未启用，请在配置管理页面开启'允许API管理'选项")
                return None
            elif response.status_code == 503:
                print(f"[API上传器] ⚠️ KV存储未配置")
                return None
            else:
                print(f"[API上传器] 获取失败，状态码: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"[API上传器] ❌ 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[API上传器] ❌ 请求失败: {e}")
            return None
        except Exception as e:
            print(f"[API上传器] ❌ 获取失败: {e}")
            return None
    
    def add_ips(self, ips: List[Dict]) -> bool:
        """
        添加优选IP到订阅项目
        
        Args:
            ips: IP列表，每个IP是一个字典，包含:
                - ip: IP地址或域名 (必需)
                - port: 端口号 (可选，默认443)
                - name: 节点名称 (可选)
        
        Returns:
            是否成功
        """
        if not ips:
            print(f"[API上传器] ⚠️ IP列表为空，跳过上传")
            return False
        
        try:
            print(f"[API上传器] 正在上传 {len(ips)} 个优选IP...")
            
            response = requests.post(
                self.api_endpoint,
                json=ips,
                headers={'Content-Type': 'application/json'},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    added = data.get('added', 0)
                    skipped = data.get('skipped', 0)
                    errors = data.get('errors', 0)
                    
                    print(f"[API上传器] ✅ 上传成功!")
                    print(f"[API上传器]    - 成功添加: {added} 个")
                    if skipped > 0:
                        print(f"[API上传器]    - 跳过重复: {skipped} 个")
                    if errors > 0:
                        print(f"[API上传器]    - 错误: {errors} 个")
                    
                    # 显示详细信息
                    if 'data' in data:
                        if 'addedIPs' in data['data'] and data['data']['addedIPs']:
                            print(f"[API上传器] 新添加的IP:")
                            for ip_info in data['data']['addedIPs'][:5]:  # 只显示前5个
                                print(f"[API上传器]    - {ip_info['ip']}:{ip_info['port']} ({ip_info['name']})")
                            if len(data['data']['addedIPs']) > 5:
                                print(f"[API上传器]    ... 还有 {len(data['data']['addedIPs']) - 5} 个")
                    
                    return True
                else:
                    print(f"[API上传器] ❌ 上传失败: {data.get('message', '未知错误')}")
                    return False
            elif response.status_code == 403:
                print(f"[API上传器] ❌ API功能未启用")
                print(f"[API上传器] 请在订阅项目的配置管理页面:")
                print(f"[API上传器] 1. 找到'高级控制'部分")
                print(f"[API上传器] 2. 将'允许API管理 (ae)'设置为'开启API管理'")
                print(f"[API上传器] 3. 保存配置")
                return False
            elif response.status_code == 503:
                print(f"[API上传器] ❌ KV存储未配置")
                print(f"[API上传器] 请在Cloudflare Workers中:")
                print(f"[API上传器] 1. 创建KV命名空间")
                print(f"[API上传器] 2. 绑定环境变量 C")
                print(f"[API上传器] 3. 重新部署代码")
                return False
            else:
                print(f"[API上传器] ❌ 上传失败，状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"[API上传器] 错误信息: {error_data.get('message', '未知错误')}")
                except:
                    print(f"[API上传器] 响应内容: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"[API上传器] ❌ 请求超时")
            return False
        except requests.exceptions.RequestException as e:
            print(f"[API上传器] ❌ 请求失败: {e}")
            return False
        except Exception as e:
            print(f"[API上传器] ❌ 上传失败: {e}")
            return False
    
    def delete_ip(self, ip: str, port: int = 443) -> bool:
        """
        删除指定的优选IP
        
        Args:
            ip: IP地址
            port: 端口号
        
        Returns:
            是否成功
        """
        try:
            print(f"[API上传器] 正在删除 {ip}:{port}...")
            
            response = requests.delete(
                self.api_endpoint,
                json={'ip': ip, 'port': port},
                headers={'Content-Type': 'application/json'},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"[API上传器] ✅ 删除成功")
                    return True
                else:
                    print(f"[API上传器] ❌ 删除失败: {data.get('message', '未知错误')}")
                    return False
            else:
                print(f"[API上传器] ❌ 删除失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[API上传器] ❌ 删除失败: {e}")
            return False
    
    def clear_all_ips(self) -> bool:
        """
        清空所有优选IP
        
        Returns:
            是否成功
        """
        try:
            print(f"[API上传器] 正在清空所有优选IP...")
            
            response = requests.delete(
                self.api_endpoint,
                json={'all': True},
                headers={'Content-Type': 'application/json'},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    deleted_count = data.get('deletedCount', 0)
                    print(f"[API上传器] ✅ 清空成功，共删除 {deleted_count} 个IP")
                    return True
                else:
                    print(f"[API上传器] ❌ 清空失败: {data.get('message', '未知错误')}")
                    return False
            else:
                print(f"[API上传器] ❌ 清空失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[API上传器] ❌ 清空失败: {e}")
            return False


def format_ips_for_api(ip_list: List[Dict]) -> List[Dict]:
    """
    将IP列表格式化为API所需的格式
    
    Args:
        ip_list: 原始IP列表
    
    Returns:
        格式化后的IP列表
    """
    formatted_ips = []
    
    for item in ip_list:
        # 提取IP和端口
        if ':' in item.get('ip', ''):
            ip_parts = item['ip'].rsplit(':', 1)
            ip = ip_parts[0]
            port = int(ip_parts[1]) if len(ip_parts) > 1 else 443
        else:
            ip = item.get('ip', '')
            port = item.get('port', 443)
        
        # 构建节点名称
        name = item.get('isp') or item.get('name') or f"{ip}:{port}"
        
        formatted_ips.append({
            'ip': ip,
            'port': port,
            'name': name
        })
    
    return formatted_ips


if __name__ == '__main__':
    # 测试代码
    print("=" * 60)
    print("优选IP API上传器 - 测试模式")
    print("=" * 60)
    
    # 检查配置
    if not SUBSCRIPTION_API_URL or not SUBSCRIPTION_API_PATH:
        print("\n⚠️ 请先配置环境变量:")
        print("   SUBSCRIPTION_API_URL=https://your-worker.workers.dev")
        print("   SUBSCRIPTION_API_PATH=/your-uuid-or-path")
        exit(1)
    
    try:
        uploader = APIUploader()
        
        # 获取当前IP列表
        print("\n1. 获取当前优选IP列表")
        print("-" * 60)
        current_ips = uploader.get_current_ips()
        
        if current_ips is not None:
            if current_ips:
                print(f"\n当前有 {len(current_ips)} 个优选IP:")
                for ip_info in current_ips[:5]:
                    print(f"  - {ip_info['ip']}:{ip_info['port']} ({ip_info['name']})")
                if len(current_ips) > 5:
                    print(f"  ... 还有 {len(current_ips) - 5} 个")
            else:
                print("\n当前没有优选IP")
        
        # 测试添加IP
        print("\n2. 测试添加优选IP")
        print("-" * 60)
        test_ips = [
            {'ip': '104.17.48.0', 'port': 443, 'name': '测试节点1-美国'},
            {'ip': '104.18.35.42', 'port': 443, 'name': '测试节点2-美国'}
        ]
        
        success = uploader.add_ips(test_ips)
        
        if success:
            print("\n✅ API上传测试成功!")
        else:
            print("\n❌ API上传测试失败")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()