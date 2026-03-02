# VPN 半自动化系统部署总结

## 当前状态

### ✅ 已完成

1. **VPN 监控脚本** (`vpn-monitor.sh`)
   - 每 60 秒检查 VPN 连接状态
   - 检测到断开时自动启动 FortiClient GUI
   - 发送飞书通知
   - 集成 GUI 自动化（待测试）

2. **GUI 自动化脚本** (`gui-auto-connect.py`)
   - 基于图像识别的按钮点击
   - 使用 PyAutoGUI + OpenCV
   - 支持多图像匹配和重试

3. **按钮捕获工具** (`capture-button.py`)
   - 交互式捕获连接按钮图像
   - 支持全屏截图调试

4. **systemd 服务配置** (`vpn-monitor.service`)
   - 开机自启动
   - 自动重启
   - 环境变量配置

5. **完整文档**
   - GUI-AUTOMATION-GUIDE.md
   - QUICKSTART.md
   - README.md

### ⏸️ 待完成

1. **安装 GUI 自动化依赖**

   ```bash
   cd /home/tsl/openclaw/vpn-auto
   ./install-gui-automation.sh
   ```

   需要安装：
   - opencv-python-headless
   - scrot
   - python3-tk

2. **解决 X11 权限问题**

   ```bash
   xhost +local:
   # 或
   xhost +SI:localuser:tsl
   ```

3. **捕获连接按钮图像**

   ```bash
   python3 capture-button.py
   ```

4. **测试 GUI 自动化**

   ```bash
   python3 gui-auto-connect.py
   ```

5. **安装并启动监控服务**
   ```bash
   cd /home/tsl/openclaw/vpn-auto
   ./install-monitor.sh
   sudo systemctl start vpn-monitor
   ```

## 当前工作方式

### 方案 A：命令行触发（已可用）

```bash
# VPN 断开时
forticlient vpn connect vpn-krgc.dasanns.com

# 状态变为 "Connecting..."
# 用户在手机上完成 MFA 认证
# VPN 连接成功
```

**优点**：

- ✅ 无需额外依赖
- ✅ 已集成到监控脚本
- ✅ 可以立即使用

**缺点**：

- ❌ 需要 FortiClient GUI 已打开
- ❌ 可能需要手动点击连接按钮

### 方案 B：GUI 自动化（待测试）

```bash
# VPN 断开时
python3 gui-auto-connect.py

# 自动启动 FortiClient GUI
# 图像识别查找连接按钮
# 自动点击连接按钮
# 用户在手机上完成 MFA 认证
# VPN 连接成功
```

**优点**：

- ✅ 完全自动化（除 MFA）
- ✅ 无需手动操作
- ✅ 图像识别更可靠

**缺点**：

- ❌ 需要图形界面
- ❌ 需要 X11 权限
- ❌ 需要捕获按钮图像

## 测试结果

### 依赖检查

| 依赖        | 状态                | 说明         |
| ----------- | ------------------- | ------------ |
| Python 3.8  | ✅ 已安装           |              |
| pyautogui   | ⚠️ 已安装但无法使用 | X11 权限问题 |
| opencv      | ❌ 未安装           | 需要安装     |
| PIL/Pillow  | ✅ 已安装           |              |
| scrot       | ❌ 未安装           | 需要安装     |
| FortiClient | ✅ 已安装           |              |

### X11 权限问题

```
错误: Can't connect to display ":0": b'No protocol specified\n'
```

**原因**：systemd 服务无法访问用户的 X11 显示

**解决方案**：

1. 允许本地用户访问 X11：

   ```bash
   xhost +SI:localuser:tsl
   ```

2. 或在用户会话中运行（不使用 systemd）：
   ```bash
   # 在终端中直接运行
   ./vpn-monitor.sh
   ```

## 推荐部署方案

### 方案 1：简化版（推荐，立即可用）

使用命令行触发 + 飞书通知：

```bash
cd /home/tsl/openclaw/vpn-auto
./install-monitor.sh
sudo systemctl start vpn-monitor
```

**工作流程**：

1. 监控检测到 VPN 断开
2. 自动运行 `forticlient vpn connect`
3. 发送飞书通知
4. 用户在手机上完成 MFA
5. VPN 连接成功

### 方案 2：完整版（需要额外配置）

GUI 自动化 + 飞书通知：

```bash
# 1. 安装依赖
cd /home/tsl/openclaw/vpn-auto
./install-gui-automation.sh

# 2. 解决 X11 权限
xhost +SI:localuser:tsl

# 3. 捕获按钮图像
python3 capture-button.py

# 4. 测试
python3 gui-auto-connect.py

# 5. 安装服务
./install-monitor.sh
sudo systemctl start vpn-monitor
```

## 下一步行动

### 立即可用（方案 1）

```bash
cd /home/tsl/openclaw/vpn-auto
./install-monitor.sh
```

按提示操作，启动监控服务。

### 完整功能（方案 2）

需要在有图形界面的环境下：

1. 登录到图形界面（桌面环境）
2. 运行 `xhost +SI:localuser:tsl`
3. 运行 `./quick-setup.sh`
4. 按提示捕获按钮图像
5. 测试并安装服务

## 文件清单

### 核心脚本

- `vpn-monitor.sh` - VPN 监控主脚本
- `gui-auto-connect.py` - GUI 自动化脚本
- `capture-button.py` - 按钮图像捕获工具

### 安装脚本

- `install-monitor.sh` - 监控服务安装
- `install-gui-automation.sh` - GUI 依赖安装
- `quick-setup.sh` - 一键设置

### 测试脚本

- `test-monitor.sh` - 监控功能测试
- `test-auto-connect.sh` - 自动连接测试
- `test-gui-deps.sh` - GUI 依赖测试

### 配置文件

- `vpn-monitor.service` - systemd 服务配置

### 文档

- `GUI-AUTOMATION-GUIDE.md` - GUI 自动化指南
- `QUICKSTART.md` - 快速开始
- `README.md` - 完整文档

## 常见问题

### Q1: 为什么需要 MFA？

A: 公司启用了 Microsoft 多因素认证（MFA），这是安全策略要求，无法绕过。

### Q2: 能否完全自动化？

A: 不能。MFA 需要手动完成（手机批准或输入验证码）。但可以自动化其他所有步骤。

### Q3: GUI 自动化失败怎么办？

A: 系统会自动回退到命令行方式（`forticlient vpn connect`），仍然可以触发连接。

### Q4: 如何查看日志？

A:

```bash
# 系统日志
journalctl -u vpn-monitor -f

# 文件日志
tail -f /home/tsl/openclaw/vpn-auto/monitor.log
```

### Q5: 如何停止服务？

A:

```bash
sudo systemctl stop vpn-monitor
sudo systemctl disable vpn-monitor
```

## 总结

VPN 半自动化系统已经完成开发和基础测试。核心功能（监控 + 命令行触发 + 飞书通知）可以立即使用。GUI 自动化功能需要在图形界面环境下进一步配置和测试。

**推荐行动**：先部署方案 1（简化版），确保基本功能正常，然后在有图形界面时再配置方案 2（完整版）。

---

**创建时间**: 2026-03-02 14:45  
**状态**: 核心功能已完成，GUI 自动化待测试  
**下一步**: 安装监控服务并测试基本功能
