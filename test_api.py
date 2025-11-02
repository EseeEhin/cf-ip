import requests
import json

base_url = 'https://cfip.wxgqlfx.fun'

print('=== 测试 API 1: 获取国家列表 ===')
try:
    response = requests.get(f'{base_url}/api/countries', timeout=10)
    print(f'状态码: {response.status_code}')
    if response.ok:
        countries = response.json()
        print(f'国家数量: {len(countries)}')
        print('前5个国家:', countries[:5])
except Exception as e:
    print(f'错误: {e}')

print('\n=== 测试 API 2: 查询代理IP ===')
try:
    # 测试查询日本的代理
    payload = {
        'country': 'JP',
        'port': '',
        'limit': 5
    }
    response = requests.post(
        f'{base_url}/api/query',
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f'状态码: {response.status_code}')
    if response.ok:
        data = response.json()
        print(f'总代理数: {data.get("totalProxies", "未知")}')
        print(f'返回代理数: {len(data.get("proxies", []))}')
        if data.get('proxies'):
            print('前3个代理:')
            for proxy in data['proxies'][:3]:
                print(f'  - {proxy["ip"]}:{proxy["port"]} | {proxy.get("country", "?")} | {proxy.get("city", "?")}')
except Exception as e:
    print(f'错误: {e}')