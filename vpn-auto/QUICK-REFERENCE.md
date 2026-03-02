# VPN 自动重连系统 - 快速参考

## 🚀 一键部署

```bash
cd /home/tsl/openclaw/vpn-auto
export DISPLAY=:1
./deploy-complete.sh
```

## 📊 系统状态

```bash
# 查看服务状态
sudo systemctl status vpn-monitor

# 查看实时日志
journalctl -u vpn-monitor -f

# 查看最近 50 条日志
journalctl -u vpn-monitor -n 50 --no-pager
```

## 🔧 服务管理

```bash
# 启动服务
sudo systemctl start vpn-monitor

# 停止服务
sudo systemctl stop vpn-monitor

# 重启服务
sudo systemctl restart vpn-monitor

# 启用开机自启
sudo systemctl enable vpn-monitor

# 禁用开机自启
sudo systemctl disable vpn-monitor
```

## 🧪 手动测试

```bash
# 测试 GUI 自动连接
cd /home/tsl/openclaw/vpn-auto
export DISPLAY=:1
python3 gui-auto-connect.py

# 测试 VPN 状态检测
forticlient vpn status

# 测试外网连接
curl -s --connect-timeout 3 https://www.google.com
```

## 🖼️ 重新捕获按钮图像

```bash
cd /home/tsl/openclaw/vpn-auto
export DISPLAY=:1
python3 capture-button.py
```

**操作步骤：**

1. 确保 FortiClient 窗口打开且处于"未连接"状态
2. 运行上面的命令
3. 按照提示，将鼠标移动到连接按钮的左上角，按 Enter
4. 将鼠标移动到连接按钮的右下角，按 Enter
5. 图像会保存到 `images/connect_button.png`

## 📁 重要文件

```
vpn-auto/
├── deploy-complete.sh          # 一键部署脚本
├── vpn-monitor.sh              # 监控主脚本
├── gui-auto-connect.py         # GUI 自动化
├── capture-button.py           # 按钮捕获工具
├── images/
│   └── connect_button.png      # 按钮图像模板
└── debug_screen.png            # 调试截图
```

## 🔍 故障排查

### 服务无法启动

```bash
# 查看详细错误
sudo systemctl status vpn-monitor
journalctl -u vpn-monitor -n 100 --no-pager

# 检查脚本权限
ls -l /home/tsl/openclaw/vpn-auto/vpn-monitor.sh

# 手动运行脚本测试
cd /home/tsl/openclaw/vpn-auto
export DISPLAY=:1
./vpn-monitor.sh
```

### GUI 自动化失败

```bash
# 查看调试截图
ls -lh /home/tsl/openclaw/vpn-auto/debug_screen.png

# 检查 X11 权限
echo $DISPLAY
xhost

# 重新配置 X11 权限
export DISPLAY=:1
xhost +SI:localuser:tsl

# 重新捕获按钮图像
python3 capture-button.py
```

### 飞书通知失败

```bash
# 测试飞书消息发送
cd /home/tsl/openclaw
pnpm openclaw message send \
  --channel feishu \
  --target ou_b3afb7d2133e4d689be523fc48f3d2b3 \
  --message "测试消息"

# 检查 Gateway 状态
pnpm openclaw channels status
```

### VPN 连接失败

```bash
# 手动连接 VPN
forticlient vpn connect

# 查看 VPN 状态
forticlient vpn status

# 查看 FortiClient 进程
ps aux | grep -i forti
```

## ⚙️ 配置调整

### 修改检查间隔

编辑 `vpn-monitor.sh`，修改 `SLEEP_INTERVAL` 变量：

```bash
SLEEP_INTERVAL=60  # 改为你想要的秒数
```

### 修改飞书用户 ID

编辑 `vpn-monitor.sh`，修改 `FEISHU_USER_ID` 变量：

```bash
FEISHU_USER_ID="ou_b3afb7d2133e4d689be523fc48f3d2b3"
```

### 修改图像识别参数

编辑 `gui-auto-connect.py`，修改以下参数：

```python
CONFIDENCE = 0.8      # 识别置信度（0.0-1.0）
MAX_RETRIES = 3       # 最大重试次数
RETRY_DELAY = 2       # 重试间隔（秒）
```

## 📈 性能指标

- 检查间隔：60秒
- VPN 状态检测：< 1秒
- 外网连接检测：3-5秒
- GUI 自动化：2-10秒
- 飞书通知：2-3秒
- 总响应时间：< 20秒

## 🎯 系统架构

```
监控循环（每60秒）
  ↓
检测 VPN 状态
  ↓
检测外网连接
  ↓
如果断开 → 启动 FortiClient
  ↓
尝试 GUI 自动化（图像识别）
  ↓
失败 → 回退到命令行
  ↓
发送飞书通知
  ↓
等待 MFA 认证（人工）
```

## 📚 相关文档

- `DEPLOYMENT-TEST-REPORT.md` - 完整部署测试报告
- `GUI-AUTO-TEST-SUCCESS.md` - GUI 自动化测试成功报告
- `GUI-AUTOMATION-GUIDE.md` - GUI 自动化完整指南
- `MANUAL-SETUP-GUIDE.md` - 手动配置指南
- `VPN-SEMI-AUTO-SUMMARY.md` - 系统总结

## 💡 提示

- GUI 图像识别失败时，系统会自动回退到命令行方式
- MFA 认证需要在手机上手动完成
- 服务异常退出时会自动重启（10秒后）
- 建议定期查看日志确保系统正常运行
