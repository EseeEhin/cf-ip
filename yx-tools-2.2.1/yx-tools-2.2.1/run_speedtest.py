#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloudflare SpeedTest 非交互式包装脚本
用于 GitHub Actions 自动化运行
"""
import subprocess
import sys
import os


def run_speedtest(
    ip_version=1,
    function=2,
    airport_code="HKG",
    config=4,
    dn_count=30,
    time_limit=300,
    speed_limit=5
):
    """
    运行测速工具（非交互模式）
    
    Args:
        ip_version: IP版本 (1=IPv4, 2=IPv6)
        function: 功能选择 (1=小白快速测试, 2=常规测速, 3=优选反代)
        airport_code: 机场码（如 HKG, NRT, LAX）
        config: 配置选项 (1=快速, 2=标准, 3=高质量, 4=自定义)
        dn_count: 节点数量
        time_limit: 延迟上限（毫秒）
        speed_limit: 速度下限（MB/s）
    
    Returns:
        int: 返回码 (0=成功, 非0=失败)
    """
    # 准备输入数据
    inputs = [
        str(ip_version),  # IP版本：1=IPv4, 2=IPv6
        str(function),    # 功能：1=小白快速测试, 2=常规测速, 3=优选反代
    ]
    
    # 根据功能选择添加不同的输入
    if function == 1:
        # 小白快速测试模式
        inputs.extend([
            str(dn_count),      # 测试IP数量
            str(time_limit),    # 延迟上限
            str(speed_limit),   # 速度下限
        ])
    elif function == 2:
        # 常规测速模式
        # 注意：常规模式会先检测可用地区，然后让用户选择
        # 这里我们需要等待地区列表显示后再输入选择
        # 由于无法预知地区顺序，我们使用机场码匹配
        # 实际上常规模式需要交互，所以我们改用小白模式
        print("⚠️  常规测速模式需要交互式选择地区")
        print("⚠️  自动切换到小白快速测试模式")
        inputs[1] = "1"  # 改为小白模式
        inputs.extend([
            str(dn_count),      # 测试IP数量
            str(time_limit),    # 延迟上限
            str(speed_limit),   # 速度下限
        ])
    elif function == 3:
        # 优选反代模式
        inputs.extend([
            "result.csv",       # CSV文件路径
            "n",                # 不进行测速
        ])
    
    # 合并所有输入
    input_data = "\n".join(inputs) + "\n"
    
    print("=" * 70)
    print(" Cloudflare SpeedTest 自动化运行")
    print("=" * 70)
    print(f" IP版本: {'IPv4' if ip_version == 1 else 'IPv6'}")
    print(f" 功能模式: {'小白快速测试' if function == 1 else '常规测速' if function == 2 else '优选反代'}")
    if function in [1, 2]:
        print(f" 测试参数:")
        print(f"   - 节点数量: {dn_count}")
        print(f"   - 延迟上限: {time_limit} ms")
        print(f"   - 速度下限: {speed_limit} MB/s")
    print("=" * 70)
    print()
    
    try:
        # 运行测速工具
        result = subprocess.run(
            [sys.executable, "cloudflare_speedtest.py"],
            input=input_data,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600  # 10分钟超时
        )
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print(" ✅ 测速完成！")
            print("=" * 70)
            
            # 检查结果文件
            if os.path.exists("result.csv"):
                print(" 📊 结果文件: result.csv")
                
                # 显示前几行结果
                try:
                    with open("result.csv", "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            print(f" 📈 共找到 {len(lines) - 1} 个优选IP")
                            print("\n 前5个最优IP:")
                            for i, line in enumerate(lines[1:6], 1):
                                print(f"   {i}. {line.strip()}")
                except Exception as e:
                    print(f" ⚠️  读取结果文件时出错: {e}")
            else:
                print(" ⚠️  未找到结果文件 result.csv")
            
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print(f" ❌ 测速失败 (返回码: {result.returncode})")
            print("=" * 70)
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("\n" + "=" * 70)
        print(" ❌ 测速超时（10分钟）")
        print("=" * 70)
        return 1
    except FileNotFoundError:
        print("\n" + "=" * 70)
        print(" ❌ 未找到 cloudflare_speedtest.py 脚本")
        print(" 💡 请确保在正确的目录下运行此脚本")
        print("=" * 70)
        return 1
    except Exception as e:
        print("\n" + "=" * 70)
        print(f" ❌ 运行出错: {e}")
        print("=" * 70)
        return 1


def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Cloudflare SpeedTest 非交互式运行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用默认参数（IPv4，小白模式，30个节点，300ms延迟，5MB/s速度）
  python run_speedtest.py
  
  # 自定义参数
  python run_speedtest.py --dn-count 50 --time-limit 200 --speed-limit 10
  
  # 使用IPv6
  python run_speedtest.py --ip-version 2
  
  # 指定机场码（注意：常规模式需要交互，会自动切换到小白模式）
  python run_speedtest.py --airport-code NRT --dn-count 20
        """
    )
    
    parser.add_argument(
        '--ip-version',
        type=int,
        choices=[1, 2],
        default=1,
        help='IP版本：1=IPv4, 2=IPv6（默认：1）'
    )
    
    parser.add_argument(
        '--function',
        type=int,
        choices=[1, 2, 3],
        default=1,
        help='功能选择：1=小白快速测试, 2=常规测速, 3=优选反代（默认：1，推荐用于自动化）'
    )
    
    parser.add_argument(
        '--airport-code',
        type=str,
        default='HKG',
        help='机场码（如：HKG, NRT, LAX）（默认：HKG）'
    )
    
    parser.add_argument(
        '--config',
        type=int,
        choices=[1, 2, 3, 4],
        default=4,
        help='配置：1=快速, 2=标准, 3=高质量, 4=自定义（默认：4）'
    )
    
    parser.add_argument(
        '--dn-count',
        type=int,
        default=30,
        help='下载节点数量（默认：30）'
    )
    
    parser.add_argument(
        '--time-limit',
        type=int,
        default=300,
        help='延迟上限（毫秒，默认：300）'
    )
    
    parser.add_argument(
        '--speed-limit',
        type=int,
        default=5,
        help='速度下限（MB/s，默认：5）'
    )
    
    args = parser.parse_args()
    
    # 运行测速
    exit_code = run_speedtest(
        ip_version=args.ip_version,
        function=args.function,
        airport_code=args.airport_code,
        config=args.config,
        dn_count=args.dn_count,
        time_limit=args.time_limit,
        speed_limit=args.speed_limit
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()