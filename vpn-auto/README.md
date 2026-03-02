# VPN 自动重连系统

## 概述

这是一个"伪无人值守"VPN 自动重连系统，用于在 SAML 强制认证下实现接近无人值守的 VPN 连接管理。

**重要说明**：

- 本系统不绕过 MFA 或其他安全措施
- 仅自动化重复性操作（检测断线、拉起客户端、填写凭据）
- 如果你的公司安全策略禁止此类自动化，请勿使用

## 架构

```
systemd (守护进程)
    ↓
vpn-watchdog.sh (检测 VPN 连接状态)
    ↓
vpn-reconnect.sh (拉起 FortiClient)
    ↓
auto-saml-login.js (Playwright 自动完成 SAML 登录)
```

## 功能特性

1. **自动检测**：每 60 秒检查一次 VPN 连接状态
2. **自动重连**：检测到断线时自动触发重连
3. **SAML 自动化**：使用 Playwright 自动完成 Microsoft SAML 认证
4. **重试机制**：失败时自动重试（最多 3 次）
5. **日志记录**：完整的操作日志，便于排查问题
6. **systemd 集成**：开机自启动，崩溃自动重启

## 安装步骤

### 1. 安装依赖

```bash
# 安装 Node.js（如果未安装）
sudo apt update
sudo apt install nodejs npm

# 验证安装
node --version
npm --version
```

### 2. 运行安装脚本

```bash
cd /home/tsl/clawd/vpn-auto
chmod +x install.sh
./install.sh
```

安装脚本会自动：

- 安装 Playwright 和 Chromium
- 设置脚本权限
- 安装 systemd 服务
- 询问是否立即启动服务

### 3. 配置凭据

编辑 `auto-saml-login.js`，确认以下配置正确：

```javascript
const CONFIG = {
  vpnServer: "vpn-krgc.dasanns.com",
  username: "yuchao.zhou@dasanns.com",
  password: "Dasanzyc1215",
  timeout: 60000,
  headless: false, // 调试时设为 false，生产环境设为 true
};
```

### 4. 测试系统

```bash
# 运行测试脚本
chmod +x test-vpn-auto.sh
./test-vpn-auto.sh

# 手动测试重连
./vpn-reconnect.sh
```

## 使用方法

### 启动服务

```bash
sudo systemctl start vpn-watchdog
```

### 停止服务

```bash
sudo systemctl stop vpn-watchdog
```

### 查看状态

```bash
sudo systemctl status vpn-watchdog
```

### 查看日志

```bash
# 实时日志
journalctl -u vpn-watchdog -f

# 最近 100 行
journalctl -u vpn-watchdog -n 100

# 查看文件日志
tail -f /home/tsl/clawd/vpn-auto/watchdog.log
tail -f /home/tsl/clawd/vpn-auto/reconnect.log
```

### 开机自启动

```bash
sudo systemctl enable vpn-watchdog
```

### 禁用开机自启动

```bash
sudo systemctl disable vpn-watchdog
```

## 配置调整

### 修改检查间隔

编辑 `vpn-watchdog.sh`：

```bash
CHECK_INTERVAL=60  # 改为你想要的秒数
```

### 修改重试次数

编辑 `vpn-reconnect.sh`：

```bash
MAX_RETRIES=3      # 改为你想要的次数
RETRY_DELAY=10     # 重试间隔（秒）
```

### 修改 Playwright 超时

编辑 `auto-saml-login.js`：

```javascript
timeout: 60000,    // 改为你想要的毫秒数
headless: true,    // 生产环境建议设为 true（无头模式）
```

## 故障排查

### 问题 1：服务无法启动

```bash
# 查看详细错误
sudo systemctl status vpn-watchdog
journalctl -u vpn-watchdog -n 50
```

常见原因：

- 脚本权限不正确：`chmod +x *.sh *.js`
- Node.js 未安装：`sudo apt install nodejs npm`
- Playwright 未安装：`cd /home/tsl/clawd/vpn-auto && npm install playwright`

