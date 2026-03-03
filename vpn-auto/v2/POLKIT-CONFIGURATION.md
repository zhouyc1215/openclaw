# PolicyKit 配置说明

## 问题描述

FortiClient 通过 GUI 启动时，系统会弹出 PolicyKit (polkit) 认证对话框，要求输入用户密码。这会阻止自动化脚本无人值守运行。

## 解决方案

配置 polkit 规则，允许特定用户（tsl）无需密码即可执行 FortiClient 相关操作。

## 配置文件

### 文件位置

```
/etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
```

### 文件内容

```ini
[Allow tsl to run FortiClient without password]
Identity=unix-user:tsl
Action=org.fortinet.forticlient.elevate;org.fortinet.fortitray.quit
ResultAny=yes
ResultInactive=yes
ResultActive=yes
```

## 配置说明

- `Identity=unix-user:tsl`: 仅对 tsl 用户生效
- `Action=org.fortinet.forticlient.elevate`: 允许启动 FortiClient
- `Action=org.fortinet.fortitray.quit`: 允许退出 FortiClient
- `ResultAny/ResultInactive/ResultActive=yes`: 在所有状态下都允许操作

## 安装步骤

### 手动安装

```bash
sudo cp vpn-auto/v2/forticlient-polkit.pkla /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
sudo chmod 644 /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
sudo systemctl restart polkit
```

### 通过安装脚本

```bash
sudo bash vpn-auto/v2/install.sh
```

安装脚本会自动：

1. 复制 polkit 配置文件
2. 设置正确的权限
3. 重启 polkit 服务

## 验证

### 测试 FortiClient 启动

```bash
# 停止 FortiClient
sudo pkill -9 -f forticlient

# 通过 GUI 点击启动（不应弹出密码对话框）
DISPLAY=:1 xdotool mousemove 40 200
DISPLAY=:1 xdotool click 1
```

### 检查 polkit 配置

```bash
# 查看配置文件
cat /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla

# 查看 polkit 服务状态
sudo systemctl status polkit
```

## 相关文件

- `forticlient-polkit.pkla`: polkit 配置文件（项目中）
- `forticlient-sudoers`: sudo 免密码配置（用于 pkill 命令）
- `/usr/share/polkit-1/actions/org.fortinet.forticlient.policy`: FortiClient polkit 策略定义
- `/usr/share/polkit-1/actions/org.fortinet.fortitray.policy`: FortiTray polkit 策略定义

## 安全说明

此配置仅允许 tsl 用户无需密码启动和退出 FortiClient，不影响其他用户或其他系统操作的权限控制。

## 故障排除

### 问题：配置后仍然弹出密码对话框

1. 检查配置文件是否正确安装：

   ```bash
   ls -la /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
   ```

2. 检查文件权限：

   ```bash
   # 应该是 644
   sudo chmod 644 /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
   ```

3. 重启 polkit 服务：

   ```bash
   sudo systemctl restart polkit
   ```

4. 检查用户名是否正确：
   ```bash
   whoami  # 应该输出 tsl
   ```

### 问题：polkit 服务无法启动

1. 检查配置文件语法：

   ```bash
   sudo journalctl -u polkit -n 50
   ```

2. 验证配置文件格式（INI 格式，注意空格和换行）

## 参考资料

- PolicyKit 官方文档: https://www.freedesktop.org/software/polkit/docs/latest/
- FortiClient Linux 文档: https://docs.fortinet.com/product/forticlient/
