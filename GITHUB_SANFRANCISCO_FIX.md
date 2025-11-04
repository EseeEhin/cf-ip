# GitHub Actions环境中Cloudflare IP显示旧金山问题修复

## 问题描述

在GitHub Actions环境中运行时，所有Cloudflare IP的地理位置都显示为"San Francisco, US"（旧金山，美国），而本地运行时能正确识别实际的数据中心位置（如日本、香港等）。

## 问题根源

从日志分析发现：

```
2025-11-04 14:03:18 [WARNING] src.ip_detector_v2:208 - CF-RAY检测失败: 104.18.35.42:443，第三方API可能不准确
2025-11-04 14:03:18 [INFO] src.api_providers:468 - API查询成功: ipinfo -> 104.18.33.4
2025-11-04 14:03:18 [INFO] src.ip_detector_v2:341 - API检测成功: 104.18.33.4 -> San Francisco, US (来源: ipinfo)
2025-11-04 14:03:18 [WARNING] src.ip_detector_v2:214 - 使用第三方API检测CF IP: 104.18.33.4，结果可能不准确 -> San Francisco, US
```

**问题链条：**

1. CF-RAY检测在GitHub Actions环境中失败 - 可能由于网络限制或连接问题
2. 回退到第三方API（ipinfo.io）- 按照原有逻辑
3. ipinfo返回Cloudflare总部地址 - 对于Cloudflare的IP，ipinfo返回的是公司注册地址（旧金山），而不是实际的数据中心位置

## 解决方案

### 1. 改进CF-RAY检测成功率

修改 `src/cf_ray_detector.py`，使用多个Host头尝试连接，提高在不同网络环境下的成功率。

### 2. 修改Cloudflare IP的检测策略

对于Cloudflare IP，如果CF-RAY检测失败，直接使用GeoIP数据库，跳过第三方API（因为会返回旧金山）。

### 3. 调整API优先级

将IP-API.COM设为最高优先级，IPInfo.IO降为备用（因为对CF IP会返回旧金山）。

## 测试方法

运行测试脚本：

```bash
python test_cf_ray_fix.py
```

## 预期效果

修复后，即使CF-RAY检测失败，也会使用GeoIP数据库提供大致准确的位置，而不是固定返回旧金山。

## 相关文件

- `src/cf_ray_detector.py` - CF-RAY检测实现
- `src/ip_detector_v2.py` - IP检测主逻辑
- `test_cf_ray_fix.py` - 测试脚本