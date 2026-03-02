# VPN 自动重连系统 - 快速开始

## 5 分钟快速部署

### 步骤 1：检查依赖

```bash
# 检查 Node.js
node --version  # 应该显示版本号

# 如果未安装
sudo apt update && sudo apt install -y nodejs npm
```

### 步骤 2：运行安装脚本

```bash
cd /home/tsl/clawd/vpn-auto
./install.sh
```

安装过程会：

1. ✅ 检查依赖
2. ✅ 安装 Playwright
3. ✅ 设置脚本权限
4. ✅ 安装 systemd 服务
5. ❓ 询问是否立即启动（建议先测试）

### 步骤 3：测试系统

```bash
# 运行测试脚本
./test-vpn-auto.sh

# 手动测试重连（重要！）
./vpn-reconnect.sh
```

观察浏览器窗口，确认能够自动完成登录。

### 步骤 4：启动服务

```bash
# 启动服务
sudo systemctl start vpn-watchdog

# 查看状态
sudo systemctl status vpn-watchdog

# 查看实时日志
journalctl -u vpn-watchdog -f
```

### 步骤 5：设置开机自启动

```bash
sudo systemctl enable vpn-watchdog
```

## 常用命令

```bash
# 启动
sudo systemctl start vpn-watchdog

# 停止
sudo systemctl stop vpn-watchdog

# 重启
sudo systemctl restart vpn-watchdog

# 查看状态
sudo systemctl status vpn-watchdog

# 查看日志
journalctl -u vpn-watchdog -f

# 查看文件日志
tail -f /home/tsl/clawd/vpn-auto/watchdog.log
tail -f /home/tsl/clawd/vpn-auto/reconnect.log
```

## 配置调整

### 修改检查间隔（默认 60 秒）

编辑 `vpn-watchdog.sh`：

```bash
CHECK_INTERVAL=60  # 改为你想要的秒数
```

### 切换到无头模式（生产环境推荐）

编辑 `auto-saml-login.js`：

```javascript
headless: true,  // 改为 true
```

## 故障排查

### 问题：Playwright 无法启动

```bash
cd /home/tsl/clawd/vpn-auto
npx playwright install chromium
npx playwright install-deps chromium
```

### 问题：SAML 登录失败

1. 设置 `headless: false` 观察浏览器
2. 检查凭据是否正确
3. 手动测试：`node auto-saml-login.js`

### 问题：服务无法启动

```bash
# 查看详细错误
sudo systemctl status vpn-watchdog
journalctl -u vpn-watchdog -n 50
```

## 集成到 OpenClaw 定时任务

在需要外网的定时任务前添加 VPN 检查：

```bash
#!/bin/bash
# 检查 VPN 连接
if ! ip addr show | grep -q "ppp\|tun\|wg"; then
    echo "VPN 未连接，触发重连..."
    /home/tsl/clawd/vpn-auto/vpn-reconnect.sh
    sleep 10
fi

# 执行你的任务
# ...
```

## 下一步

- 阅读完整文档：`README.md`
- 查看日志了解运行情况
- 根据需要调整配置
- 考虑添加飞书通知

## 安全提醒

⚠️ 本系统会在脚本中存储明文密码，请：

1. 限制文件权限：`chmod 600 auto-saml-login.js`
2. 不要提交到 Git
3. 定期更换密码
4. 确保符合公司安全策略
