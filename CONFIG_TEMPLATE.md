# 配置文件模板

本文档提供了项目所需的配置文件模板。在实施阶段，需要根据这些模板创建实际的配置文件。

## 1. settings.yaml 配置文件

**文件路径：** `config/settings.yaml`

**文件内容：**

```yaml
# ==================== 数据源配置 ====================
source:
  # 目标网站URL
  url: "https://cfip.wxgqlfx.fun/"
  
  # 要获取的国家/地区列表（使用中文名称）
  countries:
    - "日本"
    - "美国"
    - "香港"
    - "新加坡"
  
  # 每个国家获取的节点数量（10/20/50/100）
  result_count: 20
  
  # 请求超时时间（秒）
  timeout: 30

# ==================== 过滤配置 ====================
filter:
  # 最大延迟阈值（毫秒），超过此值的节点将被过滤
  max_latency: 200
  
  # 最少节点数量，低于此值会记录警告
  min_nodes: 5

# ==================== 输出配置 ====================
output:
  # 输出文件路径（相对于项目根目录）
  file_path: "output/nodes.txt"
  
  # 输出格式：
  #   - ip_port_name: IP:端口#节点名称
  #   - ip_port: IP:端口
  format: "ip_port_name"
  
  # 节点分隔符
  separator: ","

# ==================== GitHub配置 ====================
github:
  # 目标分支
  branch: "main"
  
  # 提交信息模板（{timestamp}会被替换为实际时间）
  commit_message_template: "Update nodes - {timestamp}"

# ==================== 浏览器配置 ====================
browser:
  # 是否使用无头模式（生产环境建议true）
  headless: true
  
  # 页面加载超时时间（秒）
  timeout: 30
  
  # 失败重试次数
  retry_times: 3
  
  # 等待元素出现的最大时间（秒）
  wait_timeout: 10

# ==================== 日志配置 ====================
logging:
  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: "INFO"
  
  # 日志文件路径
  file: "logs/updater.log"
  
  # 单个日志文件最大大小
  max_size: "10MB"
  
  # 保留的日志文件数量
  backup_count: 5
  
  # 日志格式
  format: "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
  
  # 日期格式
  date_format: "%Y-%m-%d %H:%M:%S"
```

---

## 2. requirements.txt 依赖文件

**文件路径：** `requirements.txt`

**文件内容：**

```txt
# ==================== 核心依赖 ====================

# Selenium - 浏览器自动化
selenium==4.15.0

# BeautifulSoup4 - HTML解析
beautifulsoup4==4.12.2

# PyYAML - YAML配置文件解析
pyyaml==6.0.1

# Requests - HTTP请求库
requests==2.31.0

# ==================== 工具库 ====================

# python-dateutil - 日期时间处理
python-dateutil==2.8.2

# lxml - XML/HTML解析器
lxml==4.9.3

# ==================== 测试依赖（可选） ====================

# pytest - 测试框架
pytest==7.4.3

# pytest-cov - 测试覆盖率
pytest-cov==4.1.0

# pytest-mock - Mock工具
pytest-mock==3.12.0
```

---

## 3. GitHub Actions 工作流配置

**文件路径：** `.github/workflows/update-ips.yml`

**文件内容：**

```yaml
name: Update Cloudflare IPs

on:
  # 定时触发（每6小时执行一次）
  schedule:
    - cron: '0 */6 * * *'
  
  # 支持手动触发
  workflow_dispatch:
  
  # 推送到main分支时触发（可选）
  # push:
  #   branches:
  #     - main
  #   paths:
  #     - 'src/**'
  #     - 'config/**'
  #     - 'main.py'

jobs:
  update-ips:
    runs-on: ubuntu-latest
    
    steps:
      # 1. 检出代码
      - name: Checkout repository
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0
      
      # 2. 设置Python环境
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          cache: 'pip'
      
      # 3. 安装Python依赖
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      # 4. 安装Chrome和ChromeDriver
      - name: Install Chrome and ChromeDriver
        run: |
          sudo apt-get update
          sudo apt-get install -y chromium-browser chromium-chromedriver
          chromium-browser --version
          chromedriver --version
      
      # 5. 创建必要的目录
      - name: Create directories
        run: |
          mkdir -p output
          mkdir -p logs
      
      # 6. 运行更新程序
      - name: Run IP updater
        run: |
          python main.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      # 7. 检查是否有变化
      - name: Check for changes
        id: check_changes
        run: |
          if git diff --quiet output/nodes.txt; then
            echo "has_changes=false" >> $GITHUB_OUTPUT
          else
            echo "has_changes=true" >> $GITHUB_OUTPUT
          fi
      
      # 8. 提交和推送更改
      - name: Commit and push changes
        if: steps.check_changes.outputs.has_changes == 'true'
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add output/nodes.txt
          git commit -m "Update nodes - $(date +'%Y-%m-%d %H:%M:%S UTC')"
          git push
      
      # 9. 上传日志（失败时）
      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: logs
          path: logs/
          retention-days: 7
      
      # 10. 输出统计信息
      - name: Output statistics
        if: always()
        run: |
          echo "=== 执行统计 ==="
          if [ -f output/nodes.txt ]; then
            NODE_COUNT=$(grep -o "," output/nodes.txt | wc -l)
            NODE_COUNT=$((NODE_COUNT + 1))
            echo "节点数量: $NODE_COUNT"
            echo "文件大小: $(du -h output/nodes.txt | cut -f1)"
          else
            echo "输出文件不存在"
          fi
```

