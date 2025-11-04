# API上传功能使用指南

## 功能说明

本项目支持通过API直接将优选IP上传到你的Cloudflare Workers订阅项目的管理后台，无需手动复制粘贴。

## 前置要求

### 1. 订阅项目配置

你的订阅项目必须满足以下条件：

1. **已配置KV存储**
   - 在Cloudflare Workers中创建KV命名空间
   - 绑定环境变量 `C`
   - 重新部署代码

2. **开启API管理功能**
   - 访问订阅项目的管理页面（例如：`https://your-worker.workers.dev/your-uuid`）
   - 找到"配置管理"部分
   - 在"高级控制"中，将"允许API管理 (ae)"设置为"开启API管理"
   - 保存配置

## 配置步骤

### 1. 复制环境变量配置文件

```bash
cp .env.example .env
```

### 2. 编辑 `.env` 文件

找到"订阅项目API配置"部分，填写以下信息：

```env
# ==================== 订阅项目API配置 ====================
# 订阅项目的Workers URL（例如: https://your-worker.workers.dev）
SUBSCRIPTION_API_URL=https://your-worker.workers.dev

# 订阅项目的API路径（UUID或自定义路径）
# 如果使用UUID模式: /351c9981-04b6-4103-aa4b-864aa9c91469
# 如果使用自定义路径: /your-custom-path
SUBSCRIPTION_API_PATH=/351c9981-04b6-4103-aa4b-864aa9c91469

# 是否启用API上传功能（true/false）
API_UPLOAD_ENABLED=true
```

### 3. 获取订阅项目信息

#### 方法1：从浏览器地址栏获取

访问你的订阅项目管理页面，地址栏显示：
```
https://your-worker.workers.dev/351c9981-04b6-4103-aa4b-864aa9c91469
```

则配置为：
- `SUBSCRIPTION_API_URL`: `https://your-worker.workers.dev`
- `SUBSCRIPTION_API_PATH`: `/351c9981-04b6-4103-aa4b-864aa9c91469`

#### 方法2：从订阅项目配置查看

如果你使用了自定义路径（d变量），则：
- `SUBSCRIPTION_API_URL`: `https://your-worker.workers.dev`
- `SUBSCRIPTION_API_PATH`: `/your-custom-path`

## 使用方法

### 运行程序

```bash
python -m src.main
```

程序会自动执行以下步骤：
1. 从多个数据源获取优选IP
2. 保存到本地文件 `output/optimal-ips.txt`
3. 上传到GitHub（如果配置了）
4. **通过API上传到订阅项目**

### 查看执行日志

程序会显示详细的执行日志：

```
============================================================
步骤 3/3: 上传到订阅项目API
============================================================
[API上传器] 初始化完成
[API上传器] API端点: https://your-worker.workers.dev/your-uuid/api/preferred-ips
[API上传器] 正在上传 128 个优选IP...
[API上传器] ✅ 上传成功!
[API上传器]    - 成功添加: 128 个
[API上传器]    - 跳过重复: 0 个
[API上传器]    - 错误: 0 个
[API上传器] 新添加的IP:
[API上传器]    - 104.17.48.0:443 (B-US-Newark)
[API上传器]    - 104.18.35.42:443 (B-US-Newark)
[API上传器]    - 104.18.32.42:443 (B-US-Newark)
[API上传器]    - 104.18.33.4:443 (B-US-Newark)
[API上传器]    - 104.18.37.4:443 (B-US-New York)
[API上传器]    ... 还有 123 个
✅ API上传成功
```

## API功能说明

### 支持的操作

API上传器支持以下操作：

1. **添加优选IP** (POST)
   - 自动添加新的优选IP
   - 跳过已存在的IP
   - 返回详细的添加结果

2. **查询优选IP** (GET)
   - 查看当前订阅项目中的所有优选IP

3. **删除优选IP** (DELETE)
   - 删除指定的优选IP
   - 清空所有优选IP

### 测试API功能

你可以单独测试API上传功能：

```bash
python -m src.api_uploader
```

这会执行以下测试：
1. 获取当前优选IP列表
2. 添加2个测试IP
3. 显示详细的执行结果

## 常见问题

### 1. API功能未启用

