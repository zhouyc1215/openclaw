# VPN 自动重连系统 v2 安装完成

## 安装状态

✅ **安装成功！**

所有核心组件已安装并测试通过。

## 已安装组件

### 系统依赖

- ✅ Python 3.8.10
- ✅ pip3 25.0.1
- ✅ xdotool (GUI 自动化)
- ✅ scrot (屏幕截图)
- ✅ python3-pyatspi (AT-SPI 驱动)
- ✅ python3-opencv (OpenCV 驱动)
- ⏳ xfce4 (可选，后台安装中)
- ⏳ supervisor (可选，后台安装中)

### Python 库

- ✅ pyyaml 6.0.3
- ✅ numpy 1.24.4
- ✅ opencv-python
- ✅ pyautogui 0.9.54
- ✅ pillow 10.4.0

### 核心模块

- ✅ 配置加载器 (config_loader.py)
- ✅ 状态机核心 (watchdog.py)
- ✅ 网络检测器 (network_check.py)
- ✅ 重连编排器 (orchestrator.py)

### 驱动模块

- ✅ AT-SPI 驱动 (主方案)
- ✅ PyAutoGUI 驱动 (备用)
- ✅ OpenCV 驱动 (兜底)

## 项目结构

```
vpn-auto/v2/
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── config_loader.py    # 配置加载器
│   ├── watchdog.py         # 状态机核心
│   ├── network_check.py    # 网络检测
│   └── orchestrator.py     # 重连策略
├── drivers/                # 驱动模块
│   ├── __init__.py
│   ├── atspi_driver.py     # AT-SPI 驱动
│   ├── pyauto_driver.py    # PyAutoGUI 驱动
│   └── vision_driver.py    # OpenCV 驱动
├── services/               # 服务脚本
│   ├── xvfb.sh            # 虚拟桌面管理
│   └── forti.sh           # FortiClient 管理
├── config/                 # 配置文件
│   └── config.yaml        # 主配置文件
├── logs/                   # 日志目录
├── run.sh                  # 统一入口
├── vpn-auto.service       # systemd 服务文件
├── install.sh             # 安装脚本
├── quick-test.sh          # 快速测试脚本
├── test-install.sh        # 安装状态检查
└── README.md              # 使用文档
```

## 快速开始

### 1. 编辑配置文件

```bash
nano vpn-auto/v2/config/config.yaml
```

关键配置项：

- `vpn.username`: VPN 用户名
- `vpn.password`: VPN 密码
- `system.sudo_password`: sudo 密码
- `system.display`: X11 显示服务器（默认 :1）
- `network.check_interval`: 检测间隔（秒）

### 2. 测试运行

```bash
# 快速测试
bash vpn-auto/v2/quick-test.sh

# 完整运行
bash vpn-auto/v2/run.sh
```

### 3. 安装 systemd 服务（可选）

```bash
# 复制服务文件
sudo cp vpn-auto/v2/vpn-auto.service /etc/systemd/system/

# 重载 systemd
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable --now vpn-auto.service

# 查看状态
sudo systemctl status vpn-auto.service

# 查看日志
sudo journalctl -u vpn-auto.service -f
```

## 工作原理

### 监控循环

```
1. 每 60 秒检测一次 VPN 状态
   ↓
2. 检查 ppp0 接口是否存在
   ↓
3. Ping 检测主机（8.8.8.8, 1.1.1.1）
   ↓
4. 如果连续失败 3 次，触发重连
   ↓
5. 重连流程：
   - 停止 FortiClient
   - 启动 FortiClient
   - 等待窗口出现
   - 调整窗口大小
   - 点击连接按钮（尝试 3 种驱动）
   - 等待 VPN 连接
   - 检查连接状态
   ↓
6. 返回步骤 1
```

### 驱动优先级

1. **AT-SPI 驱动**（主方案）
   - 使用 Linux 无障碍技术
   - 直接访问 UI 元素
   - 无需截图，速度最快

2. **PyAutoGUI 驱动**（备用）
   - 使用图像识别
   - 需要预先截取按钮图像
   - 适用于 AT-SPI 不可用的情况