---

## 4. .gitignore 文件

**文件路径：** `.gitignore`

**文件内容：**

```gitignore
# ==================== Python ====================
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# ==================== 环境 ====================
# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# ==================== 项目特定 ====================
# 日志文件
logs/*.log
logs/*.txt

# 临时文件
*.tmp
*.temp

# 浏览器缓存
.selenium/

# 本地配置（如果有）
config/local.yaml
config/*.local.yaml

# 测试输出
test_output/

# macOS
.DS_Store

# Windows
Thumbs.db
desktop.ini
```

---

## 5. LICENSE 文件

**文件路径：** `LICENSE`

**文件内容：**

```
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 6. 目录占位文件

### 6.1 logs/.gitkeep

**文件路径：** `logs/.gitkeep`

**说明：** 空文件，用于在Git中保留空目录

### 6.2 output/.gitkeep

**文件路径：** `output/.gitkeep`

**说明：** 空文件，用于在Git中保留空目录

---

## 配置说明

### 国家/地区名称对照表

在配置文件中使用中文名称，以下是常用国家的中文名称：

| 中文名称 | 国家代码 | 英文名称 |
|---------|---------|---------|
| 日本 | JP | Japan |
| 美国 | US | United States |
| 香港 | HK | Hong Kong |
| 新加坡 | SG | Singapore |
| 德国 | DE | Germany |
| 英国 | GB | United Kingdom |
| 法国 | FR | France |
| 加拿大 | CA | Canada |
| 澳大利亚 | AU | Australia |
| 韩国 | KR | South Korea |
| 台湾 | TW | Taiwan |
| 荷兰 | NL | Netherlands |

### 结果数量选项

- `10` - 获取10个节点（快速）
- `20` - 获取20个节点（推荐）
- `50` - 获取50个节点（较多）
- `100` - 获取100个节点（最多）

### 延迟阈值建议

- `100ms` - 高质量节点，数量较少
- `200ms` - 平衡质量和数量（推荐）
- `300ms` - 更多节点选择
- `500ms` - 包含大部分节点

### Cron表达式参考

| 表达式 | 说明 | 适用场景 |
|-------|------|---------|
| `0 * * * *` | 每小时 | 实时性要求高 |
| `0 */3 * * *` | 每3小时 | 频繁更新 |
| `0 */6 * * *` | 每6小时 | 推荐配置 |
| `0 */12 * * *` | 每12小时 | 节省资源 |
| `0 0 * * *` | 每天0点 | 数据稳定 |
| `0 0 * * 1` | 每周一0点 | 低频更新 |

---

## 环境变量说明

在GitHub Actions中，以下环境变量会自动设置：

| 变量名 | 说明 | 来源 |
|-------|------|------|
| `GITHUB_TOKEN` | GitHub访问令牌 | GitHub Actions自动提供 |
| `GITHUB_REPOSITORY` | 仓库名称 | GitHub Actions自动提供 |
| `GITHUB_ACTOR` | 触发者用户名 | GitHub Actions自动提供 |

---

## 配置验证清单

在实施阶段，请确保：

- [ ] `config/settings.yaml` 文件已创建并配置正确
- [ ] `requirements.txt` 文件已创建
- [ ] `.github/workflows/update-ips.yml` 文件已创建
- [ ] `.gitignore` 文件已创建
- [ ] `LICENSE` 文件已创建
- [ ] `logs/` 目录已创建
- [ ] `output/` 目录已创建
- [ ] GitHub Actions已启用
- [ ] 配置的国家名称使用中文
- [ ] 结果数量设置为20
- [ ] 延迟阈值设置为200ms
- [ ] Cron表达式配置正确

---

## 下一步操作

完成架构设计后，切换到Code模式进行实施：

1. 创建所有配置文件
2. 实现核心模块代码
3. 编写测试用例
4. 本地测试验证
5. 部署到GitHub Actions
6. 监控运行状态
