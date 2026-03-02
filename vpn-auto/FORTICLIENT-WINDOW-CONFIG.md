# FortiClient GUI 窗口配置

## 问题

FortiClient GUI 在 VPN 连接成功后会自动最小化或关闭窗口。

## 解决方案

### 方案 1: 修改 Preferences 配置 ⚠️

尝试在 `~/.config/FortiClient/Preferences` 中添加窗口配置：

```json
{
  "window": {
    "minimize_on_connect": false,
    "close_to_tray": false,
    "start_minimized": false
  },
  "vpn": {
    "auto_minimize": false,
    "keep_window_open": true
  }
}
```

**注意：** 这些配置项可能不是 FortiClient 实际使用的键名，效果不确定。

### 方案 2: 使用窗口管理器规则 ✅（推荐）

使用 `wmctrl` 和 `xdotool` 来控制窗口行为：

#### 1. 一次性配置窗口

```bash
cd /home/tsl/openclaw/vpn-auto
./keep-forticlient-open.sh
```

这个脚本会：

- 查找 FortiClient 窗口
- 激活窗口
- 设置为 sticky（在所有工作区显示）
- 设置为 above（始终在上层）
- 移动到可见位置 (100, 100)
- 设置窗口大小为 800x600

#### 2. 持续监控窗口状态

```bash
cd /home/tsl/openclaw/vpn-auto
./monitor-forticlient-window.sh
```

这个脚本会：

- 每 2 秒检查窗口状态
- 如果窗口被最小化，自动恢复
- 持续运行直到手动停止（Ctrl+C）

## 使用方法

### 启动 FortiClient GUI

```bash
export DISPLAY=:1
/opt/forticlient/gui/FortiClient &
```

### 配置窗口保持打开

```bash
cd /home/tsl/openclaw/vpn-auto
./keep-forticlient-open.sh
```

### 可选：启动窗口监控

```bash
cd /home/tsl/openclaw/vpn-auto
./monitor-forticlient-window.sh
```

## 集成到自动化系统

### 在 vpn-monitor.sh 中添加

```bash
# 确保 FortiClient GUI 运行
if ! pgrep -f "FortiClient" > /dev/null; then
    export DISPLAY=:1
    /opt/forticlient/gui/FortiClient &
    sleep 3
fi

# 配置窗口
/home/tsl/openclaw/vpn-auto/keep-forticlient-open.sh
```

### 创建 systemd 服务（可选）

```ini
[Unit]
Description=FortiClient Window Monitor
After=graphical.target

[Service]
Type=simple
User=tsl
Environment="DISPLAY=:1"
ExecStart=/home/tsl/openclaw/vpn-auto/monitor-forticlient-window.sh
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
```

## 依赖工具

### 已安装 ✅

- `xdotool` - X11 自动化工具
- `wmctrl` - 窗口管理器控制工具

### 安装命令（如果需要）

```bash
sudo apt-get install -y xdotool wmctrl
```

## 测试结果

### 当前状态

- ✅ FortiClient GUI 已启动 (PID: 1083475)
- ✅ 窗口 ID: 33554433
- ✅ 窗口已配置为 sticky + above
- ✅ 窗口位置: (100, 100)
- ✅ 窗口大小: 800x600

### 窗口属性

```bash
# 查看窗口状态
xprop -id 33554433 _NET_WM_STATE

# 查看窗口几何信息
xdotool getwindowgeometry 33554433
```

## 限制和注意事项

1. **窗口管理器依赖**
   - 这些设置依赖于 X11 窗口管理器
   - 在 Wayland 下可能不工作

2. **应用重启**
   - FortiClient 重启后需要重新应用设置
   - 建议在启动脚本中自动配置

3. **性能影响**
   - 持续监控窗口状态会占用少量 CPU
   - 建议只在需要时启用监控

4. **替代方案**
   - 如果不需要 GUI，建议直接使用 `openfortivpn` 命令行工具
   - 命令行工具更可靠、更高效

## 总结

✅ **已成功配置 FortiClient GUI 窗口保持打开**

- 使用 `keep-forticlient-open.sh` 一次性配置窗口
- 使用 `monitor-forticlient-window.sh` 持续监控（可选）
- 窗口现在会保持可见状态，不会自动最小化

如果仍然遇到窗口自动关闭的问题，建议使用命令行工具 `openfortivpn` 代替 GUI。
