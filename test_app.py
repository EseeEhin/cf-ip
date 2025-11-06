"""
本地测试脚本
用于在部署到Zeabur之前测试Web服务
"""
import os
import sys
import time
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 测试配置
BASE_URL = "http://localhost:8080"
TEST_TOKEN = os.getenv('TRIGGER_TOKEN', '')

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """测试健康检查接口"""
    print_section("测试健康检查接口")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_index():
    """测试首页接口"""
    print_section("测试首页接口")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"服务名称: {data.get('service')}")
        print(f"版本: {data.get('version')}")
        print(f"可用接口: {list(data.get('endpoints', {}).keys())}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_status():
    """测试状态接口"""
    print_section("测试状态接口")
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        
        task_status = data.get('task_status', {})
        print(f"\n任务状态:")
        print(f"  总运行次数: {task_status.get('total_runs')}")
        print(f"  成功次数: {task_status.get('success_runs')}")
        print(f"  失败次数: {task_status.get('failed_runs')}")
        print(f"  是否运行中: {task_status.get('is_running')}")
        print(f"  最后运行: {task_status.get('last_run')}")
        
        scheduler = data.get('scheduler', {})
        print(f"\n调度器状态:")
        print(f"  运行中: {scheduler.get('running')}")
        print(f"  定时任务数: {len(scheduler.get('jobs', []))}")
        
        for job in scheduler.get('jobs', []):
            print(f"    - {job.get('name')}: 下次运行 {job.get('next_run')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_config():
    """测试配置接口"""
    print_section("测试配置接口")
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        
        print(f"\n配置信息:")
        print(f"  过滤国家: {data.get('filter_countries')}")
        print(f"  查询限制: {data.get('query_limit')}")
        print(f"  最大延迟: {data.get('max_latency')}ms")
        print(f"  CF-RAY检测: {data.get('cf_ray_enabled')}")
        print(f"  定时任务: {data.get('schedule_enabled')}")
        print(f"  执行时间: {data.get('schedule_times')}")
        print(f"  GitHub仓库: {data.get('github_repo')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_trigger():
    """测试手动触发接口"""
    print_section("测试手动触发接口")
    
    # 询问用户是否要触发任务
    print("\n⚠️  警告: 此操作将触发IP更新任务")
    confirm = input("是否继续? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("已取消")
        return True
    
    try:
        headers = {}
        if TEST_TOKEN:
            headers['Authorization'] = f'Bearer {TEST_TOKEN}'
            print(f"使用认证Token: {TEST_TOKEN[:10]}...")
        
        response = requests.post(f"{BASE_URL}/trigger", headers=headers, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ 任务已触发,等待5秒后查看状态...")
            time.sleep(5)
            test_status()
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("  Zeabur部署测试脚本")
    print("🚀" * 30)
    
    print(f"\n测试目标: {BASE_URL}")
    print(f"认证Token: {'已配置' if TEST_TOKEN else '未配置'}")
    
    # 等待服务启动
    print("\n等待服务启动...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("✅ 服务已就绪")
            break
        except:
            print(f"等待中... ({i+1}/10)")
            time.sleep(2)
    else:
        print("❌ 服务未启动,请先运行: python app.py")
        return
    
    # 运行测试
    results = {
        '首页接口': test_index(),
        '健康检查': test_health(),
        '状态接口': test_status(),
        '配置接口': test_config(),
    }
    
    # 询问是否测试触发接口
    print("\n" + "=" * 60)
    test_trigger_confirm = input("是否测试手动触发接口? (y/N): ").strip().lower()
    if test_trigger_confirm == 'y':
        results['手动触发'] = test_trigger()
    
    # 输出测试结果
    print_section("测试结果汇总")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    print(f"\n总计: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过! 可以部署到Zeabur了!")
    else:
        print("\n⚠️  部分测试失败,请检查配置和日志")

if __name__ == '__main__':
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()