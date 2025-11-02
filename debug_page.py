import requests
import re

r = requests.get('https://cfip.wxgqlfx.fun/')
text = r.text

print('=== 查找script标签 ===')
scripts = re.findall(r'<script[^>]*>(.*?)</script>', text, re.DOTALL)
print(f'找到 {len(scripts)} 个script标签')

print('\n=== 查找API调用 ===')
apis = re.findall(r'(fetch|axios|XMLHttpRequest)\s*\([^)]*[\'\"](.*?)[\'\"]', text)
print(f'找到 {len(apis)} 个可能的API调用')
for api in apis[:5]:
    print(f'  - {api}')

print('\n=== 搜索IP模式 ===')
ips = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', text)
print(f'在HTML中找到 {len(ips)} 个IP:端口模式')
if ips:
    print('前5个:', ips[:5])

print('\n=== 查找div元素 ===')
from bs4 import BeautifulSoup
soup = BeautifulSoup(text, 'html.parser')
divs = soup.find_all('div')
print(f'找到 {len(divs)} 个div元素')

print('\n=== 查找包含class的div ===')
divs_with_class = soup.find_all('div', class_=True)
print(f'找到 {len(divs_with_class)} 个带class的div')
for div in divs_with_class[:10]:
    print(f'  - class: {div.get("class")}')

print('\n=== 保存HTML到文件 ===')
with open('debug_page.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('已保存到 debug_page.html')