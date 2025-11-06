# Render 部署指南

Render是一个现代化的云平台,提供免费的Web服务托管。

## 🚀 快速部署

### 步骤1: 准备Render账号

1. 访问 [Render.com](https://render.com)
2. 使用GitHub账号注册/登录

### 步骤2: 创建Web Service

1. 点击 **"New +"** → 选择 **"Web Service"**
2. 连接GitHub仓库: `EseeEhin/cf-ip`
3. 配置服务:
   - **Name**: `cf-ip-updater`
   - **Region**: Singapore (最近的区域)
   - **Branch**: `main`
   - **Runtime**: Docker
   - **Instance Type**: Free

### 步骤3: 配置环境变量

在 "Environment" 标签添加:

```bash
# 基础配置
FILTER_COUNTRIES=JP,HK,US
QUERY_LIMIT=20
MAX_LATENCY=100

# 定时任务
SCHEDULE_ENABLED=true
SCHEDULE_TIMES=8:00,14:00,20:00
RUN_ON_STARTUP=true

# Render会自动设置PORT=10000
```

### 步骤4: 部署

1. 点击 **"Create Web Service"**
2. Render自动构建Docker镜像
3. 等待部署完成(约5-10分钟)

### 步骤5: 验证部署

访问Render提供的URL:
```bash
https://cf-ip-updater.onrender.com/health
```

## 📊 Render特点

### 优势
- ✅ **完全免费**: 免费计划永久有效
- ✅ **自动部署**: Git推送自动触发
- ✅ **HTTPS**: 自动提供SSL证书
- ✅ **简单易用**: 配置简单直观

### 限制
- ⚠️ **休眠机制**: 15分钟无请求会休眠
- ⚠️ **冷启动**: 休眠后首次访问需30-60秒
- ⚠️ **资源限制**: 512MB内存,0.1 CPU

## 🔧 解决休眠问题

### 方案1: 使用UptimeRobot监控

1. 注册 [UptimeRobot](https://uptimerobot.com)
2. 添加HTTP监控:
   - URL: `https://your-app.onrender.com/health`
   - 间隔: 5分钟
3. 保持服务活跃

### 方案2: 使用Cron-job.org

1. 注册 [Cron-job.org](https://cron-job.org)
2. 创建定时任务:
   - URL: `https://your-app.onrender.com/health`
   - 间隔: 每5分钟
3. 防止服务休眠

### 方案3: 升级到付费计划

- **Starter**: $7/月
- 无休眠限制
- 更多资源

## 💡 最佳实践

### 1. 健康检查配置

在Render设置中配置:
- **Health Check Path**: `/health`
- **Health Check Interval**: 30秒

### 2. 日志查看

在Render控制台:
- 点击 "Logs" 标签
- 实时查看应用日志
- 支持日志搜索和过滤

### 3. 自动部署

Render会自动监听GitHub:
- 推送到main分支自动部署
- 可在设置中禁用自动部署

## 🔍 故障排查

### 问题1: 服务频繁休眠

**解决方案**:
- 使用UptimeRobot保持活跃
- 或升级到付费计划

### 问题2: 构建失败

**检查**:
- Dockerfile语法是否正确
- requirements.txt是否完整
- 查看构建日志定位错误

### 问题3: 环境变量未生效

**解决方案**:
- 确认环境变量已保存
- 重新部署服务
- 检查变量名拼写

## 📊 费用对比

| 计划 | 价格 | 内存 | CPU | 休眠 |
|------|------|------|-----|------|
| Free | $0 | 512MB | 0.1 | 15分钟 |
| Starter | $7/月 | 512MB | 0.5 | 无 |
| Standard | $25/月 | 2GB | 1.0 | 无 |

## 🎯 推荐配置

### 免费用户
```bash
# 基础配置
FILTER_COUNTRIES=JP,HK,US
QUERY_LIMIT=10
SCHEDULE_TIMES=8:00,20:00

# 降低资源消耗
CF_RAY_MAX_WORKERS=3
DETECTION_MAX_WORKERS=3
```

### 付费用户
```bash
# 完整配置
FILTER_COUNTRIES=JP,HK,US,SG
QUERY_LIMIT=50
SCHEDULE_TIMES=6:00,12:00,18:00,0:00

# 更高性能
CF_RAY_MAX_WORKERS=10
DETECTION_MAX_WORKERS=10
```

## 📚 相关链接

- [Render文档](https://render.com/docs)
- [Render定价](https://render.com/pricing)
- [Render状态](https://status.render.com)
- [Render社区](https://community.render.com)

## ✅ 部署检查清单

- [ ] Render账号已创建
- [ ] GitHub仓库已连接
- [ ] 环境变量已配置
- [ ] 服务已成功部署
- [ ] 健康检查通过
- [ ] (可选) UptimeRobot已配置