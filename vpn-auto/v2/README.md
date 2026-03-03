# VPN 自动重连系统 v2

工程化、模块化的 VPN 自动重连解决方案。

## 特性

- ✅ 状态机核心：智能监控和重连策略
- ✅ 多重网络检测：接口检测 + 连通性检测
- ✅ 三种驱动方案：AT-SPI（主）+ PyAutoGUI（备用）+ OpenCV（兜底）
- ✅ systemd 服务集成：开机自启动
- ✅ 虚拟桌面支持：可选 Xvfb 无头运行
- ✅ 配置中心：YAML 配置文件
- ✅ 详细日志：便于故障排查
- ✅ 飞书通知：VPN 需要手动认证时自动截图并发送到飞书

## 系统架构

```
vpn-auto/v2/
├── core/                   # 核心模块
│   ├── watchdog.py        # 状态机核心（调度一切）
│   ├── network_check.py   # 多重网络检测
│   ├── orchestrator.py    # 重连策略（大脑）
│   └── config_loader.py   # 配置加载器
├── drivers/               # 驱动模块
│   ├── atspi_driver.py    # ⭐ AT-SPI 驱动（主方案，免截图）
│   ├── pyauto_driver.py   # PyAutoGUI 驱动（备用）
│   └── vision_driver.py   # OpenCV 驱动（兜底）
├── services/              # 服务脚本
│   ├── xvfb.sh           # 虚拟桌面管理
│   └── forti.sh          # FortiClient 管理
├── config/                # 配置文件
│   └── config.yaml       # 主配置文件
├── logs/                  # 日志目录
├── run.sh                 # 统一入口
├── vpn-auto.service      # systemd 服务文件
└── README.md             # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
sudo bash vpn-auto/v2/install.sh
```

### 2. 配置

编辑配置文件：

```bash
nano vpn-auto/v2/config/config.yaml
```

关键配置项：

- `vpn.username`: VPN 用户名
- `vpn.password`: VPN 密码
- `system.sudo_password`: sudo 密码
- `system.display`: X11 显示服务器（默认 :1）
- `network.check_interval`: 检测间隔（秒）

### 3. 测试运行

```bash
bash vpn-auto/v2/run.sh
```

### 4. 安装 systemd 服务

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

### 状态机流程

```
监控循环
  ↓
检测 VPN 状态
  ↓
[正常] → 重置失败计数 → 继续监控
  ↓
[断开] → 增加失败计数
  ↓
[失败次数 >= 阈值] → 触发重连
  ↓
重连流程：
  1. 停止 FortiClient
  2. 启动 FortiClient
  3. 等待窗口出现
  4. 调整窗口大小
  5. 等待 GUI 加载
  6. 点击连接按钮（尝试所有驱动）
  7. 等待 VPN 连接
  8. 检查连接状态
  ↓
[成功] → 重置失败计数 → 继续监控
[失败] → 保持失败计数 → 下次继续尝试
```

### 驱动优先级

1. **AT-SPI 驱动**（主方案）
   - 使用 Linux 无障碍技术
   - 直接访问 UI 元素
   - 无需截图，速度快
   - 需要 `python3-pyatspi`

2. **PyAutoGUI 驱动**（备用）
   - 使用图像识别
   - 需要预先截取按钮图像
   - 需要 `pyautogui`

3. **OpenCV 驱动**（兜底）
   - 使用颜色检测
   - 最鲁棒，但速度较慢
   - 需要 `opencv-python`

## 配置说明

### VPN 配置

```yaml
vpn:
  process_name: forticlient
  launch_method: gui_click # gui_click 或 command
  gui_sidebar_x: 40 # 左边栏 X 坐标
  gui_sidebar_y: 200 # 左边栏 Y 坐标
  window_name: FortiClient
  window_width: 1200
  window_height: 800
  username: your_username
  password: your_password
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
  vpn_connect_timeout: 60 # VPN 连接超时（秒），每 10 秒检查一次
```

