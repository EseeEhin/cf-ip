# Zeabur 快速部署指南 ⚡

5分钟快速部署Cloudflare优选IP自动更新服务到Zeabur!

## 🚀 快速开始

### 步骤1: 准备GitHub仓库 (1分钟)

确保你的GitHub仓库包含以下文件:
- ✅ `app.py`
- ✅ `requirements.txt`
- ✅ `zbpack.json`
- ✅ `src/` 目录

### 步骤2: 在Zeabur创建项目 (2分钟)

1. 访问 [Zeabur控制台](https://dash.zeabur.com)
2. 点击 **"New Project"**
3. 点击 **"Add Service"** → 选择 **"Git"**
4. 选择你的GitHub仓库

### 步骤3: 配置环境变量 (2分钟)

在服务设置中添加以下**最小配置**:

```bash
# 基础配置
FILTER_COUNTRIES=JP,HK,US
QUERY_LIMIT=20

# 定时任务(每天8:00, 14:00, 20:00执行)
SCHEDULE_ENABLED=true
SCHEDULE_TIMES=8:00,14:00,20:00

# 启动时立即执行一次
RUN_ON_STARTUP=true
```

**可选配置** - GitHub自动上传:
```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=username/repo
GITHUB_BRANCH=main
GITHUB_FILE_PATH=optimal-ips.txt
```

### 步骤4: 部署并获取域名 (1分钟)

1. 保存配置,Zeabur自动开始部署
2. 等待部署完成(约2-3分钟)
3. 点击 **"Generate Domain"** 生成访问域名
4. 访问域名,看到服务信息即部署成功! 🎉

---

## 🔍 验证部署

### 1. 检查服务状态
```bash
curl https://your-domain.zeabur.app/health
```

### 2. 查看任务状态
```bash
curl https://your-domain.zeabur.app/status
```

### 3. 手动触发任务
```bash
curl -X POST https://your-domain.zeabur.app/trigger
```

---

## 📋 常用配置模板

### 模板1: 基础配置(推荐)
```bash
FILTER_COUNTRIES=JP,HK,US
QUERY_LIMIT=20
SCHEDULE_ENABLED=true
SCHEDULE_TIMES=8:00,14:00,20:00
RUN_ON_STARTUP=true
```

### 模板2: 高频更新
```bash
FILTER_COUNTRIES=JP,HK,US,SG
QUERY_LIMIT=50
SCHEDULE_ENABLED=true
SCHEDULE_TIMES=6:00,12:00,18:00,0:00
RUN_ON_STARTUP=true
CF_RAY_MAX_WORKERS=10
```

### 模板3: 仅手动触发
```bash
FILTER_COUNTRIES=JP,HK,US
QUERY_LIMIT=20
SCHEDULE_ENABLED=false
TRIGGER_TOKEN=my-secret-token
```

---

## 🎯 下一步

- 📖 查看完整文档: [ZEABUR_DEPLOYMENT.md](ZEABUR_DEPLOYMENT.md)
- 🔧 了解所有配置: [.env.example](.env.example)
- 📊 查看项目说明: [README.md](README.md)

---

**部署遇到问题?** 查看 [常见问题](ZEABUR_DEPLOYMENT.md#常见问题)