### 问题 2：Playwright 无法启动浏览器

```bash
# 重新安装 Chromium
cd /home/tsl/clawd/vpn-auto
npx playwright install chromium

# 检查依赖
npx playwright install-deps chromium
```

### 问题 3：SAML 登录失败

1. 手动测试 Playwright 脚本：

   ```bash
   cd /home/tsl/clawd/vpn-auto
   node auto-saml-login.js
   ```

2. 设置 `headless: false` 观察浏览器行为

3. 检查凭据是否正确

4. 检查 SAML 页面元素是否变化（可能需要更新选择器）

### 问题 4：VPN 连接检测不准确

编辑 `vpn-watchdog.sh` 中的 `check_vpn_connected()` 函数，添加更多检测方法：

```bash
check_vpn_connected() {
    # 方法1：检查网络接口
    if ip addr show | grep -q "ppp\|tun\|wg"; then
        return 0
    fi

    # 方法2：检查特定路由
    if ip route | grep -q "10.0.0.0/8"; then
        return 0
    fi

    # 方法3：ping 内网地址
    if ping -c 1 -W 2 10.0.0.1 &> /dev/null; then
        return 0
    fi

    return 1
}
```

## 安全建议

1. **保护凭据**：
   - 不要将凭据提交到 Git
   - 考虑使用环境变量或加密存储
   - 定期更换密码

2. **限制访问**：

   ```bash
   chmod 600 auto-saml-login.js
   chmod 700 /home/tsl/clawd/vpn-auto
   ```

3. **监控日志**：
   - 定期检查日志，发现异常行为
   - 设置日志轮转，避免占用过多空间

4. **遵守公司政策**：
   - 确认此类自动化符合公司安全策略
   - 如有疑问，咨询 IT 部门

## 高级配置

### 集成到 OpenClaw 定时任务

在定时任务执行前检查 VPN：

```bash
# 在 cron 任务脚本开头添加
if ! ip addr show | grep -q "ppp\|tun\|wg"; then
    echo "VPN 未连接，触发重连..."
    /home/tsl/clawd/vpn-auto/vpn-reconnect.sh
    sleep 10
fi
```

### 发送通知

在 `vpn-reconnect.sh` 中添加飞书通知：

```bash
# 连接成功后发送通知
if trigger_vpn_connect; then
    log "✅ VPN 连接成功"
    pnpm openclaw message send \
        --channel feishu \
        --target ou_b3afb7d2133e4d689be523fc48f3d2b3 \
        --message "VPN 自动重连成功 - $(date '+%H:%M:%S')"
fi
```

## 文件说明

- `vpn-watchdog.sh` - 主守护进程，定期检查 VPN 状态
- `vpn-reconnect.sh` - 重连脚本，拉起 FortiClient 并触发登录
- `auto-saml-login.js` - Playwright 脚本，自动完成 SAML 认证
- `vpn-watchdog.service` - systemd 服务配置
- `install.sh` - 安装脚本
- `test-vpn-auto.sh` - 测试脚本
- `watchdog.log` - Watchdog 日志
- `reconnect.log` - 重连日志

## 卸载

```bash
# 停止并禁用服务
sudo systemctl stop vpn-watchdog
sudo systemctl disable vpn-watchdog

# 删除服务文件
sudo rm /etc/systemd/system/vpn-watchdog.service
sudo systemctl daemon-reload

# 删除脚本目录（可选）
rm -rf /home/tsl/clawd/vpn-auto
```

## 许可证

本项目仅供学习和个人使用。使用前请确保符合你所在组织的安全策略。

## 支持

如有问题，请查看：

1. 日志文件：`watchdog.log` 和 `reconnect.log`
2. systemd 日志：`journalctl -u vpn-watchdog -f`
3. 测试脚本：`./test-vpn-auto.sh`
