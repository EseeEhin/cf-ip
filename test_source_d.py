"""
测试来源D功能
"""
import logging
from src.multi_source_fetcher import SourceD

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_source_d():
    """测试来源D"""
    print("=" * 60)
    print("测试来源D (ipdb.api.030101.xyz)")
    print("=" * 60)
    
    source_d = SourceD()
    print(f"\n数据源名称: {source_d.name}")
    print(f"数据源前缀: {source_d.prefix}")
    print(f"BestProxy URL: {source_d.bestproxy_url}")
    print(f"BestCF URL: {source_d.bestcf_url}")
    print(f"启用BestProxy: {source_d.enable_bestproxy}")
    print(f"启用BestCF: {source_d.enable_bestcf}")
    
    print("\n开始获取数据...")
    nodes = source_d.fetch(countries=['JP', 'HK', 'US'])
    
    print(f"\n获取到 {len(nodes)} 个节点")
    
    # 统计节点类型
    proxy_nodes = [n for n in nodes if n.get('type') == 'proxy']
    cf_nodes = [n for n in nodes if n.get('type') == 'cf']
    
    print(f"  - Proxy节点: {len(proxy_nodes)}")
    print(f"  - CF节点: {len(cf_nodes)}")
    
    # 显示前5个节点
    if nodes:
        print("\n前5个节点示例:")
        for i, node in enumerate(nodes[:5], 1):
            node_type = node.get('type', '')
            type_label = '[Proxy]' if node_type == 'proxy' else '[CF]' if node_type == 'cf' else ''
            print(f"  {i}. {node['ip']}:{node['port']}#{node['source']}-{node['country']} {type_label}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_source_d()