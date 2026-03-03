# 重启验证检查清单

## 重启前准备

在重启电脑之前，请确认以下配置已完成：

### 1. systemd 服务配置

```bash
# 检查服务是否已安装
sudo systemctl status vpn-auto.service

# 检查是否已启用开机自启动
systemctl is-enabled vpn-auto.service
```

应该看到：

- ✅ 服务状态: `Active: active (running)`
- ✅ 开机自启动: `enabled`

### 2. 配置文件检查

```bash
# 检查配置文件是否存在
ls -lh ~/openclaw/vpn-auto/v2/config/config.yaml

# 验证配置文件语法
python3 -c "from core.config_loader import load_config; load_config()"
```

### 3. 权限检查

```bash
# 检查脚本权限
ls -lh ~/openclaw/vpn-auto/v2/run.sh
ls -lh ~/openclaw/vpn-auto/v2/verify-after-reboot.sh
```

应该都有执行权限 (`-rwxr-xr-x`)

### 4. 停止当前服务（可选）

```bash
# 如果要测试完整的开机启动流程，可以先停止服务
sudo systemctl stop vpn-auto.service
```

---

## 重启命令

```bash
sudo reboot
```

---

## 重启后验证步骤

### 1. 等待系统完全启动

等待 1-2 分钟，让所有服务完全启动。

### 2. 运行验证脚本

```bash
bash ~/openclaw/vpn-auto/v2/verify-after-reboot.sh
```

### 3. 检查关键指标

验证脚本会检查以下内容：

#### ✅ 必须通过的检查项

1. **systemd 服务状态**: 必须是 `active (running)`
2. **开机自启动**: 必须是 `enabled`
3. **Watchdog 进程**: 必须正在运行
4. **日志文件**: 必须存在且有新内容
5. **配置文件**: 必须能正常加载

#### ⚠️ 可能需要时间的检查项

1. **VPN 连接状态**: 可能需要几分钟才能连接
2. **FortiClient 进程**: 系统会在检测到断开后启动
3. **FortiClient 窗口**: 需要 GUI 环境完全启动

---

## 预期行为

### 正常启动流程

1. **系统启动** (0-30秒)
   - systemd 启动 vpn-auto.service
   - run.sh 脚本开始执行
   - Watchdog 进程启动

2. **初始检测** (30-90秒)
   - Watchdog 开始检测 VPN 状态
   - 检测到 VPN 断开
   - 失败计数器开始累计 (1/3, 2/3, 3/3)

3. **自动重连** (90-180秒)
   - 达到失败阈值 (3次)
   - 触发重连流程
   - 停止 FortiClient
   - 启动 FortiClient
   - 点击 SAML Login 按钮
   - 等待 VPN 连接

4. **连接成功** (180-240秒)
   - VPN 连接建立 (ppp0 接口)
   - 失败计数器重置
   - 进入正常监控模式

### 时间线参考

```
T+0s    系统启动
T+30s   vpn-auto.service 启动
T+60s   第一次检测 (失败 1/3)
T+120s  第二次检测 (失败 2/3)
T+180s  第三次检测 (失败 3/3) → 触发重连
T+210s  FortiClient 重启完成
T+240s  VPN 连接成功
```

---

## 故障排查

### 如果服务未启动

```bash
# 查看服务状态
sudo systemctl status vpn-auto.service

# 查看详细日志
sudo journalctl -u vpn-auto.service -n 50 --no-pager

# 手动启动服务
sudo systemctl start vpn-auto.service
```

### 如果 VPN 未连接

```bash
# 查看应用日志
tail -50 ~/openclaw/vpn-auto/v2/logs/vpn-*.log

# 检查 FortiClient 状态
ps aux | grep forticlient

# 检查网络接口
ip addr show ppp0

# 手动触发重连（停止并重启服务）
sudo systemctl restart vpn-auto.service
```

### 如果配置有问题

```bash
# 编辑配置文件
nano ~/openclaw/vpn-auto/v2/config/config.yaml

# 重新加载配置（重启服务）
sudo systemctl restart vpn-auto.service
```

---

## 监控命令

### 实时查看日志

```bash
# systemd 日志
sudo journalctl -u vpn-auto.service -f

# 应用日志
tail -f ~/openclaw/vpn-auto/v2/logs/vpn-*.log
```

### 检查 VPN 状态

```bash
# 检查 ppp0 接口
ip addr show ppp0

# 检查路由
ip route | grep ppp0

# 测试外网连接
ping -c 3 8.8.8.8
```

### 检查进程

```bash
# 查看 Watchdog 进程
ps aux | grep watchdog.py

# 查看 FortiClient 进程
ps aux | grep forticlient

# 查看资源使用
top -p $(pgrep -f watchdog.py)
```

---

## 成功标志

重启后系统正常工作的标志：

1. ✅ `sudo systemctl status vpn-auto.service` 显示 `active (running)`
2. ✅ `pgrep -f watchdog.py` 返回进程 ID
3. ✅ 日志文件有新内容且无错误
4. ✅ 3-5 分钟后 VPN 自动连接成功
5. ✅ `ip addr show ppp0` 显示 IP 地址
6. ✅ 可以访问外网 (`ping 8.8.8.8`)

---

## 配置调整建议

如果重启后发现问题，可以调整以下配置：

### 增加检测间隔

```yaml
# config/config.yaml
network:
  check_interval: 120 # 从 60 改为 120 秒
```

### 减少失败阈值

```yaml
# config/config.yaml
reconnect:
  max_failures: 2 # 从 3 改为 2，更快触发重连
```

### 增加超时时间

```yaml
# config/config.yaml
reconnect:
  window_wait_timeout: 60 # 从 30 改为 60 秒
  gui_load_delay: 30 # 从 15 改为 30 秒
  vpn_connect_timeout: 60 # 从 30 改为 60 秒
```

---

## 联系支持

如果遇到无法解决的问题，请提供以下信息：

1. 验证脚本输出: `bash verify-after-reboot.sh > verify-output.txt`
2. systemd 日志: `sudo journalctl -u vpn-auto.service -n 100 > systemd.log`
3. 应用日志: `tail -100 ~/openclaw/vpn-auto/v2/logs/vpn-*.log > app.log`
4. 系统信息: `uname -a && cat /etc/os-release`
