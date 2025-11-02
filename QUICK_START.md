# 🚀 快速配置指南

## ✅ 第一步：代码已上传

代码已成功推送到：https://github.com/EseeEhin/cf-ip

## 🔑 第二步：配置GitHub Secrets（重要！）

### 1. 创建Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 **"Generate new token"** → **"Generate new token (classic)"**
3. 设置名称：`CF_IP_UPDATER`
4. 勾选权限：**`repo`** (完整仓库访问权限)
5. 点击 **"Generate token"**
6. **立即复制Token**（格式：`ghp_xxxxxxxxxxxxx`）

### 2. 配置Repository Secrets

1. 访问：https://github.com/EseeEhin/cf-ip/settings/secrets/actions
2. 点击 **"New repository secret"**
3. 添加两个Secrets：

#### Secret 1: GH_TOKEN
- **Name**: `GH_TOKEN`
- **Value**: 粘贴刚才复制的Token（`ghp_xxxxxxxxxxxxx`）
- 点击 **"Add secret"**

#### Secret 2: TARGET_REPO
- **Name**: `TARGET_REPO`
- **Value**: `EseeEhin/cf-ip`
- 点击 **"Add secret"**

## ⚙️ 第三步：启用GitHub Actions

1. 访问：https://github.com/EseeEhin/cf-ip/actions
2. 如果看到提示，点击 **"I understand my workflows, go ahead and enable them"**

## 🎯 第四步：测试运行

### 手动触发测试（推荐）

1. 访问：https://github.com/EseeEhin/cf-ip/actions
2. 点击左侧的 **"Update Optimal IPs"**
3. 点击右侧的 **"Run workflow"** 按钮
4. 保持默认选项，点击绿色的 **"Run workflow"**
5. 刷新页面，查看运行状态

### 查看运行结果

- ✅ 成功：会显示绿色的勾
- ❌ 失败：会显示红色的叉（点击查看详细日志）

## 📊 第五步：获取IP文件链接

运行成功后，访问以下链接获取优选IP：

```
https://raw.githubusercontent.com/EseeEhin/cf-ip/main/优选IP.txt
```

或者直接访问仓库查看文件：
```
https://github.com/EseeEhin/cf-ip/blob/main/优选IP.txt
```

## 🔄 自动更新时间

配置完成后，系统将在以下时间自动更新（北京时间）：
- 🕗 每天 08:00
- 🕑 每天 14:00  
- 🕗 每天 20:00

## 📝 在订阅项目中使用

将raw链接添加到你的订阅转换项目配置中：

```
https://raw.githubusercontent.com/EseeEhin/cf-ip/main/优选IP.txt
```

## 🎨 可选配置

### 修改国家列表

如果想获取其他国家的IP，添加Secret：

- **Name**: `FILTER_COUNTRIES`
- **Value**: `JP,US,SG,HK,TW,KR` （根据需要修改）

### 修改每个国家的IP数量

- **Name**: `QUERY_LIMIT`
- **Value**: `100` （默认值，可修改为50、200等）

### Cloudflare节点真实位置检测

项目支持通过CF-RAY检测获取Cloudflare节点的真实数据中心位置。

#### 功能说明

- ✅ **自动启用**：默认已启用，无需额外配置
- 🌍 **全球覆盖**：支持100+个Cloudflare数据中心
- 🎯 **精确定位**：显示真实的国家和城市（如：JP-Tokyo、HK-Hong Kong）
- 🔄 **自动回退**：检测失败时自动回退到CF-Anycast标记

#### 启用方法

默认已启用，无需额外配置。

#### 禁用方法

如果需要禁用CF-RAY检测，在`.env`文件中设置：

```env
CF_RAY_DETECTION_ENABLED=false
```

#### 效果对比

**启用前**：
```
104.16.132.229:443#A-CF-Anycast
```

**启用后**：
```
104.16.132.229:443#A-JP-Tokyo
```

#### 详细说明

更多配置选项和技术细节，请参考：[CF_RAY_DETECTION.md](CF_RAY_DETECTION.md)

## ❓ 常见问题

### Q: Actions运行失败怎么办？

**检查清单**：
1. ✅ 确认已添加 `GH_TOKEN` Secret
2. ✅ 确认Token有 `repo` 权限
3. ✅ 确认 `TARGET_REPO` 值为 `EseeEhin/cf-ip`
4. ✅ 查看Actions日志中的具体错误

### Q: 如何查看详细日志？

1. 访问：https://github.com/EseeEhin/cf-ip/actions
2. 点击任意运行记录
3. 点击 **"update-ips"** 查看详细步骤
4. 展开每个步骤查看输出

### Q: 如何修改更新频率？

编辑文件：`.github/workflows/update-ips.yml`

找到这一行：
```yaml
- cron: '0 0,6,12 * * *'  # 当前：8:00, 14:00, 20:00
```

修改为你需要的时间（注意：使用UTC时间，北京时间-8小时）

## 📚 更多文档

- 📖 [详细配置指南](SETUP_GUIDE.md)
- 🏗️ [架构设计文档](ARCHITECTURE.md)
- 📋 [实施计划](IMPLEMENTATION_PLAN.md)
- 📘 [完整README](README.md)

## 🎉 完成！

配置完成后，你的优选IP将自动更新，无需手动操作！

---

**需要帮助？** 
- 查看详细文档：[SETUP_GUIDE.md](SETUP_GUIDE.md)
- 提交Issue：https://github.com/EseeEhin/cf-ip/issues