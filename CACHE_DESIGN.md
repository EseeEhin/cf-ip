# IP地理位置缓存设计方案

## 问题分析

### 当前限制
- **API限制**：ip-api.com 免费版每分钟45次请求
- **节点数量**：3个数据源，每个可能有几十到上百个IP
- **更新频率**：每天3次自动更新

### 计算示例
```
来源A：10个IP（JP） + 10个IP（HK） + 10个IP（US） = 30个
来源B：假设50个IP
来源C：假设50个IP
总计：约130个IP需要查询地理位置
```

如果每次都查询，会超过45次/分钟的限制。

## 🎯 缓存设计方案

### 方案：本地JSON文件缓存 + 智能更新

#### 1. 缓存结构

```json
{
  "cache_version": "1.0",
  "last_updated": "2025-11-02T15:30:00",
  "ips": {
    "172.64.229.95": {
      "country": "US",
      "country_name": "United States",
      "city": "Los Angeles",
      "cached_at": "2025-11-02T15:30:00",
      "query_count": 1
    },
    "162.159.45.47": {
      "country": "US",
      "country_name": "United States", 
      "city": "San Francisco",
      "cached_at": "2025-11-02T14:20:00",
      "query_count": 3
    }
  }
}
```

#### 2. 缓存策略

**缓存有效期**：
- ✅ **30天**：IP地理位置相对稳定，30天内不会变化
- 🔄 超过30天的缓存自动失效，重新查询

**查询逻辑**：
```python
def get_ip_location(ip):
    # 1. 检查缓存
    if ip in cache and not is_expired(cache[ip]):
        return cache[ip]  # 命中缓存，直接返回
    
    # 2. 缓存未命中或已过期，查询API
    location = query_api(ip)
    
    # 3. 更新缓存
    cache[ip] = location
    save_cache()
    
    return location
```

**批量处理优化**：
```python
def process_ips_batch(ip_list):
    results = []
    uncached_ips = []
    
    # 第一步：从缓存获取
    for ip in ip_list:
        if ip in cache and not is_expired(cache[ip]):
            results.append(cache[ip])
        else:
            uncached_ips.append(ip)
    
    # 第二步：批量查询未缓存的IP（控制速率）
    for ip in uncached_ips:
        location = query_api_with_rate_limit(ip)
        results.append(location)
        cache[ip] = location
    
    save_cache()
    return results
```

#### 3. 速率限制控制

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=45, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window  # 秒
        self.requests = deque()
    
    def wait_if_needed(self):
        now = time.time()
        
        # 移除时间窗口外的请求记录
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # 如果达到限制，等待
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time + 1)
                self.requests.clear()
        
        # 记录本次请求
        self.requests.append(time.time())
```

#### 4. 缓存文件管理

**文件位置**：`cache/ip_location_cache.json`

**缓存操作**：
```python
import json
from datetime import datetime, timedelta

class IPLocationCache:
    def __init__(self, cache_file='cache/ip_location_cache.json'):
        self.cache_file = cache_file
        self.cache = self.load_cache()
        self.cache_days = 30  # 缓存有效期30天
    
    def load_cache(self):
        """加载缓存文件"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'cache_version': '1.0', 'ips': {}}
    
    def save_cache(self):
        """保存缓存到文件"""
        self.cache['last_updated'] = datetime.now().isoformat()
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def get(self, ip):
        """获取IP的地理位置（从缓存）"""
        if ip not in self.cache['ips']:
            return None
        
        cached_data = self.cache['ips'][ip]
        cached_time = datetime.fromisoformat(cached_data['cached_at'])
        
        # 检查是否过期
        if datetime.now() - cached_time > timedelta(days=self.cache_days):
            return None  # 缓存过期
        
        return cached_data
    
    def set(self, ip, location_data):
        """设置IP的地理位置到缓存"""
        self.cache['ips'][ip] = {
            **location_data,
            'cached_at': datetime.now().isoformat(),
            'query_count': self.cache['ips'].get(ip, {}).get('query_count', 0) + 1
        }
        self.save_cache()
    
    def cleanup_expired(self):
        """清理过期的缓存"""
        now = datetime.now()
        expired_ips = []
        
        for ip, data in self.cache['ips'].items():
            cached_time = datetime.fromisoformat(data['cached_at'])
            if now - cached_time > timedelta(days=self.cache_days):
                expired_ips.append(ip)
        
        for ip in expired_ips:
            del self.cache['ips'][ip]
        
        if expired_ips:
            self.save_cache()
        
        return len(expired_ips)
```

## 📊 性能优化效果

### 首次运行（无缓存）
```
总IP数：130个
API查询：130次
耗时：约3分钟（控制速率）
```

### 后续运行（有缓存）
```
总IP数：130个
缓存命中：约120个（92%）
API查询：约10个（新IP）
耗时：约15秒
```

### 缓存命中率预估
- **第1次运行**：0%（全部查询）
- **第2次运行**：90%+（大部分IP重复）
- **稳定运行**：95%+（只有少量新IP）

## 🔧 实现要点

### 1. 目录结构
```
clash-cf-updater/
├── cache/
│   ├── .gitkeep
│   └── ip_location_cache.json  # 缓存文件
├── src/
│   ├── ip_location.py          # 新增：IP地理位置查询模块
│   └── ...
```

### 2. .gitignore 更新
```
# 缓存文件
cache/*.json
!cache/.gitkeep
```

### 3. 配置项
```python
# 在 config.py 中添加
cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
cache_days = int(os.getenv('CACHE_DAYS', '30'))
api_rate_limit = int(os.getenv('API_RATE_LIMIT', '40'))  # 留5个余量
```

## 🎯 最终方案总结

### 优势
1. ✅ **大幅减少API调用**：缓存命中率95%+
2. ✅ **提升运行速度**：从3分钟降到15秒
3. ✅ **避免速率限制**：智能控制请求频率
4. ✅ **降低网络依赖**：大部分数据从本地读取
5. ✅ **数据持久化**：缓存文件可以提交到仓库（可选）

### 实现步骤
1. 创建 `src/ip_location.py` 模块
2. 实现 `IPLocationCache` 类
3. 实现 `RateLimiter` 类
4. 集成到现有的数据获取流程
5. 添加缓存管理命令（清理、统计等）

### 使用示例
```python
from src.ip_location import get_ip_location_with_cache

# 自动使用缓存
location = get_ip_location_with_cache('172.64.229.95')
# 返回：{'country': 'US', 'city': 'Los Angeles'}
```

这个方案可以完美解决API限制问题，你觉得如何？