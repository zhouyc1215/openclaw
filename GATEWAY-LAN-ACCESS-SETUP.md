# Gateway 局域网访问配置完成

## ✅ 配置状态

Gateway 已成功配置为局域网访问模式！

### 当前配置

```json
{
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "port": 18789
  }
}
```

### 监听地址

- **绑定地址**: `0.0.0.0:18789`
- **局域网访问**: `http://10.71.1.116:18789/`
- **本地访问**: `http://127.0.0.1:18789/`

## 🌐 访问方式

### 1. 从局域网内其他设备访问

```bash
# WebSocket 连接
ws://10.71.1.116:18789

# HTTP 访问 (Control UI)
http://10.71.1.116:18789/

# Canvas 界面
http://10.71.1.116:18789/__clawdbot__/canvas/
```

### 2. 从本机访问

```bash
# WebSocket 连接
ws://127.0.0.1:18789

# HTTP 访问
http://127.0.0.1:18789/
```

## 🔧 配置方法

### 方法 1: 使用 CLI 命令 (推荐)

```bash
# 设置绑定模式为 LAN
clawdbot config set gateway.bind lan

# 重启 Gateway
pkill -9 -f "clawdbot-gateway"
clawdbot gateway run
```

### 方法 2: 直接编辑配置文件

编辑 `~/.openclaw/openclaw.json`:

```json
{
  "gateway": {
    "bind": "lan",
    "port": 18789
  }
}
```

然后重启 Gateway。

### 方法 3: 命令行参数 (临时)

```bash
clawdbot gateway run --bind lan --port 18789
```

## 📊 绑定模式说明

OpenClaw Gateway 支持三种绑定模式:

| 模式       | 绑定地址     | 说明           | 安全性    |
| ---------- | ------------ | -------------- | --------- |
| `loopback` | `127.0.0.1`  | 仅本机访问     | 🔒 最安全 |
| `lan`      | `0.0.0.0`    | 局域网访问     | ⚠️ 中等   |
| `tailnet`  | Tailscale IP | Tailscale 网络 | 🔐 安全   |

## 🔒 安全建议

### 1. 启用认证

局域网访问时建议启用认证:

```bash
# 设置密码认证
clawdbot config set gateway.auth.mode password
clawdbot config set gateway.auth.password "your-secure-password"
```

或使用 Token 认证:

```bash
clawdbot config set gateway.auth.mode token
clawdbot config set gateway.auth.token "your-secure-token"
```

### 2. 防火墙配置

如果需要限制访问，可以配置防火墙:

```bash
# 仅允许特定 IP 访问
sudo ufw allow from 10.71.1.0/24 to any port 18789

# 或使用 iptables
sudo iptables -A INPUT -p tcp -s 10.71.1.0/24 --dport 18789 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 18789 -j DROP
```

### 3. 使用 Tailscale (推荐)

对于远程访问，推荐使用 Tailscale:

```bash
# 配置 Tailscale Serve (仅 Tailnet 内访问)
clawdbot config set gateway.tailscale.mode serve

# 或 Funnel (公网访问，需要密码)
clawdbot config set gateway.tailscale.mode funnel
clawdbot config set gateway.auth.mode password
```

## 🧪 测试访问

### 测试 HTTP 访问

```bash
# 从本机测试
curl http://127.0.0.1:18789/

# 从局域网其他设备测试
curl http://10.71.1.116:18789/
```

### 测试 WebSocket 连接

```bash
# 使用 wscat (需要安装: npm install -g wscat)
wscat -c ws://10.71.1.116:18789
```

### 使用浏览器

直接在浏览器中打开:

- Control UI: `http://10.71.1.116:18789/`
- Canvas: `http://10.71.1.116:18789/__clawdbot__/canvas/`

## 📱 客户端配置

### macOS App

在 macOS 应用中配置远程 Gateway:

1. 打开 OpenClaw 菜单栏应用
2. 设置 -> Gateway
3. 输入: `ws://10.71.1.116:18789`

### CLI 配置

```bash
# 设置远程 Gateway
export OPENCLAW_GATEWAY_URL=ws://10.71.1.116:18789

# 或在配置文件中设置
clawdbot config set gateway.remote.url ws://10.71.1.116:18789
```

### iOS/Android 节点

在移动应用中:

1. 打开设置
2. Gateway 地址: `10.71.1.116`
3. 端口: `18789`

## 🔍 故障排查

### 问题 1: 无法从局域网访问

**检查绑定地址**:

```bash
ss -tlnp | grep 18789
```

应该看到 `0.0.0.0:18789` 而不是 `127.0.0.1:18789`

**解决方案**:

```bash
# 确认配置
clawdbot config get gateway.bind

# 应该返回 "lan"，如果不是:
clawdbot config set gateway.bind lan

# 重启 Gateway
pkill -9 -f "clawdbot-gateway"
clawdbot gateway run
```

### 问题 2: 防火墙阻止

**检查防火墙**:

```bash
# Ubuntu/Debian
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --list-all
```

**开放端口**:

```bash
# Ubuntu/Debian
sudo ufw allow 18789/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=18789/tcp --permanent
sudo firewall-cmd --reload
```

### 问题 3: 认证失败

如果启用了认证，确保客户端提供正确的凭证:

```bash
# 检查认证配置
clawdbot config get gateway.auth

# 重置认证
clawdbot config set gateway.auth.mode none
```

## 📝 日志查看

查看 Gateway 日志:

```bash
# 实时日志
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log

# 查看启动日志
grep "listening on" /tmp/clawdbot/clawdbot-*.log
```

## 🚀 性能优化

### 1. 调整并发限制

```bash
clawdbot config set agents.defaults.maxConcurrent 8
clawdbot config set agents.defaults.subagents.maxConcurrent 16
```

### 2. 启用缓存

```bash
clawdbot config set agents.defaults.compaction.mode safeguard
```

### 3. 配置资源限制

```bash
# 限制内存使用
export NODE_OPTIONS="--max-old-space-size=4096"

# 启动 Gateway
clawdbot gateway run
```

## 📚 相关文档

- [Gateway 配置](https://docs.openclaw.ai/gateway/configuration)
- [远程访问](https://docs.openclaw.ai/gateway/remote)
- [安全指南](https://docs.openclaw.ai/gateway/security)
- [Tailscale 集成](https://docs.openclaw.ai/gateway/tailscale)

## ✅ 配置完成清单

- [x] 配置文件已更新 (`gateway.bind: "lan"`)
- [x] Gateway 已重启
- [x] 绑定地址确认 (`0.0.0.0:18789`)
- [x] 局域网访问测试通过
- [ ] 启用认证 (可选但推荐)
- [ ] 配置防火墙 (可选)
- [ ] 配置 Tailscale (可选)

---

**配置完成时间**: 2026-02-25 16:08
**Gateway 版本**: 2026.2.6-3
**绑定地址**: 0.0.0.0:18789
**局域网 IP**: 10.71.1.116

🎉 现在你可以从局域网内的任何设备访问 Gateway 了！
