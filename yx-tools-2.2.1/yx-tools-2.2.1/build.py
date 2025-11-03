#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动打包脚本
用于将 Python 脚本打包成各平台的可执行文件
"""

import os
import sys
import platform
import subprocess

def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装（版本: {PyInstaller.__version__}）")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        return False

def install_pyinstaller():
    """安装 PyInstaller"""
    print("\n正在安装 PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller 安装成功")
        return True
    except subprocess.CalledProcessError:
        print("✗ PyInstaller 安装失败")
        return False

def build_executable():
    """打包可执行文件"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # 确定输出文件名
    if system == "darwin":
        os_name = "macos"
    elif system == "linux":
        os_name = "linux"
    elif system == "windows":
        os_name = "windows"
    else:
        os_name = system
    
    if machine in ["x86_64", "amd64", "x64"]:
        arch = "amd64"
    elif machine in ["arm64", "aarch64"]:
        arch = "arm64"
    else:
        arch = machine
    
    output_name = f"CloudflareSpeedTest-{os_name}-{arch}"
    
    print(f"\n开始打包...")
    print(f"目标系统: {os_name}")
    print(f"目标架构: {arch}")
    print(f"输出文件: {output_name}")
    print("-" * 60)
    
    # PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--onefile",                    # 打包成单个文件
        "--name", output_name,          # 输出文件名
        "--clean",                      # 清理临时文件
        "--noconfirm",                  # 不询问覆盖
        "--strip",                      # 去除调试符号（减小体积）
        "--optimize", "2",              # 优化级别
        "--console",                    # 控制台程序
        "cloudflare_speedtest.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 60)
        print(f"✓ 打包成功！")
        print(f"可执行文件位置: dist/{output_name}")
        print("=" * 60)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Cloudflare SpeedTest 可执行文件打包工具")
    print("=" * 60)
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        choice = input("\n是否安装 PyInstaller? [Y/n]: ").strip().lower()
        if choice in ['', 'y', 'yes']:
            if not install_pyinstaller():
                print("\n请手动安装: pip install pyinstaller")
                return 1
        else:
            print("\n取消打包")
            return 1
    
    # 打包
    if build_executable():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

