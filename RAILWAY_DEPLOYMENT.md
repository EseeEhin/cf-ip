# Railway 部署指南

Railway是一个现代化的云平台,支持从GitHub自动部署,提供免费额度。

## 🚀 快速部署

### 步骤1: 准备Railway账号

1. 访问 [Railway.app](https://railway.app)
2. 使用GitHub账号登录
3. 验证邮箱

### 步骤2: 创建新项目

1. 点击 **"New Project"**
2. 选择 **"Deploy from GitHub repo"**
3. 授权Railway访问你的GitHub
4. 选择仓库: `EseeEhin/cf-ip`

### 步骤3: 配置环境变量

在Railway项目设置中添加环境变量:

#### 必需配置
```bash
# 基础配置
FILTER_COUNTRIES=JP,HK,US
QUERY_LIMIT=20
MAX_LATENCY=100

# 定时任务
SCHEDULE_ENABLED=true
SCHEDULE_TIMES=8:00,14:00,20:00
RUN_ON_STARTUP=true

# Railway会自动设置PORT
```

#### 可选配置
```bash
# GitHub上传
GITHUB_TOKEN=your_token
GITHUB_REPO=username/repo
GITHUB_BRANCH=main

# CF-RAY检测
CF_RAY_DETECTION_ENABLED=true
CF_RAY_TIMEOUT=20
CF_RAY_MAX_WORKERS=5
```

### 步骤4: 部署

1. Railway会自动检测Dockerfile
2. 自动构建并部署
3. 等待部署完成(约3-5分钟)

### 步骤5: 获取访问地址

1. 在项目设置中点击 **"Generate Domain"**
2. 获取公开访问地址
3. 访问 `https://your-app.railway.app/health` 验证

## 📊 Railway优势

- ✅ **免费额度**: $5/月免费额度
- ✅ **自动部署**: Git推送自动触发部署
- ✅ **简单配置**: 自动检测Dockerfile
- ✅ **内置数据库**: 支持PostgreSQL、Redis等
- ✅ **日志查看**: 实时查看应用日志

## 💰 费用说明

**免费计划**:
- $5/月免费额度
- 512MB内存
- 1GB存储
- 100GB流量

**预估消耗**:
- 本项目约消耗 $2-3/月
- 可在免费额度内运行

## 🔧 常见问题

### Q: 如何查看日志?
**A**: 在Railway项目页面点击 "Deployments" → 选择部署 → 查看日志

### Q: 如何重新部署?
**A**: 推送代码到GitHub会自动触发,或在Railway点击 "Redeploy"

### Q: 端口配置?
**A**: Railway自动设置PORT环境变量,app.py会自动读取

## 📚 相关链接

- [Railway文档](https://docs.railway.app)
- [Railway定价](https://railway.app/pricing)
- [Railway状态](https://status.railway.app)