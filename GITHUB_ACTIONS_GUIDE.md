# GitHub Actions 自动化部署指南

## 📋 目录

- [功能说明](#功能说明)
- [配置步骤](#配置步骤)
- [Secrets配置](#secrets配置)
- [运行方式](#运行方式)
- [查看日志](#查看日志)
- [故障排查](#故障排查)
- [高级配置](#高级配置)

## 功能说明

GitHub Actions会自动执行以下任务：

1. ✅ **定时运行** - 每3小时自动运行一次
2. ✅ **获取优选IP** - 从多个数据源获取最新的优选IP
3. ✅ **保存到GitHub** - 将结果保存到仓库（可选）
4. ✅ **上传到订阅项目** - 通过API直接上传到Cloudflare Workers订阅项目
5. ✅ **日志保存** - 自动保存执行日志，保留7天

## 配置步骤

### 第一步：Fork或创建仓库

1. **Fork本仓库**
   ```
   点击GitHub页面右上角的 "Fork" 按钮
   ```

   或

2. **创建新仓库**
   ```bash
   # 克隆代码到本地
   git clone https://github.com/your-username/clash-cf-updater.git
   cd clash-cf-updater
   
   # 推送到你的GitHub仓库
   git remote set-url origin https://github.com/your-username/your-repo.git
   git push -u origin main
   ```

### 第二步：配置GitHub Secrets

在你的GitHub仓库中配置Secrets：

1. 进入仓库页面
2. 点击 `Settings` (设置)
3. 在左侧菜单找到 `Secrets and variables` → `Actions`
4. 点击 `New repository secret` 添加以下Secrets

## Secrets配置

### 必需配置（API上传）

如果你想使用API上传功能，需要配置：

| Secret名称 | 说明 | 示例值 |
|-----------|------|--------|
| `SUBSCRIPTION_API_URL` | 订阅项目的Workers URL | `https://your-worker.workers.dev` |
| `SUBSCRIPTION_API_PATH` | API路径（UUID或自定义路径） | `/351c9981-04b6-4103-aa4b-864aa9c91469` |
| `API_UPLOAD_ENABLED` | 是否启用API上传 | `true` |

### 可选配置（GitHub上传）

如果你想同时保存到GitHub仓库，需要配置：

| Secret名称 | 说明 | 示例值 |
|-----------|------|--------|
| `GH_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` |
| `TARGET_REPO` | 目标仓库 | `username/repo` |

### 配置说明

#### 1. SUBSCRIPTION_API_URL

订阅项目的Workers URL，不包含路径部分。

**获取方法**：
- 访问你的订阅项目管理页面
- 从浏览器地址栏复制域名部分

**示例**：
```
https://your-worker.workers.dev
```

#### 2. SUBSCRIPTION_API_PATH

订阅项目的API路径，包含UUID或自定义路径。

**获取方法**：

**方法A - UUID模式**：
- 从订阅项目管理页面的URL中获取
- 例如：`https://your-worker.workers.dev/351c9981-04b6-4103-aa4b-864aa9c91469`
- 则填写：`/351c9981-04b6-4103-aa4b-864aa9c91469`

**方法B - 自定义路径模式**：
- 如果你在订阅项目中设置了d变量（自定义路径）
- 例如：d变量设置为 `/mypath`
- 则填写：`/mypath`

#### 3. API_UPLOAD_ENABLED

是否启用API上传功能。

**值**：
- `true` - 启用API上传
- `false` - 禁用API上传

#### 4. GH_TOKEN（可选）

GitHub Personal Access Token，用于上传文件到GitHub仓库。

**创建方法**：
1. 访问 https://github.com/settings/tokens
2. 点击 `Generate new token` → `Generate new token (classic)`
3. 设置Token名称，例如：`clash-cf-updater`
4. 选择权限：勾选 `repo` (完整仓库访问权限)
5. 点击 `Generate token`
6. **立即复制Token**（只显示一次）

#### 5. TARGET_REPO（可选）

目标GitHub仓库，格式为 `username/repo`。

**示例**：
```
EseeEhin/cf-ip
```

## 配置示例

### 示例1：仅使用API上传

```
SUBSCRIPTION_API_URL = https://my-worker.workers.dev
SUBSCRIPTION_API_PATH = /351c9981-04b6-4103-aa4b-864aa9c91469
API_UPLOAD_ENABLED = true
```

不需要配置 `GH_TOKEN` 和 `TARGET_REPO`。

### 示例2：同时使用GitHub和API

```
# API配置
SUBSCRIPTION_API_URL = https://my-worker.workers.dev
SUBSCRIPTION_API_PATH = /mypath
API_UPLOAD_ENABLED = true

# GitHub配置
GH_TOKEN = ghp_xxxxxxxxxxxxxxxxxxxx
TARGET_REPO = username/cf-ip
```

### 示例3：仅使用GitHub上传

```
# GitHub配置
GH_TOKEN = ghp_xxxxxxxxxxxxxxxxxxxx
TARGET_REPO = username/cf-ip

# 不配置API相关Secrets，或设置
API_UPLOAD_ENABLED = false
```

## 运行方式

### 1. 自动运行（定时任务）

GitHub Actions会自动每3小时运行一次：

**运行时间（北京时间）**：
- 02:00
- 05:00
- 08:00
- 11:00
- 14:00
- 17:00
- 20:00
- 23:00

**查看运行状态**：
1. 进入仓库页面
2. 点击 `Actions` 标签
3. 查看 `Update Optimal IPs` 工作流

### 2. 手动运行

你可以随时手动触发运行：

1. 进入仓库页面
2. 点击 `Actions` 标签
3. 选择 `Update Optimal IPs` 工作流
4. 点击右侧的 `Run workflow` 按钮
5. 选择分支（通常是 `main`）
6. 点击绿色的 `Run workflow` 按钮

### 3. 代码推送触发

每次推送代码到 `main` 分支时，也会自动运行。

## 查看日志

### 实时日志

1. 进入 `Actions` 页面
2. 点击最新的运行记录
3. 点击 `update-ips` 任务
4. 展开各个步骤查看详细日志

### 下载日志

1. 进入 `Actions` 页面
2. 点击运行记录
3. 在页面底部找到 `Artifacts`
4. 下载 `logs-xxx` 文件
5. 解压查看详细日志

**日志保留时间**：7天

## 执行流程

```
┌─────────────────────────────────────────┐
│  1. Checkout code (检出代码)            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  2. Set up Python (设置Python环境)      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  3. Install dependencies (安装依赖)     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  4. Run IP fetcher (运行主程序)         │
│     ├─ 获取优选IP                       │
│     ├─ 保存到本地文件                   │
│     ├─ 上传到GitHub (可选)              │
│     └─ 上传到订阅项目API (可选)         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  5. Upload logs (上传日志)              │
└─────────────────────────────────────────┘
```

## 故障排查

### 问题1：Actions运行失败

**症状**：Actions显示红色❌

**排查步骤**：
1. 点击失败的运行记录
2. 查看具体哪个步骤失败
3. 展开步骤查看错误信息

**常见原因**：
- Secrets配置错误
- API功能未启用
- 网络连接问题

### 问题2：API上传失败

**症状**：日志显示"API上传失败"

**解决方法**：
1. 检查 `SUBSCRIPTION_API_URL` 是否正确
2. 检查 `SUBSCRIPTION_API_PATH` 是否正确
3. 确认订阅项目已开启"允许API管理 (ae)"
4. 确认订阅项目已配置KV存储

### 问题3：GitHub上传失败

**症状**：日志显示"GitHub上传失败"

**解决方法**：
1. 检查 `GH_TOKEN` 是否有效
2. 检查 `TARGET_REPO` 格式是否正确
3. 确认Token有 `repo` 权限
4. 确认目标仓库存在

### 问题4：Secrets未生效

**症状**：日志显示"未配置XXX"

**解决方法**：
1. 确认Secrets名称拼写正确（区分大小写）
2. 确认Secrets已保存
3. 重新运行工作流

### 问题5：定时任务未运行

**症状**：到了预定时间但没有运行

**可能原因**：
1. GitHub Actions有时会延迟几分钟
2. 仓库长时间无活动可能被暂停

**解决方法**：
1. 等待5-10分钟
2. 手动运行一次激活
3. 定期推送代码保持活跃

## 高级配置

### 修改运行频率

编辑 `.github/workflows/update-ips.yml`：

```yaml
on:
  schedule:
    # 每小时运行一次
    - cron: '0 * * * *'
    
    # 每6小时运行一次
    - cron: '0 */6 * * *'
    
    # 每天凌晨2点运行
    - cron: '0 18 * * *'  # UTC时间18:00 = 北京时间02:00
```

### 添加通知

可以添加邮件或其他通知方式：

```yaml
- name: Send notification
  if: failure()
  run: |
    # 发送通知的命令
    echo "任务失败，发送通知"
```

### 自定义环境变量

在 `env` 部分添加更多环境变量：

```yaml
- name: Run IP fetcher and uploader
  env:
    GITHUB_TOKEN: ${{ secrets.GH_TOKEN }}
    GITHUB_REPO: ${{ secrets.TARGET_REPO }}
    SUBSCRIPTION_API_URL: ${{ secrets.SUBSCRIPTION_API_URL }}
    SUBSCRIPTION_API_PATH: ${{ secrets.SUBSCRIPTION_API_PATH }}
    API_UPLOAD_ENABLED: ${{ secrets.API_UPLOAD_ENABLED }}
    # 自定义配置
    FILTER_COUNTRIES: JP,HK,US,SG
    QUERY_LIMIT: 20
    LOG_LEVEL: DEBUG
  run: python -m src.main
```

## 安全建议

### 1. 保护Secrets

- ❌ 不要在代码中硬编码敏感信息
- ❌ 不要在日志中打印Secrets
- ✅ 使用GitHub Secrets存储敏感信息
- ✅ 定期更换Token和密码

### 2. 最小权限原则

- GitHub Token只授予必需的权限
- 如果只需要上传文件，只勾选 `repo` 权限

### 3. 定期检查

- 定期查看Actions运行日志
- 检查是否有异常访问
- 及时更新依赖包

## 监控和维护

### 查看运行历史

```
Actions → Update Optimal IPs → 查看所有运行记录
```

### 查看成功率

GitHub会显示工作流的成功率统计。

### 日志分析

下载日志文件，分析：
- 获取了多少个IP
- 哪些数据源成功/失败
- 上传是否成功
- 执行耗时

## 常见使用场景

### 场景1：测试配置

1. 配置好所有Secrets
2. 手动运行一次
3. 查看日志确认配置正确
4. 等待定时任务自动运行

### 场景2：紧急更新

1. 进入Actions页面
2. 手动触发运行
3. 等待几分钟完成
4. 检查订阅项目是否更新

### 场景3：调试问题

1. 在Secrets中添加 `LOG_LEVEL=DEBUG`
2. 手动运行一次
3. 下载详细日志
4. 分析问题原因

## 成本说明

GitHub Actions对公开仓库**完全免费**，没有使用限制。

对于私有仓库：
- 免费账户：每月2000分钟
- 本项目每次运行约2-3分钟
- 每3小时运行一次，每天8次
- 每月约 8 × 30 × 3 = 720 分钟

**建议**：使用公开仓库，完全免费。

## 相关文档

- [GitHub Actions官方文档](https://docs.github.com/en/actions)
- [Cron表达式说明](https://crontab.guru/)
- [API_UPLOAD_GUIDE.md](API_UPLOAD_GUIDE.md) - API上传详细指南
- [README.md](README.md) - 项目总体说明

## 总结

GitHub Actions提供了强大的自动化能力：

✅ **零成本** - 公开仓库完全免费
✅ **全自动** - 定时运行，无需人工干预
✅ **可靠** - GitHub基础设施保障
✅ **灵活** - 支持手动触发和自定义配置
✅ **透明** - 完整的日志记录

配置好后，你就可以完全放手，让GitHub Actions自动帮你更新优选IP！🚀