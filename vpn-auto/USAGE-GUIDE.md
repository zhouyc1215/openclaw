# VPN 自动点击使用指南

## 快速开始

### 方法 1: 简化版本（推荐）

假设 FortiClient 已经在运行：

```bash
cd vpn-auto
bash test-simple.sh
```

### 方法 2: 完整版本（包含重启）

自动重启 FortiClient 并点击：

```bash
cd vpn-auto
bash test-complete-flow.sh
```

## 使用说明

### 前提条件

1. FortiClient 已安装
2. X11 显示服务器运行在 DISPLAY :1
3. 已安装所有依赖：
   - Python 3.8+
   - opencv-python
   - pytesseract
   - xdotool
   - scrot

### 手动启动 FortiClient

如果使用简化版本，需要先手动启动 FortiClient：

```bash
DISPLAY=:1 /usr/bin/forticlient gui &
```

等待 10-15 秒让 GUI 完全加载。

### 运行脚本

#### 选项 A: 简化版（推荐）

```bash
cd vpn-auto
python3 simple-click-button.py
```

**优点：**

- 不会重启 FortiClient
- 运行速度快
- 更稳定

**缺点：**

- 需要手动启动 FortiClient
- 需要手动调整窗口大小（如果太小）

#### 选项 B: 完整版

```bash
cd vpn-auto
python3 smart-find-button.py
```

**优点：**

- 自动启动 FortiClient
- 自动调整窗口大小
- 完全自动化

**缺点：**

- 启动时间较长（~20秒）
- 可能不稳定

## 常见问题

### Q1: VPN 未连接怎么办？

**A:** 点击 SAML Login 按钮后，通常需要在浏览器中完成认证：

1. 检查是否打开了浏览器窗口
2. 在浏览器中输入用户名密码
3. 完成 MFA 认证（如果需要）
4. 等待浏览器重定向回 FortiClient
5. VPN 自动连接

### Q2: 找不到按钮怎么办？

**A:** 检查以下几点：

1. FortiClient 窗口是否打开
2. 窗口是否太小（应该至少 800x600）
3. SAML Login 按钮是否可见
4. 运行调试脚本查看详情：
   ```bash
   bash debug-step-by-step.sh
   ```

### Q3: 窗口太小怎么办？

**A:** 手动调整窗口大小：

```bash
bash maximize-forticlient.sh
```

或者使用完整版脚本，会自动调整。

### Q4: 如何查看详细日志？

**A:** 所有脚本都会输出详细日志到终端。

查看 FortiClient 启动日志：

```bash
tail -f /tmp/forticlient-gui-debug.log
```

## 调试工具

### 1. 逐步调试

```bash
bash debug-step-by-step.sh
```

显示每一步的详细信息，包括：

- FortiClient 进程状态
- 窗口信息
- 截图
- X11 显示状态

### 2. 检查状态

```bash
bash check-forticlient-status.sh
```

显示当前状态：

- FortiClient 进程
- VPN 进程
- VPN 接口
- 截图

### 3. 调整窗口

```bash
bash maximize-forticlient.sh
```

手动调整 FortiClient 窗口大小和位置。

### 4. 分析截图

```bash
python3 analyze-screenshots.py
```

分析截图，对比点击前后的变化。

### 5. 识别按钮文字

```bash
python3 identify-button-text.py
```

使用 OCR 识别按钮上的文字。

## 脚本说明

### 核心脚本

| 脚本                     | 说明           | 用途             |
| ------------------------ | -------------- | ---------------- |
| `simple-click-button.py` | 简化版点击脚本 | 日常使用（推荐） |
| `smart-find-button.py`   | 完整版点击脚本 | 完全自动化       |
| `test-simple.sh`         | 简化测试脚本   | 快速测试         |
| `test-complete-flow.sh`  | 完整测试脚本   | 完整流程测试     |

### 调试脚本

| 脚本                          | 说明     |
| ----------------------------- | -------- |
| `debug-step-by-step.sh`       | 逐步调试 |
| `check-forticlient-status.sh` | 状态检查 |
| `maximize-forticlient.sh`     | 窗口调整 |
| `analyze-screenshots.py`      | 截图分析 |
| `identify-button-text.py`     | 文字识别 |

## 配置参数

### 环境变量

```bash
DISPLAY=:1  # X11 显示服务器
```

### 按钮识别参数

```python
# HSV 颜色范围（深蓝色）
BLUE_LOWER = [100, 100, 100]
BLUE_UPPER = [130, 255, 255]

# 按钮尺寸范围
MIN_BUTTON_AREA = 2000
MAX_BUTTON_AREA = 50000
MIN_BUTTON_WIDTH = 80
MAX_BUTTON_WIDTH = 300
MIN_BUTTON_HEIGHT = 25
MAX_BUTTON_HEIGHT = 80
```

### 窗口配置

```python
# 窗口大小
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# 窗口位置
WINDOW_X = 100
WINDOW_Y = 100
```

## 工作流程

### 简化版工作流程

1. 检查 FortiClient 是否运行
2. 检查窗口大小（如果太小则调整）
3. 截图
4. 查找 SAML Login 按钮
5. 移动光标到按钮
6. 点击按钮
7. 按 Enter 键

### 完整版工作流程

1. 停止旧的 FortiClient 进程
2. 启动新的 FortiClient GUI
3. 等待窗口出现（最多30秒）
4. 等待 GUI 完全加载（10秒）
5. 调整窗口大小和位置
6. 激活窗口
7. 截图
8. 查找 SAML Login 按钮
9. 移动光标到按钮
10. 点击按钮
11. 按 Enter 键

## 已知限制

1. **VPN 连接需要手动认证**
   - SAML 认证需要在浏览器中完成
   - 需要手动输入用户名密码
   - 需要手动完成 MFA 认证

2. **窗口大小问题**
   - FortiClient 初始窗口可能只有 10x10 像素
   - 需要手动或自动调整窗口大小

3. **X11 显示**
   - 必须在 X11 环境中运行
   - DISPLAY 必须设置为 :1

## 下一步改进

如果需要完全自动化 VPN 连接，可以考虑：

1. **浏览器自动化**
   - 使用 Selenium 或 Playwright
   - 自动完成 SAML 认证
   - 自动输入用户名密码
   - 自动完成 MFA 认证

2. **使用命令行工具**
   - 使用 `openfortivpn` 直接连接
   - 不需要 GUI
   - 更稳定可靠

3. **监控和重试**
   - 监控 VPN 连接状态
   - 自动重试失败的连接
   - 发送通知

## 支持

如有问题，请查看：

- `FINAL-SUMMARY.md` - 项目总结
- `FINAL-ANALYSIS.md` - 详细分析
- `SCREENSHOT-ANALYSIS-REPORT.md` - 截图分析

或运行调试脚本获取更多信息。
