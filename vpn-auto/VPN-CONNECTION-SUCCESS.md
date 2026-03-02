# VPN 连接成功总结

## 当前状态

✅ **VPN 已成功连接！**

```bash
$ forticlient vpn status
Status: Connected
  VPN name: vpn-krgc.dasanns.com
  Username: yuchao.zhou@dasanns.com
  IP: 10.60.4.20
  Sent bytes: 4194149
  Recv bytes: 232066
  Duration: 00:01:25
```

## 发现的问题

### 1. GUI 自动化的挑战

- FortiClient GUI 在连接成功后会自动关闭或最小化
- 这导致无法通过 GUI 自动化来点击按钮
- 实际上 VPN 已经通过后台进程 `openfortivpn` 成功连接

### 2. 实际的连接方式

VPN 连接不是通过 GUI 点击实现的，而是通过后台的 `openfortivpn` 进程：

```bash
$ ps aux | grep openfortivpn
root  1001346  openfortivpn vpn-krgc.dasanns.com 443 -u yuchao.zhou@dasanns.com
root  1001715  openfortivpn -c /etc/openfortivpn/config
root  1001849  openfortivpn vpn-krgc.dasanns.com 443 -u yuchao.zhou@dasanns.com
```

## 解决方案

### 方案 1: 使用 openfortivpn 命令行（推荐）✅

直接使用 `openfortivpn` 命令行工具连接，无需 GUI：

```bash
# 创建配置文件
sudo tee /etc/openfortivpn/config > /dev/null << 'EOF'
host = vpn-krgc.dasanns.com
port = 443
username = yuchao.zhou@dasanns.com
password = Dasanzyc1215
trusted-cert = <cert_hash>
EOF

# 连接
sudo openfortivpn -c /etc/openfortivpn/config
```

### 方案 2: 使用 FortiClient CLI

```bash
# 如果有 VPN 配置文件
forticlient vpn connect <vpn_name> -u username -p
```

### 方案 3: 保持 GUI 窗口打开（不推荐）

FortiClient 是 Electron 应用，窗口行为可能是硬编码的。可以尝试：

1. 修改启动参数
2. 使用窗口管理器规则防止窗口关闭
3. 监控窗口状态并自动重新打开

但这些方法都不如直接使用命令行可靠。

## 监控系统集成

### 更新 vpn-monitor.sh

由于 VPN 实际上是通过 `openfortivpn` 连接的，监控脚本应该：

1. 检测 VPN 断开
2. 直接调用 `openfortivpn` 命令重连
3. 无需 GUI 自动化

```bash
# 检测 VPN 状态
if ! forticlient vpn status | grep -q "Connected"; then
    # 直接使用 openfortivpn 重连
    sudo openfortivpn -c /etc/openfortivpn/config &

    # 或者使用 forticlient CLI（如果有配置）
    # forticlient vpn connect <vpn_name> -u username -p
fi
```

## 配置文件位置

### FortiClient 配置

- 用户配置: `~/.config/FortiClient/`
- Preferences: `~/.config/FortiClient/Preferences` (JSON)
- 日志: `~/.config/FortiClient/logs/`

### openfortivpn 配置

- 系统配置: `/etc/openfortivpn/config`
- 用户配置: `~/.config/openfortivpn/config`

## 下一步行动

### 1. 简化监控脚本 ✅

移除 GUI 自动化部分，直接使用命令行连接：

```bash
# vpn-monitor.sh 简化版
if ! is_vpn_connected; then
    log "VPN 断开，正在重连..."

    # 方法 1: 使用 openfortivpn
    sudo openfortivpn -c /etc/openfortivpn/config &

    # 方法 2: 使用 forticlient CLI（如果有配置）
    # forticlient vpn connect <vpn_name> -u username -p

    send_feishu_notification "VPN 正在重连..."
fi
```

### 2. 配置 openfortivpn

创建配置文件以便自动重连：

```bash
sudo mkdir -p /etc/openfortivpn
sudo tee /etc/openfortivpn/config > /dev/null << 'EOF'
host = vpn-krgc.dasanns.com
port = 443
username = yuchao.zhou@dasanns.com
password = Dasanzyc1215
# 添加其他必要的配置
EOF

sudo chmod 600 /etc/openfortivpn/config
```

### 3. 测试自动重连

```bash
# 断开 VPN
forticlient vpn disconnect

# 等待监控服务检测并重连
# 查看日志
journalctl -u vpn-monitor -f
```

## 总结

虽然我们花了很多时间研究 GUI 自动化，但实际上：

1. ✅ VPN 已经成功连接
2. ✅ 连接是通过 `openfortivpn` 后台进程实现的
3. ✅ 不需要 GUI 自动化
4. ✅ 可以直接使用命令行工具进行监控和重连

下一步应该：

- 简化监控脚本，移除 GUI 部分
- 配置 `openfortivpn` 以便自动重连
- 测试完整的监控和重连流程

GUI 自动化的工作虽然没有直接用上，但为我们提供了很多有价值的工具和经验，可以用于其他需要 GUI 自动化的场景。
