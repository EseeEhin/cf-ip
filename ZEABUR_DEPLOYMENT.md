# Zeabur 部署指南

本指南将帮助你将Cloudflare优选IP自动更新系统部署到Zeabur平台。

## 📋 目录

- [部署前准备](#部署前准备)
- [快速部署](#快速部署)
- [环境变量配置](#环境变量配置)
- [定时任务配置](#定时任务配置)
- [API接口说明](#api接口说明)
- [常见问题](#常见问题)

---

## 🚀 部署前准备

### 1. 注册Zeabur账号

访问 [Zeabur官网](https://zeabur.com) 注册账号并登录。

### 2. 准备GitHub仓库

确保你的项目已经推送到GitHub仓库,包含以下文件:
- ✅ `app.py` - Web服务入口
- ✅ `requirements.txt` - Python依赖
- ✅ `zbpack.json` - Zeabur配置
- ✅ `src/` - 源代码目录
- ✅ `.env.example` - 环境变量示例

---

## 🎯 快速部署

### 步骤1: 创建新项目

1. 登录Zeabur控制台
2. 点击 **"New Project"** 创建新项目
3. 输入项目名称,如: `cf-ip-updater`

### 步骤2: 添加服务

1. 在项目中点击 **"Add Service"**
2. 选择 **"Git"** 
3. 授权并选择你的GitHub仓库
4. 选择分支(通常是 `main` 或 `master`)

### 步骤3: 配置环境变量

在服务设置中添加以下环境变量:

#### 必需配置

```bash
# 过滤国家(逗号分隔)
FILTER_COUNTRIES=JP,HK,US

# 每个国家查询数量
QUERY_LIMIT=20

# 最大延迟(毫秒)
MAX_LATENCY=100
```

#### 定时任务配置

```bash
# 是否启用定时任务(默认: true)
SCHEDULE_ENABLED=true

# 定时执行时间(北京时间,逗号分隔)
# 默认: 每天8:00, 14:00, 20:00
SCHEDULE_TIMES=8:00,14:00,20:00

# 是否在启动时立即执行一次(默认: false)
RUN_ON_STARTUP=true
```

#### GitHub上传配置(可选)

```bash
# GitHub Personal Access Token
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# GitHub仓库(格式: username/repo)
GITHUB_REPO=your-username/your-repo

# GitHub分支
GITHUB_BRANCH=main

# 文件路径
GITHUB_FILE_PATH=optimal-ips.txt
```

#### 订阅项目API配置(可选)

```bash
# 订阅项目Workers URL
SUBSCRIPTION_API_URL=https://your-worker.workers.dev

# API路径
SUBSCRIPTION_API_PATH=/your-uuid-path

# 是否启用API上传
API_UPLOAD_ENABLED=true
```

#### 手动触发认证(可选)

```bash
# 手动触发API的认证Token
TRIGGER_TOKEN=your-secret-token
```

### 步骤4: 部署

1. 保存环境变量配置
2. Zeabur会自动开始构建和部署
3. 等待部署完成(通常需要2-5分钟)

### 步骤5: 获取访问地址

1. 部署成功后,在服务详情页找到 **"Domains"**
2. 点击 **"Generate Domain"** 生成访问域名
3. 记录下域名,如: `cf-ip-updater.zeabur.app`

---

## ⚙️ 环境变量配置

### 核心配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `FILTER_COUNTRIES` | 过滤国家代码 | `JP,HK,US` | `JP,US,SG,HK` |
| `QUERY_LIMIT` | 每国家IP数量 | `20` | `50` |
| `MAX_LATENCY` | 最大延迟(ms) | `100` | `200` |
| `OUTPUT_FILE` | 输出文件路径 | `output/optimal-ips.txt` | - |

### 定时任务配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `SCHEDULE_ENABLED` | 启用定时任务 | `true` | `true/false` |
| `SCHEDULE_TIMES` | 执行时间(北京时间) | `8:00,14:00,20:00` | `6:00,12:00,18:00,0:00` |
| `RUN_ON_STARTUP` | 启动时立即执行 | `false` | `true/false` |

### CF-RAY检测配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `CF_RAY_DETECTION_ENABLED` | 启用CF-RAY检测 | `true` | `true/false` |
| `CF_RAY_TIMEOUT` | CF-RAY超时(秒) | `20` | `15` |
| `CF_RAY_MAX_WORKERS` | 并发数 | `5` | `10` |
| `CF_RAY_MAX_RETRIES` | 重试次数 | `3` | `5` |

### 第三方API配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ENABLE_API_FALLBACK` | 启用API备选 | `true` |
| `ENABLE_IPINFO_WIDGET` | 启用IPInfo API | `true` |
| `ENABLE_IPAPI_COM` | 启用IP-API | `true` |
| `ENABLE_IPWHOIS` | 启用IPWhois | `true` |
| `API_TIMEOUT` | API超时(秒) | `5` |

### 安全配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `TRIGGER_TOKEN` | 手动触发认证Token | 空 | `my-secret-token-123` |

---

## 🕐 定时任务配置

### 预设方案

#### 方案1: 每天3次(推荐)
```bash
SCHEDULE_TIMES=8:00,14:00,20:00
```
适合大多数场景,平衡更新频率和资源消耗。

#### 方案2: 每天4次
```bash
SCHEDULE_TIMES=6:00,12:00,18:00,0:00
```
更频繁的更新,适合对实时性要求高的场景。

#### 方案3: 每天2次
```bash
SCHEDULE_TIMES=9:00,21:00
```
较低频率,适合IP变化不频繁的场景。

#### 方案4: 每6小时
```bash
SCHEDULE_TIMES=0:00,6:00,12:00,18:00
```
均匀分布,全天候覆盖。

### 自定义时间

你可以设置任意时间点,格式为 `HH:MM`,多个时间用逗号分隔:

```bash
SCHEDULE_TIMES=7:30,13:45,19:15,23:00
```

**注意**: 所有时间均为北京时间(UTC+8)。

---

## 🔌 API接口说明

部署成功后,你的服务将提供以下HTTP接口:

### 1. 服务信息
```bash
GET https://your-domain.zeabur.app/
```

**响应示例**:
```json
{
  "service": "Cloudflare优选IP自动更新服务",
  "status": "running",
  "version": "2.0.0",
  "endpoints": {
    "/": "服务信息",
    "/health": "健康检查",
    "/status": "任务状态",
    "/trigger": "手动触发任务 (POST)",
    "/config": "配置信息"
  }
}
```

### 2. 健康检查
```bash
GET https://your-domain.zeabur.app/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-04T16:00:00",
  "scheduler_running": true
}
```

### 3. 任务状态
```bash
GET https://your-domain.zeabur.app/status
```

**响应示例**:
```json
{
  "task_status": {
    "last_run": "2025-11-04T14:00:00",
    "last_success": "2025-11-04T14:00:00",
    "last_error": null,
    "is_running": false,
    "total_runs": 10,
    "success_runs": 10,
    "failed_runs": 0
  },
  "scheduler": {
    "running": true,
    "jobs": [
      {
        "id": "update_task_8_0",
        "name": "IP更新任务 8:00",
        "next_run": "2025-11-05T08:00:00"
      }
    ]
  }
}
```

### 4. 手动触发任务
```bash
POST https://your-domain.zeabur.app/trigger
```

**不需要认证**:
```bash
curl -X POST https://your-domain.zeabur.app/trigger
```

**需要认证**(如果设置了`TRIGGER_TOKEN`):
```bash
curl -X POST https://your-domain.zeabur.app/trigger \
  -H "Authorization: Bearer your-secret-token"
```

**响应示例**:
```json
{
  "success": true,
  "message": "任务已触发",
  "timestamp": "2025-11-04T16:00:00"
}
```

### 5. 配置信息
```bash
GET https://your-domain.zeabur.app/config
```

**响应示例**:
```json
{
  "filter_countries": ["JP", "HK", "US"],
  "query_limit": 20,
  "max_latency": 100,
  "output_file": "output/optimal-ips.txt",
  "cf_ray_enabled": true,
  "github_repo": "username/repo",
  "schedule_enabled": "true",
  "schedule_times": "8:00,14:00,20:00"
}
```

---

## 🔧 常见问题

### Q1: 如何查看任务执行日志?

**A**: 在Zeabur控制台:
1. 进入你的服务
2. 点击 **"Logs"** 标签
3. 查看实时日志输出

### Q2: 定时任务没有执行怎么办?

**A**: 检查以下几点:
1. 确认 `SCHEDULE_ENABLED=true`
2. 检查 `SCHEDULE_TIMES` 格式是否正确
3. 查看日志是否有错误信息
4. 访问 `/status` 接口查看调度器状态

### Q3: 如何立即执行一次任务?

**A**: 有两种方式:
1. **启动时执行**: 设置 `RUN_ON_STARTUP=true` 并重启服务
2. **手动触发**: 调用 `POST /trigger` 接口

### Q4: 如何修改定时执行时间?

**A**: 
1. 在Zeabur控制台修改 `SCHEDULE_TIMES` 环境变量
2. 保存后服务会自动重启
3. 新的定时任务配置将生效

### Q5: 服务占用多少资源?

**A**: 
- **内存**: 约200-500MB(取决于并发数和缓存大小)
- **CPU**: 任务执行时会有短暂峰值,平时几乎不占用
- **存储**: 约50-100MB(代码+依赖+缓存)

### Q6: 如何保护手动触发接口?

**A**: 设置 `TRIGGER_TOKEN` 环境变量:
```bash
TRIGGER_TOKEN=your-secret-token-123
```

然后调用时需要携带认证头:
```bash
curl -X POST https://your-domain.zeabur.app/trigger \
  -H "Authorization: Bearer your-secret-token-123"
```

### Q7: GitHub上传失败怎么办?

**A**: 检查:
1. `GITHUB_TOKEN` 是否有效(需要 `repo` 权限)
2. `GITHUB_REPO` 格式是否正确(`username/repo`)
3. 仓库是否存在且有写入权限
4. 查看日志中的详细错误信息

### Q8: 如何禁用定时任务,只使用手动触发?

**A**: 设置环境变量:
```bash
SCHEDULE_ENABLED=false
```

然后通过 `POST /trigger` 接口手动触发任务。

### Q9: 可以同时部署多个实例吗?

**A**: 可以,但需要注意:
- 如果上传到同一个GitHub仓库,可能会有冲突
- 建议不同实例使用不同的输出路径或仓库
- 或者只在一个实例启用定时任务,其他实例仅用于手动触发

### Q10: 如何监控服务运行状态?

**A**: 
1. **定期检查**: 使用监控工具定期访问 `/health` 接口
2. **查看状态**: 访问 `/status` 接口查看任务执行情况
3. **日志监控**: 在Zeabur控制台查看日志
4. **告警设置**: 可以使用第三方监控服务(如UptimeRobot)

---

## 📊 性能优化建议

### 1. 调整并发数

根据Zeabur实例规格调整并发数:

**小型实例** (512MB内存):
```bash
CF_RAY_MAX_WORKERS=5
DETECTION_MAX_WORKERS=5
```

**中型实例** (1GB内存):
```bash
CF_RAY_MAX_WORKERS=10
DETECTION_MAX_WORKERS=10
```

**大型实例** (2GB+内存):
```bash
CF_RAY_MAX_WORKERS=20
DETECTION_MAX_WORKERS=20
```

### 2. 优化超时时间

网络良好时可以减少超时时间:
```bash
CF_RAY_TIMEOUT=5
API_TIMEOUT=3
```

网络较差时增加超时时间:
```bash
CF_RAY_TIMEOUT=20
API_TIMEOUT=8
```

### 3. 启用缓存

确保缓存已启用以提升性能:
```bash
CACHE_ENABLED=true
CACHE_DAYS=30
CF_RAY_CACHE_ENABLED=true
```

---

## 🎉 部署完成

恭喜!你已经成功将Cloudflare优选IP自动更新系统部署到Zeabur。

**下一步**:
1. ✅ 访问你的服务域名,确认服务正常运行
2. ✅ 查看 `/status` 接口,确认定时任务已配置
3. ✅ 等待第一次定时任务执行,或手动触发一次
4. ✅ 检查输出文件或GitHub仓库,确认IP已更新

**需要帮助?**
- 查看项目 [README.md](README.md)
- 查看 [GitHub Issues](https://github.com/your-repo/issues)
- 查看 [Zeabur文档](https://zeabur.com/docs)

---

**最后更新**: 2025-11-04