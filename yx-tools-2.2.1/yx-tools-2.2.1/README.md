# Cloudflare SpeedTest 跨平台自动化工具

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个功能强大的跨平台Cloudflare测速工具，支持全球97个数据中心机场码映射，提供常规测速和优选反代功能。

## 主要功能

### 常规测速
- **全球97个数据中心** - 支持完整的Cloudflare机场码映射
- **智能测速** - 自动下载最新IP列表，支持自定义参数
- **结果分析** - 生成详细的CSV格式测速报告

### 优选反代
- **CSV文件处理** - 从测速结果中提取最优IP
- **反代列表生成** - 自动生成`ips_ports.txt`反代配置
- **多格式支持** - 兼容各种CSV文件格式

## 支持平台

| 平台 | 架构 | 状态 |
|------|------|------|
| **Windows** | x64 | 完全支持 |
| **Windows** | ARM64 | 完全支持 |
| **macOS** | Intel | 完全支持 |
| **macOS** | Apple Silicon | 完全支持 |
| **Linux** | x64 | 完全支持 |
| **Linux** | ARM64 | 完全支持 |

## 快速开始

### 方法一：直接运行（推荐）

```bash
# 克隆项目
git clone https://github.com/byJoey/yx-tools.git
cd yx-tools


# 安装依赖
pip install -r requirements.txt

# 运行程序
python3 cloudflare_speedtest.py
```

### 方法二：使用预编译版本

从 [Releases](https://github.com/byJoey/yx-tools/releases) 页面下载对应平台的可执行文件：

- `CloudflareSpeedTest-windows-amd64.exe` - Windows x64
- `CloudflareSpeedTest-macos-amd64` - macOS Intel
- `CloudflareSpeedTest-macos-arm64` - macOS Apple Silicon
- `CloudflareSpeedTest-linux-amd64` - Linux x64
- `CloudflareSpeedTest-linux-arm64` - Linux ARM64

## 使用指南

### 1. 常规测速
mac Linux
```bash
chmod 755 可执行文件拽到终端回车
可执行文件拽到终端回车
如果还是不行 请执行sudo spctl --master-disable
依然不行 xattr -d com.apple.quarantine 可执行文件拽到终端回车
```


选择功能：
```
功能选择:
  1. 常规测速 - 测试指定机场码的IP速度
  2. 优选反代 - 从CSV文件生成反代IP列表

请选择功能 [默认: 1]: 1
```

#### 机场码选择
- 输入机场码：`HKG` (香港)
- 输入城市名：`香港` 或 `Hong Kong`
- 查看完整列表：输入 `LIST`

#### 自定义参数
```
自定义配置:
请输入要测试的IP数量 [默认: 10]: 20
请输入下载速度下限 (MB/s) [默认: 10]: 50
请输入延迟上限 (ms) [默认: 200]: 100
请输入测速时间限制 (秒) [默认: 10]: 15
```

### 2. 优选反代

```bash
python3 cloudflare_speedtest.py
```

选择功能：
```
功能选择:
  1. 常规测速 - 测试指定机场码的IP速度
  2. 优选反代 - 从CSV文件生成反代IP列表

请选择功能 [默认: 1]: 2
```

#### CSV文件处理
```
优选反代模式
==================================================
此功能将从CSV文件中提取IP和端口信息，生成反代IP列表
CSV文件格式要求：
  - 包含 'IP 地址' 和 '端口' 列
  - 或包含 'ip' 和 'port' 列
  - 支持逗号分隔的CSV格式
==================================================

请输入CSV文件路径 [默认: result.csv]: 
```

## 输出文件

### 测速结果 (result.csv)
```csv
IP 地址,端口,延迟,下载速度 (MB/s),上传速度 (MB/s)
1.2.3.4,443,10.5,150.2,120.8
5.6.7.8,80,15.2,200.1,180.5
```

### 反代列表 (ips_ports.txt)
```
1.2.3.4:443
5.6.7.8:80
9.10.11.12:8080
```

## 支持的机场码

### 亚太地区
- **HKG** - 香港
- **NRT** - 东京
- **SIN** - 新加坡
- **SYD** - 悉尼
- **ICN** - 首尔
- **TPE** - 台北

### 欧洲地区
- **LHR** - 伦敦
- **FRA** - 法兰克福
- **AMS** - 阿姆斯特丹
- **CDG** - 巴黎
- **MAD** - 马德里
- **FCO** - 罗马

### 美洲地区
- **LAX** - 洛杉矶
- **SFO** - 旧金山
- **DFW** - 达拉斯
- **ORD** - 芝加哥
- **JFK** - 纽约
- **YYZ** - 多伦多

> 完整列表包含97个全球数据中心，支持所有主要城市和地区。

## 高级配置

### 环境变量
```bash
# 设置默认机场码
export DEFAULT_AIRPORT=HKG

# 设置默认IP数量
export DEFAULT_IP_COUNT=20

# 设置默认速度阈值
export DEFAULT_SPEED_LIMIT=50
```

### 配置文件
创建 `config.json` 文件：
```json
{
  "default_airport": "HKG",
  "default_ip_count": 20,
  "default_speed_limit": 50,
  "default_delay_limit": 200,
  "default_time_limit": 10
}
```

## 开发说明

### 项目结构
```
cloudflare-speedtest/
├── cloudflare_speedtest.py    # 主程序
├── requirements.txt            # 依赖文件
├── .github/
│   └── workflows/
│       └── build-all-platforms.yml  # 自动构建
├── README.md                   # 说明文档
└── LICENSE                     # 许可证
```



## 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 报告问题
如果您发现任何问题，请：
1. 检查 [Issues](https://github.com/your-username/cloudflare-speedtest/issues) 是否已存在
2. 创建新的 Issue，详细描述问题
3. 提供系统信息和错误日志

## 更新日志

### v1.0.0 
- 初始版本发布
- 支持97个全球数据中心
- 常规测速功能
- 优选反代功能
- 跨平台支持
- 预编译可执行文件

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 致谢

- [Cloudflare](https://www.cloudflare.com/) - 提供全球CDN服务
- [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest) - 原始测速工具
- 所有贡献者和用户的支持


---

**如果这个项目对您有帮助，请给我们一个星标！**