**错误信息**：
```
[API上传器] ❌ API功能未启用
```

**解决方法**：
1. 访问订阅项目的配置管理页面
2. 找到"高级控制"部分
3. 将"允许API管理 (ae)"设置为"开启API管理"
4. 保存配置

### 2. KV存储未配置

**错误信息**：
```
[API上传器] ❌ KV存储未配置
```

**解决方法**：
1. 在Cloudflare Workers中创建KV命名空间
2. 绑定环境变量 `C`
3. 重新部署代码

### 3. 请求超时

**错误信息**：
```
[API上传器] ❌ 请求超时
```

**解决方法**：
1. 检查网络连接
2. 检查Workers URL是否正确
3. 增加超时时间（在 `.env` 中设置 `REQUEST_TIMEOUT=60`）

### 4. 路径验证失败

**错误信息**：
```
路径验证失败
```

**解决方法**：
1. 确认 `SUBSCRIPTION_API_PATH` 配置正确
2. 如果使用UUID模式，确保UUID与订阅项目的u变量一致
3. 如果使用自定义路径，确保路径与订阅项目的d变量一致

## 数据格式

### 输入格式（程序自动处理）

程序会自动将获取的IP数据转换为API所需的格式：

```json
[
  {
    "ip": "104.17.48.0",
    "port": 443,
    "name": "B-US-Newark"
  },
  {
    "ip": "104.18.35.42",
    "port": 443,
    "name": "B-US-Newark"
  }
]
```

### 订阅项目中的显示格式

上传成功后，在订阅项目的配置管理页面，"优选IP列表 (yx)"字段会显示：

```
104.17.48.0:443#B-US-Newark,104.18.35.42:443#B-US-Newark,...
```

## 安全建议

1. **不要公开分享你的配置文件**
   - `.env` 文件包含敏感信息，不要提交到Git仓库
   - 项目已在 `.gitignore` 中排除了 `.env` 文件

2. **定期更换UUID**
   - 如果担心安全问题，可以定期更换订阅项目的UUID

3. **使用自定义路径**
   - 相比UUID，自定义路径更难被猜测
   - 在订阅项目中设置d变量使用自定义路径

4. **限制API访问**
   - 只在需要时开启"允许API管理"功能
   - 不使用时可以关闭该功能

## 高级用法

### 仅上传到API，不上传到GitHub

在 `.env` 中：

```env
# 不配置GitHub相关变量
GITHUB_TOKEN=
GITHUB_REPO=

# 启用API上传
API_UPLOAD_ENABLED=true
```

### 同时上传到GitHub和API

在 `.env` 中：

```env
# 配置GitHub
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repo

# 启用API上传
API_UPLOAD_ENABLED=true
```

### 使用GitHub Actions自动上传

GitHub Actions会自动执行程序，包括API上传功能。确保在GitHub Secrets中配置：

- `SUBSCRIPTION_API_URL`
- `SUBSCRIPTION_API_PATH`
- `API_UPLOAD_ENABLED` (设置为 `true`)

## 技术细节

### API端点

程序使用以下API端点：

```
{SUBSCRIPTION_API_URL}{SUBSCRIPTION_API_PATH}/api/preferred-ips
```

例如：
```
https://your-worker.workers.dev/351c9981-04b6-4103-aa4b-864aa9c91469/api/preferred-ips
```

### 请求方法

- **GET**: 查询当前优选IP列表
- **POST**: 添加新的优选IP
- **DELETE**: 删除优选IP

### 响应格式

成功响应示例：

```json
{
  "success": true,
  "message": "成功添加 128 个IP",
  "added": 128,
  "skipped": 0,
  "errors": 0,
  "data": {
    "addedIPs": [...]
  }
}
```

## 相关文档

- [README.md](README.md) - 项目总体说明
- [QUICK_START.md](QUICK_START.md) - 快速开始指南
- [CONFIG_TEMPLATE.md](CONFIG_TEMPLATE.md) - 配置模板说明

## 支持

如果遇到问题，请：

1. 查看程序日志文件 `logs/ip_fetcher.log`
2. 检查订阅项目的配置是否正确
3. 确认KV存储和API管理功能已启用
4. 提交Issue到GitHub仓库