3. **OpenCV 驱动**（兜底）
   - 使用颜色检测
   - 最鲁棒，但速度较慢
   - 适用于前两种驱动都失败的情况

## 配置说明

### VPN 配置

```yaml
vpn:
  process_name: forticlient
  launch_method: gui_click # gui_click 或 command
  gui_sidebar_x: 40 # 左边栏 X 坐标
  gui_sidebar_y: 200 # 左边栏 Y 坐标（第三个按钮）
  window_name: FortiClient
  window_width: 1200
  window_height: 800
  username: yuchao.zhou@dasanns.com
  password: Dasanzyc1215
```

### 网络检测配置

```yaml
network:
  check_interval: 60 # 检测间隔（秒）
  check_hosts: # 检测主机列表
    - 8.8.8.8
    - 1.1.1.1
  ping_count: 2 # Ping 次数
  ping_timeout: 5 # Ping 超时（秒）
  vpn_interface: ppp0 # VPN 网络接口
```

### 重连策略配置

```yaml
reconnect:
  max_failures: 3 # 最大连续失败次数
  retry_delay: 10 # 重试延迟（秒）
  restart_delay: 2 # 重启延迟（秒）
  window_wait_timeout: 30 # 窗口等待超时（秒）
  gui_load_delay: 15 # GUI 加载延迟（秒）
  vpn_connect_timeout: 30 # VPN 连接超时（秒）
```

## 故障排查

### 查看日志

```bash
# systemd 日志
sudo journalctl -u vpn-auto.service -f

# 应用日志
tail -f vpn-auto/v2/logs/vpn-*.log
```

### 常见问题

1. **窗口未出现**
   - 检查 `gui_sidebar_x` 和 `gui_sidebar_y` 坐标
   - 手动启动 FortiClient 验证

2. **未找到按钮**
   - 增加 `gui_load_delay`
   - 调整 `button.hsv_lower` 和 `button.hsv_upper`
   - 检查窗口大小

3. **VPN 未连接**
   - 检查网络连接
   - 手动完成 SAML 认证
   - 查看 FortiClient 日志

4. **驱动失败**
   - 检查依赖是否安装
   - 尝试禁用某些驱动
   - 查看详细日志

### 手动测试

```bash
# 测试网络检测
DISPLAY=:1 python3 -c "
from core.config_loader import load_config
from core.network_check import NetworkChecker
config = load_config('vpn-auto/v2/config/config.yaml')
checker = NetworkChecker(config)
print('VPN 连接:', checker.is_vpn_connected())
"

# 测试重连流程
DISPLAY=:1 python3 -c "
from core.config_loader import load_config
from core.orchestrator import ReconnectOrchestrator
config = load_config('vpn-auto/v2/config/config.yaml')
orchestrator = ReconnectOrchestrator(config)
orchestrator.reconnect()
"
```

## 安全建议

1. **密码存储**
   - 使用环境变量存储密码
   - 配置文件权限设为 600
   - 考虑使用加密存储（如 keyring）

2. **sudo 免密码**（可选）

   ```bash
   # /etc/sudoers.d/forticlient
   tsl ALL=(ALL) NOPASSWD: /usr/bin/pkill -9 -f forticlient
   ```

3. **文件权限**
   ```bash
   chmod 600 vpn-auto/v2/config/config.yaml
   chmod 700 vpn-auto/v2/run.sh
   ```

## 下一步

1. ✅ 核心功能已完成并测试通过
2. ⏳ 等待 apt 安装完成（可选组件）
3. 📝 编辑配置文件
4. 🧪 运行测试
5. 🚀 部署 systemd 服务

## 技术支持

- 详细文档：`vpn-auto/v2/README.md`
- 技术文档：`vpn-auto/TECHNICAL-DOCUMENTATION.md`
- 配置文件：`vpn-auto/v2/config/config.yaml`

## 版本信息

- 版本：v2.0.0
- 创建日期：2026-03-03
- Python 版本：3.8.10
- 系统：Linux (Ubuntu 20.04)

---

✅ **安装完成！系统已就绪，可以开始使用。**
