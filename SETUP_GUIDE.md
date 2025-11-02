# 配置指南 - 上传到 GitHub 仓库

## 📋 前置准备

1. **GitHub账号**：确保你已登录GitHub
2. **Git工具**：确保本地已安装Git
3. **仓库地址**：https://github.com/EseeEhin/cf-ip.git

## 🚀 步骤1：初始化本地Git仓库

在项目根目录（`d:/clash-cf-updater`）执行以下命令：

```bash
# 初始化Git仓库
git init

# 添加所有文件到暂存区
git add .

# 提交到本地仓库
git commit -m "Initial commit: Clash优选IP自动更新器"

# 添加远程仓库
git remote add origin https://github.com/EseeEhin/cf-ip.git

# 推送到GitHub（首次推送）
git branch -M main
git push -u origin main
```

## 🔑 步骤2：配置GitHub Secrets

推送成功后，需要在GitHub仓库中配置Secrets：

### 2.1 创建Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 **"Generate new token"** > **"Generate new token (classic)"**
3. 设置Token名称：`CF_IP_UPDATER`
4. 勾选权限：
   - ✅ `repo` (完整仓库访问权限)
5. 点击 **"Generate token"**
6. **立即复制Token**（只显示一次！）

### 2.2 配置Repository Secrets

1. 访问仓库设置：https://github.com/EseeEhin/cf-ip/settings/secrets/actions
2. 点击 **"New repository secret"**
3. 添加以下Secrets：

| Secret名称 | 值 | 说明 |
|-----------|---|------|
| `GH_TOKEN` | `ghp_xxxxx...` | 刚才创建的Personal Access Token |
| `TARGET_REPO` | `EseeEhin/cf-ip` | 目标仓库（当前仓库） |

### 2.3 配置可选的Secrets（如需自定义）

| Secret名称 | 默认值 | 说明 |
|-----------|--------|------|
| `FILTER_COUNTRIES` | `JP,US,SG` | 要获取的国家代码（逗号分隔） |
| `QUERY_LIMIT` | `100` | 每个国家获取的IP数量 |
| `GITHUB_FILE_PATH` | `优选IP.txt` | GitHub中的文件路径 |

## ⚙️ 步骤3：启用GitHub Actions

1. 访问：https://github.com/EseeEhin/cf-ip/actions
2. 如果看到提示，点击 **"I understand my workflows, go ahead and enable them"**
3. GitHub Actions现在已启用

## 🎯 步骤4：测试运行

### 方式1：手动触发（推荐首次测试）

1. 访问：https://github.com/EseeEhin/cf-ip/actions
2. 选择 **"Update Optimal IPs"** 工作流
3. 点击 **"Run workflow"** 按钮
4. 选择分支：`main`
5. 点击绿色的 **"Run workflow"** 按钮
6. 等待几秒，刷新页面查看运行状态

### 方式2：等待自动运行

工作流会在以下时间自动运行（北京时间）：
- 每天 08:00
- 每天 14:00
- 每天 20:00

## 📊 步骤5：查看结果

### 5.1 查看运行日志

1. 访问：https://github.com/EseeEhin/cf-ip/actions
2. 点击最新的运行记录
3. 查看详细的执行日志

### 5.2 获取raw链接

成功运行后，IP文件会自动上传到仓库，访问链接：

```
https://raw.githubusercontent.com/EseeEhin/cf-ip/main/优选IP.txt
```

### 5.3 在订阅项目中使用

将上述raw链接配置到你的订阅转换项目中即可使用。

## 🔧 常见问题

### Q1: 推送时提示权限错误？

**解决方案**：
```bash
# 使用HTTPS方式，会提示输入用户名和密码
# 用户名：你的GitHub用户名
# 密码：使用Personal Access Token（不是GitHub密码）

# 或者配置SSH密钥（推荐）
```

### Q2: Actions运行失败？

**检查清单**：
1. ✅ 是否正确配置了 `GH_TOKEN` Secret？
2. ✅ Token是否有 `repo` 权限？
3. ✅ `TARGET_REPO` 是否正确（`EseeEhin/cf-ip`）？
4. ✅ 查看Actions日志中的具体错误信息

### Q3: 如何修改更新频率？

编辑 `.github/workflows/update-ips.yml` 文件中的 `cron` 表达式：

```yaml
schedule:
  - cron: '0 0,6,12 * * *'  # 当前：北京时间 8:00, 14:00, 20:00
```

常用时间配置：

| Cron表达式 | 北京时间 | 说明 |
|-----------|---------|------|
| `0 0,6,12,18 * * *` | 8:00, 14:00, 20:00, 2:00 | 每6小时 |
| `0 */4 * * *` | 每4小时 | 更频繁 |
| `0 0 * * *` | 8:00 | 每天一次 |

### Q4: 如何添加更多国家？

**方式1：修改代码**（永久生效）

编辑 `.env.example` 或创建 `.env` 文件：
```
FILTER_COUNTRIES=JP,US,SG,HK,TW,KR
```

**方式2：使用Secret**（推荐）

在GitHub Secrets中添加 `FILTER_COUNTRIES`：
```
JP,US,SG,HK,TW,KR
```

## 📝 下一步

1. ✅ 推送代码到GitHub
2. ✅ 配置Secrets
3. ✅ 手动触发测试
4. ✅ 验证输出文件
5. ✅ 配置到订阅项目

## 🎉 完成！

配置完成后，系统将自动：
- 每天定时获取优选IP
- 自动更新到GitHub仓库
- 提供稳定的raw链接供订阅使用

---

**需要帮助？** 查看详细日志或提交Issue：https://github.com/EseeEhin/cf-ip/issues