**VPN 连接检测机制**：

- 点击 SAML Login 按钮后，系统会每 10 秒检查一次 VPN 状态
- 最多检查 6 次（总共 60 秒）
- 一旦检测到 VPN 连接成功，立即返回（不需要等待完整的 60 秒）
- 如果 60 秒内 VPN 仍未连接，才判定为需要手动 SAML 认证

### 按钮识别配置

```yaml
button:
  # HSV 颜色范围（用于 OpenCV 驱动）
  hsv_lower: [100, 100, 100]
  hsv_upper: [130, 255, 255]

  # 按钮尺寸范围
  min_area: 2000
  max_area: 50000
  min_width: 80
  max_width: 300
  min_height: 25
  max_height: 80
```

### 驱动配置

```yaml
drivers:
  priority: # 驱动优先级
    - atspi
    - pyauto
    - vision

  atspi:
    enabled: true
    timeout: 10

  pyauto:
    enabled: true
    confidence: 0.8
    button_image: /path/to/button.png

  vision:
    enabled: true
    debug_output: false
```

### 飞书通知配置

```yaml
feishu:
  enabled: true # 是否启用飞书通知
  user_id: "ou_xxx" # 飞书用户 ID
  openclaw_bin: "/usr/bin/pnpm openclaw" # openclaw 命令路径
```

**飞书通知触发条件**：

- 当系统成功点击 SAML Login 按钮后
- 等待 30 秒后 VPN 仍未连接
- 此时说明需要手动在浏览器中完成 SAML 认证
- 系统会自动截取当前屏幕并发送到飞书，提醒用户完成认证

**注意**：

- 如果点击按钮失败，不会发送通知（因为可能是其他问题）
- 只有在按钮点击成功但 VPN 未连接时才发送通知
- 确保 OpenClaw Gateway 正在运行且飞书通道已配置

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
python3 -c "
from core.config_loader import load_config
from core.network_check import NetworkChecker
config = load_config()
checker = NetworkChecker(config)
print('VPN 连接:', checker.is_vpn_connected())
"

# 测试重连流程
python3 -c "
from core.config_loader import load_config
from core.orchestrator import ReconnectOrchestrator
config = load_config()
orchestrator = ReconnectOrchestrator(config)
orchestrator.reconnect()
"
```

## 安全建议

1. **配置 sudo 免密码**（推荐）：

   ```bash
   # 复制 sudoers 配置
   sudo cp vpn-auto/v2/forticlient-sudoers /etc/sudoers.d/forticlient
   sudo chmod 440 /etc/sudoers.d/forticlient

   # 测试免密码执行
   sudo -n pkill -9 -f forticlient
   ```

   配置后，系统不需要自动输入 sudo 密码，更加安全和可靠。

2. **密码存储**：
   - 使用环境变量存储密码
   - 配置文件权限设为 600
   - 考虑使用加密存储（如 keyring）

3. **文件权限**：
   ```bash
   chmod 600 vpn-auto/v2/config/config.yaml
   chmod 700 vpn-auto/v2/run.sh
   ```

## 扩展性

### 添加新驱动

1. 在 `drivers/` 目录创建新驱动文件
2. 实现 `click_connect()` 方法
3. 在 `orchestrator.py` 中注册驱动
4. 在 `config.yaml` 中配置驱动

### 支持多个 VPN

1. 创建多个配置文件
2. 创建多个 systemd 服务
3. 使用不同的 DISPLAY

### 集成到其他系统

- 可以作为 Python 模块导入
- 可以通过 API 调用
- 可以集成到监控系统

## 性能优化

- AT-SPI 驱动速度最快（无需截图）
- 调整 `check_interval` 平衡响应速度和资源占用
- 使用虚拟桌面减少 GUI 开销

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 参考资料

- [AT-SPI 文档](https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/)
- [xdotool 文档](https://www.semicomplete.com/projects/xdotool/)
- [OpenCV Python 教程](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)
- [systemd 服务管理](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
