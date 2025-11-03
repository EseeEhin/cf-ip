# Cloudflare SpeedTest 非交互式运行指南

## 概述

[`run_speedtest.py`](run_speedtest.py:1) 是一个包装脚本，用于在 GitHub Actions 或其他自动化环境中非交互式运行 [`cloudflare_speedtest.py`](cloudflare_speedtest.py:1)。

## 为什么需要这个脚本？

原始的 [`cloudflare_speedtest.py`](cloudflare_speedtest.py:1) 脚本设计为交互式使用，需要用户输入多个参数。在 GitHub Actions 等自动化环境中，无法进行交互式输入，导致脚本运行失败。

[`run_speedtest.py`](run_speedtest.py:1) 解决了这个问题，通过命令行参数提供所有必要的配置，并自动将输入传递给原始脚本。

## 功能特性

- ✅ **完全非交互式**：所有参数通过命令行指定
- ✅ **自动化友好**：适用于 GitHub Actions、cron 任务等
- ✅ **参数验证**：提供清晰的参数说明和默认值
- ✅ **结果展示**：自动显示测速结果摘要
- ✅ **错误处理**：完善的超时和异常处理

## 使用方法

### 基本用法

```bash
# 使用默认参数（IPv4，小白模式，30个节点，300ms延迟，5MB/s速度）
python run_speedtest.py
```

### 自定义参数

```bash
# 测试 50 个节点，延迟上限 200ms，速度下限 10MB/s
python run_speedtest.py --dn-count 50 --time-limit 200 --speed-limit 10
```

### 使用 IPv6

```bash
python run_speedtest.py --ip-version 2
```

### 指定机场码

```bash
# 测试东京节点
python run_speedtest.py --airport-code NRT --dn-count 20
```

## 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--ip-version` | int | 1 | IP版本：1=IPv4, 2=IPv6 |
| `--function` | int | 1 | 功能选择：1=小白快速测试, 2=常规测速, 3=优选反代 |
| `--airport-code` | str | HKG | 机场码（如：HKG, NRT, LAX） |
| `--config` | int | 4 | 配置：1=快速, 2=标准, 3=高质量, 4=自定义 |
| `--dn-count` | int | 30 | 下载节点数量 |
| `--time-limit` | int | 300 | 延迟上限（毫秒） |
| `--speed-limit` | int | 5 | 速度下限（MB/s） |

## 常用场景

### 1. 快速测试（10个节点）

```bash
python run_speedtest.py --dn-count 10 --time-limit 1000 --speed-limit 1
```

### 2. 标准测试（20个节点）

```bash
python run_speedtest.py --dn-count 20 --time-limit 500 --speed-limit 5
```

### 3. 高质量测试（50个节点）

```bash
python run_speedtest.py --dn-count 50 --time-limit 200 --speed-limit 10
```

### 4. 测试多个地区

```bash
# 香港
python run_speedtest.py --airport-code HKG --dn-count 30
mv result.csv result_hkg.csv

# 东京
python run_speedtest.py --airport-code NRT --dn-count 30
mv result.csv result_nrt.csv

# 洛杉矶
python run_speedtest.py --airport-code LAX --dn-count 30
mv result.csv result_lax.csv
```

## GitHub Actions 集成

在 [`.github/workflows/update-ips.yml`](.github/workflows/update-ips.yml:1) 中使用：

```yaml
- name: Run speedtest
  run: |
    cd yx-tools-2.2.1/yx-tools-2.2.1
    
    # 测试香港节点
    python run_speedtest.py --airport-code HKG --dn-count 30 --time-limit 300 --speed-limit 5
    mv result.csv ../../result_hkg.csv
    
    # 测试东京节点
    python run_speedtest.py --airport-code NRT --dn-count 30 --time-limit 300 --speed-limit 5
    mv result.csv ../../result_nrt.csv
```

## 输出文件

脚本运行成功后会生成：

- **result.csv**：测速结果文件，包含所有优选IP的详细信息
  - 格式：IP地址,端口,延迟平均值,下载速度,上传速度

## 注意事项

### 1. 功能模式说明

- **小白快速测试（推荐）**：`--function 1`
  - 无需选择地区，自动测试所有可用IP
  - 适合自动化场景
  - 默认使用此模式

- **常规测速**：`--function 2`
  - 需要交互式选择地区
  - 在非交互环境中会自动切换到小白模式
  - 不推荐在自动化中使用

- **优选反代**：`--function 3`
  - 从已有的 result.csv 生成反代IP列表
  - 需要先运行测速生成 result.csv

### 2. 超时设置

脚本默认超时时间为 10 分钟。如果测试节点数量较多，可能需要更长时间。

### 3. 依赖要求

确保已安装必要的依赖：

```bash
pip install requests
```

### 4. 权限问题

在 Linux/macOS 上，可能需要给脚本添加执行权限：

```bash
chmod +x run_speedtest.py
```

## 故障排除

### 问题：脚本运行超时

**解决方案**：减少测试节点数量或增加超时时间

```bash
python run_speedtest.py --dn-count 10  # 减少到10个节点
```

### 问题：未找到 cloudflare_speedtest.py

**解决方案**：确保在正确的目录下运行脚本

```bash
cd yx-tools-2.2.1/yx-tools-2.2.1
python run_speedtest.py
```

### 问题：未生成 result.csv

**解决方案**：检查网络连接和测速参数是否合理

```bash
# 使用更宽松的参数
python run_speedtest.py --time-limit 1000 --speed-limit 1
```

## 技术实现

[`run_speedtest.py`](run_speedtest.py:1) 通过以下方式实现非交互式运行：

1. **参数解析**：使用 [`argparse`](run_speedtest.py:1) 解析命令行参数
2. **输入模拟**：将所有交互式输入预先准备好
3. **进程通信**：通过 [`subprocess.run()`](run_speedtest.py:1) 的 `input` 参数传递输入
4. **结果处理**：自动检查和展示测速结果

## 相关文件

- [`cloudflare_speedtest.py`](cloudflare_speedtest.py:1) - 原始测速脚本
- [`run_speedtest.py`](run_speedtest.py:1) - 非交互式包装脚本
- [`.github/workflows/update-ips.yml`](.github/workflows/update-ips.yml:1) - GitHub Actions 工作流

## 许可证

本脚本遵循与原始 yx-tools 项目相同的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0 (2025-11-03)

- ✨ 初始版本
- ✅ 支持完全非交互式运行
- ✅ 支持所有主要参数配置
- ✅ 集成到 GitHub Actions