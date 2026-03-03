# VPN 自动重连系统 v2 - 架构文档

## 目录

- [1. 系统概述](#1-系统概述)
- [2. 核心架构](#2-核心架构)
- [3. 核心模块详解](#3-核心模块详解)
- [4. 驱动模块详解](#4-驱动模块详解)
- [5. 状态机流程](#5-状态机流程)
- [6. 重连策略详解](#6-重连策略详解)
- [7. 配置系统](#7-配置系统)
- [8. systemd 服务集成](#8-systemd-服务集成)
- [9. 故障排查指南](#9-故障排查指南)

---

## 1. 系统概述

### 1.1 设计目标

VPN 自动重连系统 v2 是一个工程化、模块化的解决方案，旨在：

- **自动化**：无需人工干预，自动检测和恢复 VPN 连接
- **可靠性**：多重检测机制 + 多驱动备份方案
- **可维护性**：清晰的模块划分 + 详细的日志记录
- **可扩展性**：易于添加新驱动和新功能
- **生产就绪**：systemd 服务集成 + 开机自启动

### 1.2 技术栈

- **语言**: Python 3.8+
- **GUI 自动化**: xdotool, AT-SPI, PyAutoGUI, OpenCV
- **进程管理**: systemd
- **配置管理**: YAML
- **日志系统**: Python logging
- **权限管理**: PolicyKit (polkit), sudo
- **通知系统**: 飞书 (Feishu) 集成

### 1.3 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      systemd 服务层                          │
│                   (vpn-auto.service)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      入口层 (run.sh)                         │
│              - 环境检查                                       │
│              - 日志配置                                       │
│              - 启动 watchdog                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   核心层 (core/)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  watchdog.py │  │network_check │  │orchestrator  │      │
│  │  (状态机)    │──│  (检测器)    │  │  (编排器)    │      │
│  └──────────────┘  └──────────────┘  └──────┬───────┘      │
│                                              │               │
└──────────────────────────────────────────────┼──────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   驱动层 (drivers/)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ atspi_driver │  │pyauto_driver │  │vision_driver │      │
│  │  (主方案)    │  │  (备用)      │  │  (兜底)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   系统层                                     │
│  - X11 (DISPLAY :1)                                         │
│  - FortiClient GUI                                          │
│  - 网络接口 (ppp0)                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 核心架构

### 2.1 分层设计

系统采用经典的分层架构：

1. **服务层**: systemd 服务管理，负责进程生命周期
2. **入口层**: run.sh 脚本，负责环境初始化和启动
3. **核心层**: 业务逻辑核心，包含状态机、检测器、编排器
4. **驱动层**: GUI 自动化驱动，提供多种实现方案
5. **系统层**: 底层系统资源（X11、网络、进程）

### 2.2 模块职责

| 模块                 | 职责                                               | 依赖                        |
| -------------------- | -------------------------------------------------- | --------------------------- |
| `watchdog.py`        | 状态机核心，监控循环，触发重连                     | network_check, orchestrator |
| `network_check.py`   | 网络检测，接口检测 + 连通性检测 + FortiClient 状态 | 无                          |
| `orchestrator.py`    | 重连策略编排，协调整个重连流程                     | drivers/\*, feishu_notifier |
| `config_loader.py`   | 配置加载，YAML 解析                                | 无                          |
| `feishu_notifier.py` | 飞书通知，截图上传，消息发送                       | 无                          |
| `atspi_driver.py`    | AT-SPI 驱动，无障碍技术                            | pyatspi                     |
| `pyauto_driver.py`   | PyAutoGUI 驱动，图像识别                           | pyautogui                   |
| `vision_driver.py`   | OpenCV 驱动，颜色检测                              | opencv-python               |

### 2.3 数据流

```
配置文件 (config.yaml)
    ↓
config_loader.py (加载配置)
    ↓
watchdog.py (初始化)
    ├─→ network_checker (创建检测器)
    └─→ orchestrator (创建编排器)
            ├─→ atspi_driver (加载驱动)
            ├─→ pyauto_driver
            └─→ vision_driver
    ↓
监控循环
    ├─→ network_checker.is_vpn_connected() (检测)
    └─→ orchestrator.reconnect() (重连)
            ├─→ stop_forticlient()
            ├─→ start_forticlient()
            ├─→ wait_for_window()
            ├─→ resize_window()
            └─→ click_connect_button()
                    ├─→ atspi_driver.click_connect()
                    ├─→ pyauto_driver.click_connect()
                    └─→ vision_driver.click_connect()
```

---

## 3. 核心模块详解

### 3.1 watchdog.py - 状态机核心

#### 3.1.1 设计思想

watchdog 是整个系统的"大脑"，负责：

- 定时检测 VPN 状态
- 维护失败计数器
- 触发重连流程

#### 3.1.2 状态机设计

```python
状态变量:
- consecutive_failures: 连续失败次数
- max_failures: 最大失败次数阈值

状态转换:
[正常] → consecutive_failures = 0
[断开] → consecutive_failures += 1
[失败次数 >= 阈值] → 触发重连
[重连成功] → consecutive_failures = 0
[重连失败] → 保持 consecutive_failures (下次继续尝试)
```

#### 3.1.3 核心代码逻辑

```python
def run(self):
    """主循环"""
    while True:
        try:
            # 1. 检测 VPN 状态
            if self.network_checker.is_vpn_connected():
                # VPN 正常 → 重置失败计数
                if self.consecutive_failures > 0:
                    logger.info("✅ VPN 已恢复连接")
                self.consecutive_failures = 0
            else:
                # VPN 断开 → 增加失败计数
                self.consecutive_failures += 1
                logger.warning(f"⚠️  VPN 断开 (失败次数: {self.consecutive_failures}/{self.max_failures})")

                # 2. 检查是否达到阈值
                if self.consecutive_failures >= self.max_failures:
                    logger.error(f"❌ VPN 连续失败 {self.consecutive_failures} 次，触发重连")
                    self.trigger_reconnect()

            # 3. 等待下一次检测
            time.sleep(self.check_interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"监控循环异常: {e}", exc_info=True)
            time.sleep(self.check_interval)
```

**关键设计点**:

1. **失败计数器**: 避免偶发性网络波动触发重连
2. **异常处理**: 确保监控循环不会因异常而退出
3. **日志记录**: 详细记录状态变化，便于故障排查

---

### 3.2 network_check.py - 网络检测器

#### 3.2.1 设计思想

采用**多重检测机制**，提高检测准确性：

1. **FortiClient 状态检测**: 使用 `forticlient vpn status` 命令（最准确）
2. **接口检测**: 检查 VPN 网络接口是否存在
3. **连通性检测**: Ping 外部主机验证网络连通性

#### 3.2.2 检测流程

```
is_vpn_connected()
    ↓
check_vpn_interface()
    ├─→ [方法 1] forticlient vpn status (检查 "Status: Connected")
    │       ├─→ [已连接] → True
    │       └─→ [未连接] → 继续
    ├─→ [方法 2] ip addr show fctvpn16ec49c7 (检查指定接口)
    │       ├─→ [存在] → True
    │       └─→ [不存在] → 继续
    └─→ [方法 3] 查找 fctvpn 开头的接口
            ├─→ [找到] → True
            └─→ [未找到] → False
    ↓
[接口存在] → check_network_connectivity()
    ├─→ ping 8.8.8.8
    ├─→ ping 1.1.1.1
    └─→ [任一成功] → True
```

#### 3.2.3 核心代码逻辑

```python
def check_vpn_interface(self):
    """检查 VPN 网络接口是否存在"""
    try:
        # 方法 1: 使用 forticlient vpn status 命令（最准确）
        result = subprocess.run(
            ['forticlient', 'vpn', 'status'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and 'Status: Connected' in result.stdout:
            logger.debug("✅ FortiClient VPN 已连接")
            return True

        # 方法 2: 检查指定的接口名称
        result = subprocess.run(
            ['ip', 'addr', 'show', self.vpn_interface],  # fctvpn16ec49c7
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and 'inet ' in result.stdout:
            logger.debug(f"✅ VPN 接口 {self.vpn_interface} 存在")
            return True

        # 方法 3: 如果指定接口不存在，尝试查找 fctvpn 开头的接口
        if 'fctvpn' in self.vpn_interface:
            result = subprocess.run(
                ['ip', 'addr', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # 查找 fctvpn 开头的接口
            import re
            for line in result.stdout.split('\n'):
                if 'fctvpn' in line:
                    match = re.search(r'(\d+): (fctvpn\w+):', line)
                    if match:
                        iface = match.group(2)
                        # 检查这个接口是否有 IP 地址
                        iface_result = subprocess.run(
                            ['ip', 'addr', 'show', iface],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if 'inet ' in iface_result.stdout:
                            logger.debug(f"✅ VPN 接口 {iface} 存在")
                            return True

        logger.debug("❌ VPN 接口不存在")
        return False

    except Exception as e:
        logger.error(f"检查 VPN 接口失败: {e}")
        return False

def ping_host(self, host):
    """Ping 主机"""
    try:
        result = subprocess.run(
            ['ping', '-c', str(self.ping_count), '-W', str(self.ping_timeout), host],
            capture_output=True,
            text=True,
            timeout=self.ping_timeout + 5
        )

        return result.returncode == 0

    except Exception as e:
        logger.debug(f"Ping {host} 失败: {e}")
        return False
```

**关键设计点**:

1. **优先级检测**: forticlient 命令 > 指定接口 > 动态查找接口
2. **FortiClient 命令**: 最准确的检测方式，直接查询 VPN 客户端状态
3. **动态接口查找**: 支持 FortiClient 动态生成的接口名称（如 fctvpn16ec49c7）
4. **双重验证**: 接口存在 + 网络连通，两者都满足才认为 VPN 正常
5. **超时控制**: 避免检测卡住
6. **多主机检测**: 提高容错性（任一主机可达即可）

---

### 3.3 orchestrator.py - 重连策略编排器

#### 3.3.1 设计思想

orchestrator 是重连流程的"指挥官"，负责：

- 协调整个重连流程（停止 → 启动 → 等待 → 点击）
- 管理多个驱动（加载、优先级、回退）
- 处理各种异常情况

#### 3.3.2 重连流程

```
reconnect()
    ↓
1. stop_forticlient()
    ├─→ sudo pkill -9 -f forticlient
    └─→ 自动输入 sudo 密码 (xdotool)
    ↓
2. start_forticlient()
    └─→ 点击左边栏图标 (xdotool)
    ↓
3. wait_for_window()
    └─→ 循环检测窗口是否出现 (xdotool search)
    ↓
4. resize_window()
    └─→ 调整窗口大小 (xdotool windowsize)
    ↓
5. 等待 GUI 加载 (sleep)
    ↓
6. click_connect_button()
    ├─→ 尝试 atspi_driver
    ├─→ 尝试 pyauto_driver
    └─→ 尝试 vision_driver
    ↓
7. wait_for_vpn_connection()
    └─→ 检查 ppp0 接口
```

#### 3.3.3 驱动管理逻辑

```python
def _init_drivers(self):
    """初始化驱动"""
    drivers = []

    # 按优先级加载驱动
    for driver_name in self.config['drivers']['priority']:
        driver_config = self.config['drivers'].get(driver_name, {})

        # 检查是否启用
        if not driver_config.get('enabled', True):
            logger.info(f"驱动 {driver_name} 已禁用")
            continue

        # 实例化驱动
        if driver_name == 'atspi':
            drivers.append(ATSPIDriver(self.config))
        elif driver_name == 'pyauto':
            drivers.append(PyAutoDriver(self.config))
        elif driver_name == 'vision':
            drivers.append(VisionDriver(self.config))
        else:
            logger.warning(f"未知驱动: {driver_name}")

    return drivers

def click_connect_button(self):
    """点击连接按钮（尝试所有驱动）"""
    logger.info("尝试点击连接按钮...")

    # 按优先级依次尝试
    for driver in self.drivers:
        driver_name = driver.__class__.__name__
        logger.info(f"尝试驱动: {driver_name}")

        try:
            if driver.click_connect():
                logger.info(f"✅ {driver_name} 成功")
                return True
            else:
                logger.warning(f"⚠️  {driver_name} 失败")

        except Exception as e:
            logger.error(f"❌ {driver_name} 异常: {e}")

    logger.error("所有驱动都失败了")
    return False
```

**关键设计点**:

1. **优先级机制**: 按配置顺序尝试驱动
2. **回退策略**: 一个驱动失败后自动尝试下一个
3. **异常隔离**: 单个驱动异常不影响其他驱动

#### 3.3.4 权限管理优化

系统使用两种免密码机制，避免密码明文存储和自动输入：

**1. sudo 免密码配置**

```bash
# /etc/sudoers.d/forticlient
tsl ALL=(ALL) NOPASSWD: /usr/bin/pkill -9 -f forticlient
```

**2. polkit 免密码配置**

```ini
# /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
[Allow tsl to run FortiClient without password]
Identity=unix-user:tsl
Action=org.fortinet.forticlient.elevate;org.fortinet.fortitray.quit
ResultAny=yes
ResultInactive=yes
ResultActive=yes
```

**stop_forticlient 优化后的实现**:

```python
def stop_forticlient(self):
    """停止 FortiClient"""
    logger.info("停止 FortiClient 进程...")

    try:
        # 尝试使用 sudo 免密码模式
        result = subprocess.run(
            ['sudo', '-n', 'pkill', '-9', '-f', 'forticlient'],
            capture_output=True,
            text=True,
            timeout=10
        )

        logger.debug(f"sudo pkill 返回码: {result.returncode}")

        # 返回码 0 表示成功杀死进程
        # 返回码 1 表示没有找到进程（也算成功）
        # 返回码 137 表示进程被杀死（也算成功）
        if result.returncode in [0, 1, 137]:
            logger.info("✅ FortiClient 进程已停止（sudo 免密码）")
            time.sleep(2)

            # 将光标移动到屏幕中央，避免误触发其他操作
            self.move_cursor_to_center()
            return True

        # 如果免密码失败，尝试不使用 sudo
        logger.warning(f"⚠️  sudo 返回码 {result.returncode}，尝试不使用 sudo...")

        result = subprocess.run(
            ['pkill', '-9', '-f', 'forticlient'],
            capture_output=True,
            text=True,
            timeout=10
        )

        time.sleep(2)
        logger.info("✅ FortiClient 进程已停止")

        # 将光标移动到屏幕中央
        self.move_cursor_to_center()
        return True

    except Exception as e:
        logger.error(f"停止 FortiClient 失败: {e}")
        return False

def move_cursor_to_center(self):
    """将光标移动到屏幕中央"""
    try:
        # 获取屏幕分辨率
        result = subprocess.run(
            ['xdpyinfo'],
            capture_output=True,
            text=True,
            env={'DISPLAY': self.display}
        )

        # 解析分辨率
        import re
        match = re.search(r'dimensions:\s+(\d+)x(\d+)', result.stdout)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            center_x = width // 2
            center_y = height // 2

            logger.info(f"将光标移动到屏幕中央 ({center_x}, {center_y})...")
            subprocess.run(
                ['xdotool', 'mousemove', str(center_x), str(center_y)],
                env={'DISPLAY': self.display}
            )
        else:
            # 如果无法获取分辨率，使用默认值（1920x1080 的中央）
            logger.info("将光标移动到屏幕中央 (960, 540)...")
            subprocess.run(
                ['xdotool', 'mousemove', '960', '540'],
                env={'DISPLAY': self.display}
            )

    except Exception as e:
        logger.debug(f"移动光标失败: {e}")
```

**关键改进**:

1. **sudo 免密码**: 使用 `/etc/sudoers.d/forticlient` 配置，无需在代码中存储密码
2. **polkit 免密码**: 使用 polkit 规则，FortiClient GUI 启动时不弹出密码对话框
3. **光标管理**: 停止 FortiClient 后将光标移动到屏幕中央，避免误触发其他操作
4. **返回码处理**: 正确处理 pkill 的多种返回码（0, 1, 137）
5. **调试日志**: 添加返回码日志，便于故障排查

---

#### 3.3.5 窗口等待优化

系统优化了窗口等待逻辑，增加了重试机制：

```python
def wait_for_window(self):
    """等待窗口出现"""
    window_name = self.config['vpn']['window_name']
    timeout = self.config['reconnect']['window_wait_timeout']
    retry_click_interval = 15  # 每 15 秒重试点击一次

    logger.info(f"等待 {window_name} 窗口出现（最多 {timeout} 秒）...")

    for i in range(timeout):
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--name', window_name],
                capture_output=True,
                text=True,
                env={'DISPLAY': self.display}
            )

            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"✅ 窗口已出现（等待 {i+1} 秒）")
                return True

        except Exception:
            pass

        # 每 15 秒重试点击一次（可能是密码对话框阻止了启动）
        if i > 0 and i % retry_click_interval == 0:
            logger.warning(f"⚠️  窗口尚未出现，重试点击左边栏图标...")
            self.click_sidebar_icon()

        time.sleep(1)

    logger.error(f"❌ 窗口未在 {timeout} 秒内出现")
    return False

def click_sidebar_icon(self):
    """点击左边栏图标"""
    try:
        sidebar_x = self.config['vpn']['gui_sidebar_x']
        sidebar_y = self.config['vpn']['gui_sidebar_y']

        logger.info(f"点击左边栏图标 ({sidebar_x}, {sidebar_y})...")
        subprocess.run(
            ['xdotool', 'mousemove', '--sync', str(sidebar_x), str(sidebar_y)],
            env={'DISPLAY': self.display}
        )
        time.sleep(0.5)
        subprocess.run(
            ['xdotool', 'click', '1'],
            env={'DISPLAY': self.display}
        )
        time.sleep(2)
        return True
    except Exception as e:
        logger.error(f"点击左边栏图标失败: {e}")
        return False
```

**关键改进**:

1. **重试机制**: 如果窗口未出现，每 15 秒重试点击一次左边栏图标
2. **polkit 对话框处理**: 重试点击可以触发 polkit 认证对话框的关闭
3. **独立方法**: 将点击逻辑提取为独立方法，便于复用

---

#### 3.3.6 飞书通知集成

系统集成了飞书通知功能，当 VPN 需要手动 SAML 认证时自动发送截图：

```python
# core/feishu_notifier.py

class FeishuNotifier:
    """飞书通知器"""

    def __init__(self, config):
        """初始化"""
        self.config = config
        self.enabled = config['feishu']['enabled']
        self.user_id = config['feishu']['user_id']
        self.openclaw_bin = config['feishu']['openclaw_bin']
        self.display = config['system']['display']

        if self.enabled:
            logger.info(f"飞书通知已启用，目标用户: {self.user_id}")

    def take_screenshot_and_send(self, caption=""):
        """截图并发送到飞书"""
        if not self.enabled:
            return

        try:
            # 1. 截取屏幕
            screenshot_path = f"/tmp/vpn-saml-{os.getpid()}.png"
            logger.info("正在截取屏幕...")

            result = subprocess.run(
                ['scrot', screenshot_path],
                env={'DISPLAY': self.display},
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error("截图失败")
                return

            logger.info(f"截图已保存: {screenshot_path}")

            # 2. 发送图片到飞书
            self._send_image(screenshot_path)

            # 3. 发送文字消息
            if caption:
                self._send_message(caption)

            # 4. 清理临时文件
            os.remove(screenshot_path)

        except Exception as e:
            logger.error(f"发送飞书通知失败: {e}")

    def _send_image(self, image_path):
        """发送图片"""
        try:
            cmd = f"{self.openclaw_bin} message send --user-id {self.user_id} --image {image_path}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("✅ 飞书图片发送成功")
            else:
                logger.error(f"飞书图片发送失败: {result.stderr}")

        except Exception as e:
            logger.error(f"发送图片异常: {e}")

    def _send_message(self, message):
        """发送文字消息"""
        try:
            cmd = f"{self.openclaw_bin} message send --user-id {self.user_id} --text '{message}'"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("✅ 飞书消息发送成功")
            else:
                logger.error(f"飞书消息发送失败: {result.stderr}")

        except Exception as e:
            logger.error(f"发送消息异常: {e}")
```

**使用场景**:

```python
# 在 orchestrator.py 的 reconnect() 方法中
if button_clicked and not vpn_connected:
    logger.warning("⚠️  VPN 需要手动完成 SAML 认证")
    # 发送截图到飞书
    self.feishu.take_screenshot_and_send(
        caption="⚠️ VPN 需要手动完成 SAML 认证\n"
                "请在浏览器中完成认证流程"
    )
    return False
```

**配置示例**:

```yaml
# config.yaml
feishu:
  enabled: true
  user_id: "ou_b3afb7d2133e4d689be523fc48f3d2b3"
  openclaw_bin: "/usr/bin/pnpm openclaw"
```

---

## 4. 驱动模块详解

### 4.1 驱动接口设计

所有驱动都实现统一的接口：

```python
class Driver:
    def __init__(self, config):
        """初始化驱动"""
        pass

    def click_connect(self) -> bool:
        """点击连接按钮

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        pass
```

### 4.2 atspi_driver.py - AT-SPI 驱动（主方案）

#### 4.2.1 技术原理

AT-SPI (Assistive Technology Service Provider Interface) 是 Linux 的无障碍技术框架，允许程序直接访问 GUI 应用的 UI 元素树。

**优势**:

- 无需截图，速度快
- 直接访问 UI 元素，准确性高
- 不受窗口位置、大小影响

**劣势**:

- 需要应用支持 AT-SPI（大部分 GTK/Qt 应用都支持）
- 需要安装 `python3-pyatspi`

#### 4.2.2 核心代码逻辑

```python
def click_connect(self):
    """点击连接按钮"""
    if not self.available:
        logger.warning("AT-SPI 驱动不可用")
        return False

    try:
        logger.info("使用 AT-SPI 查找按钮...")

        # 1. 获取桌面（所有应用的根节点）
        desktop = self.pyatspi.Registry.getDesktop(0)

        # 2. 遍历所有应用
        for app in desktop:
            if 'forti' in app.name.lower():
                logger.info(f"找到应用: {app.name}")

                # 3. 查找连接按钮
                button = self._find_button(app, 'connect')
                if not button:
                    button = self._find_button(app, 'saml')
                if not button:
                    button = self._find_button(app, 'login')

                # 4. 点击按钮
                if button:
                    logger.info(f"找到按钮: {button.name}")
                    button.doAction(0)  # 执行默认动作（点击）
                    logger.info("✅ AT-SPI 点击成功")
                    return True

        logger.warning("未找到 FortiClient 应用或按钮")
        return False

    except Exception as e:
        logger.error(f"AT-SPI 驱动异常: {e}")
        return False

def _find_button(self, node, keyword):
    """递归查找按钮"""
    try:
        # 1. 检查当前节点
        if node.name and keyword.lower() in node.name.lower():
            # 检查是否是按钮
            if node.getRole() == self.pyatspi.ROLE_PUSH_BUTTON:
                return node

        # 2. 递归查找子节点
        for i in range(node.childCount):
            child = node.getChildAtIndex(i)
            result = self._find_button(child, keyword)
            if result:
                return result

    except Exception:
        pass

    return None
```

**关键技术点**:

1. **UI 树遍历**: 从桌面根节点开始，递归遍历所有应用和 UI 元素
2. **模糊匹配**: 使用关键词（connect/saml/login）匹配按钮名称
3. **角色检查**: 确保找到的元素是按钮（ROLE_PUSH_BUTTON）
4. **动作执行**: 使用 `doAction(0)` 执行默认动作（点击）

---

### 4.3 pyauto_driver.py - PyAutoGUI 驱动（备用方案）

#### 4.3.1 技术原理

PyAutoGUI 是一个跨平台的 GUI 自动化库，使用**图像识别**技术查找屏幕上的元素。

**优势**:

- 跨平台（Windows/macOS/Linux）
- 不依赖应用的无障碍支持
- 适合固定 UI 布局

**劣势**:

- 需要预先截取按钮图像
- 受窗口位置、大小、分辨率影响
- 速度较慢（需要截图 + 图像匹配）

#### 4.3.2 核心代码逻辑

```python
def click_connect(self):
    """点击连接按钮"""
    if not self.available:
        logger.warning("PyAutoGUI 驱动不可用")
        return False

    if not self.button_image or not os.path.exists(self.button_image):
        logger.warning(f"按钮图像不存在: {self.button_image}")
        return False

    try:
        logger.info("使用 PyAutoGUI 查找按钮...")

        # 1. 设置 DISPLAY 环境变量
        os.environ['DISPLAY'] = self.display

        # 2. 在屏幕上查找按钮图像
        location = self.pyautogui.locateCenterOnScreen(
            self.button_image,
            confidence=self.confidence  # 匹配置信度 (0.8)
        )

        # 3. 点击按钮
        if location:
            logger.info(f"找到按钮: {location}")
            self.pyautogui.click(location)
            logger.info("✅ PyAutoGUI 点击成功")
            return True
        else:
            logger.warning("未找到按钮")
            return False

    except Exception as e:
        logger.error(f"PyAutoGUI 驱动异常: {e}")
        return False
```

**关键技术点**:

1. **图像匹配**: 使用 `locateCenterOnScreen` 在屏幕上查找按钮图像
2. **置信度控制**: `confidence=0.8` 允许一定的图像差异
3. **坐标点击**: 找到按钮后直接点击中心坐标

**使用前提**:

- 需要预先截取按钮图像（PNG 格式）
- 图像需要包含完整的按钮（包括边框、文字）
- 配置文件中指定图像路径：`button_image: /path/to/button.png`

---

### 4.4 vision_driver.py - OpenCV 驱动（兜底方案）

#### 4.4.1 技术原理

OpenCV 驱动使用**颜色检测**技术识别按钮，基于以下假设：

- SAML Login 按钮通常是蓝色
- 可以通过 HSV 颜色空间筛选蓝色区域
- 结合尺寸约束和位置约束提高准确性

**优势**:

- 不需要预先截取图像
- 对按钮文字变化不敏感
- 最鲁棒（兜底方案）

**劣势**:

- 速度最慢（截图 + 图像处理）
- 可能误识别其他蓝色元素
- 需要调整颜色范围参数

#### 4.4.2 核心代码逻辑

```python
def click_connect(self):
    """点击连接按钮"""
    if not self.available:
        logger.warning("OpenCV 驱动不可用")
        return False

    try:
        logger.info("使用 OpenCV 查找按钮...")

        # 1. 截图
        if not self._take_screenshot():
            logger.error("截图失败")
            return False

        # 2. 查找按钮
        button = self._find_button()
        if not button:
            logger.warning("未找到按钮")
            return False

        logger.info(f"找到按钮: ({button['center_x']}, {button['center_y']})")

        # 3. 点击按钮
        self._click_button(button['center_x'], button['center_y'])
        logger.info("✅ OpenCV 点击成功")
        return True

    except Exception as e:
        logger.error(f"OpenCV 驱动异常: {e}")
        return False

def _find_button(self):
    """查找按钮"""
    try:
        # 1. 读取截图
        img = self.cv2.imread(self.screenshot_path)
        if img is None:
            logger.error("无法读取截图")
            return None

        # 2. 颜色空间转换（BGR → HSV）
        hsv = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2HSV)

        # 3. 颜色范围筛选（蓝色）
        hsv_lower = self.np.array(self.config['button']['hsv_lower'])  # [100, 100, 100]
        hsv_upper = self.np.array(self.config['button']['hsv_upper'])  # [130, 255, 255]
        mask = self.cv2.inRange(hsv, hsv_lower, hsv_upper)

        # 4. 形态学处理（去噪）
        kernel = self.np.ones((5, 5), self.np.uint8)
        mask = self.cv2.morphologyEx(mask, self.cv2.MORPH_CLOSE, kernel)  # 闭运算（填充空洞）
        mask = self.cv2.morphologyEx(mask, self.cv2.MORPH_OPEN, kernel)   # 开运算（去除噪点）

        # 5. 轮廓检测
        contours, _ = self.cv2.findContours(
            mask,
            self.cv2.RETR_EXTERNAL,      # 只检测外轮廓
            self.cv2.CHAIN_APPROX_SIMPLE # 压缩轮廓
        )

        # 6. 候选筛选
        candidates = []
        screen_center_x = img.shape[1] // 2
        screen_center_y = img.shape[0] // 2

        for contour in contours:
            area = self.cv2.contourArea(contour)
            x, y, w, h = self.cv2.boundingRect(contour)

            # 尺寸约束
            if (self.config['button']['min_area'] <= area <= self.config['button']['max_area'] and
                self.config['button']['min_width'] <= w <= self.config['button']['max_width'] and
                self.config['button']['min_height'] <= h <= self.config['button']['max_height']):

                center_x = x + w // 2
                center_y = y + h // 2
                distance = self.np.sqrt(
                    (center_x - screen_center_x)**2 +
                    (center_y - screen_center_y)**2
                )

                candidates.append({
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'center_x': center_x,
                    'center_y': center_y,
                    'distance': distance
                })

        # 7. 选择最接近屏幕中心的候选
        if candidates:
            candidates.sort(key=lambda c: c['distance'])
            return candidates[0]

        return None

    except Exception as e:
        logger.error(f"查找按钮失败: {e}")
        return None
```

**关键技术点**:

1. **HSV 颜色空间**:
   - HSV (Hue, Saturation, Value) 比 RGB 更适合颜色检测
   - H (色调): 100-130 对应蓝色
   - S (饱和度): 100-255 排除灰色
   - V (明度): 100-255 排除黑色

2. **形态学处理**:
   - 闭运算 (MORPH_CLOSE): 填充按钮内部的小空洞
   - 开运算 (MORPH_OPEN): 去除背景噪点

3. **尺寸约束**:

   ```yaml
   min_area: 2000 # 最小面积（像素²）
   max_area: 50000 # 最大面积
   min_width: 80 # 最小宽度（像素）
   max_width: 300 # 最大宽度
   min_height: 25 # 最小高度
   max_height: 80 # 最大高度
   ```

4. **位置约束**:
   - 计算候选按钮到屏幕中心的距离
   - 选择最接近中心的候选（SAML Login 按钮通常在中心区域）

5. **点击操作**:
   ```python
   def _click_button(self, x, y):
       """点击按钮"""
       # 1. 移动光标
       subprocess.run(['xdotool', 'mousemove', '--sync', str(x), str(y)])
       time.sleep(1.0)

       # 2. 点击
       subprocess.run(['xdotool', 'click', '1'])
       time.sleep(0.5)

       # 3. 按 Enter（确保触发）
       subprocess.run(['xdotool', 'key', 'Return'])
       time.sleep(0.5)
   ```

---

## 5. 状态机流程

### 5.1 完整状态转换图

```
┌─────────────────────────────────────────────────────────────┐
│                        初始化                                │
│  - 加载配置                                                  │
│  - 创建 network_checker                                      │
│  - 创建 orchestrator                                         │
│  - 加载驱动                                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  监控循环    │
                  └──────┬───────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  检测 VPN 状态       │
              └──────┬───────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌────────┐            ┌────────────┐
    │ 正常   │            │  断开      │
    └───┬────┘            └─────┬──────┘
        │                       │
        ▼                       ▼
  consecutive_failures = 0   consecutive_failures += 1
        │                       │
        │                       ▼
        │              ┌─────────────────────┐
        │              │ 失败次数 >= 阈值？  │
        │              └─────┬───────────────┘
        │                    │
        │              ┌─────┴─────┐
        │              │           │
        │              ▼           ▼
        │           [是]         [否]
        │              │           │
        │              ▼           │
        │        ┌──────────┐     │
        │        │ 触发重连 │     │
        │        └────┬─────┘     │
        │             │           │
        │             ▼           │
        │      ┌────────────┐    │
        │      │ 重连流程   │    │
        │      └─────┬──────┘    │
        │            │           │
        │      ┌─────┴─────┐    │
        │      │           │    │
        │      ▼           ▼    │
        │   [成功]      [失败] │
        │      │           │    │
        │      ▼           │    │
        │  consecutive    │    │
        │  _failures = 0  │    │
        │      │           │    │
        └──────┴───────────┴────┘
                 │
                 ▼
          ┌──────────────┐
          │ 等待下一次   │
          │ 检测         │
          └──────┬───────┘
                 │
                 └─────→ (循环)
```

### 5.2 重连流程详细步骤

```
reconnect()
    │
    ├─→ 1. stop_forticlient()
    │       ├─→ 启动 sudo pkill 命令（后台）
    │       ├─→ 等待 2 秒（密码窗口出现）
    │       ├─→ xdotool type <password>
    │       ├─→ xdotool key Return
    │       ├─→ 等待命令完成
    │       └─→ 等待 2 秒（进程完全停止）
    │
    ├─→ 2. start_forticlient()
    │       ├─→ xdotool mousemove <sidebar_x> <sidebar_y>
    │       ├─→ 等待 0.5 秒
    │       ├─→ xdotool click 1
    │       └─→ 等待 2 秒
    │
    ├─→ 3. wait_for_window()
    │       ├─→ 循环检测（最多 30 秒）
    │       │   ├─→ xdotool search --name "FortiClient"
    │       │   ├─→ 找到 → 返回 True
    │       │   └─→ 未找到 → 等待 1 秒 → 继续
    │       └─→ 超时 → 返回 False
    │
    ├─→ 4. resize_window()
    │       ├─→ xdotool search --name "FortiClient" (获取窗口 ID)
    │       ├─→ xdotool getwindowgeometry <window_id>
    │       ├─→ 检查是否是 10x10 像素
    │       ├─→ 是 → xdotool windowmove <window_id> 100 100
    │       │       xdotool windowsize <window_id> 1200 800
    │       └─→ 否 → 跳过
    │
    ├─→ 5. 等待 GUI 加载
    │       └─→ sleep(15)
    │
    ├─→ 6. click_connect_button()
    │       ├─→ 尝试 atspi_driver.click_connect()
    │       │   ├─→ 成功 → 返回 True
    │       │   └─→ 失败 → 继续
    │       ├─→ 尝试 pyauto_driver.click_connect()
    │       │   ├─→ 成功 → 返回 True
    │       │   └─→ 失败 → 继续
    │       ├─→ 尝试 vision_driver.click_connect()
    │       │   ├─→ 成功 → 返回 True
    │       │   └─→ 失败 → 继续
    │       └─→ 所有驱动都失败 → 返回 False
    │
    └─→ 7. wait_for_vpn_connection()
            ├─→ 每 10 秒检查一次（最多 60 秒）
            ├─→ 方法 1: forticlient vpn status (检查 "Status: Connected")
            ├─→ 方法 2: ip addr show fctvpn16ec49c7 (检查接口)
            ├─→ 是 → 返回 True
            └─→ 否 → 返回 False
```

### 5.3 时序控制

系统中的时序控制非常关键，以下是各个等待时间的设计考虑：

| 等待点           | 时间   | 原因                       |
| ---------------- | ------ | -------------------------- |
| pkill 完成后     | 2 秒   | 确保进程完全停止           |
| 点击左边栏图标后 | 2 秒   | 应用启动需要时间           |
| 窗口检测循环     | 1 秒   | 避免 CPU 占用过高          |
| 窗口未出现重试   | 15 秒  | 给 polkit 对话框足够时间   |
| GUI 加载         | 15 秒  | FortiClient 初始化需要时间 |
| 光标移动后       | 1 秒   | 确保光标到位               |
| 点击后           | 0.5 秒 | 确保点击生效               |
| 按 Enter 后      | 0.5 秒 | 确保按键生效               |
| VPN 连接检查间隔 | 10 秒  | 平衡响应速度和 CPU 占用    |
| VPN 连接超时     | 60 秒  | SAML 认证需要时间          |

---

## 6. 重连策略详解

### 6.1 失败计数器机制

```python
# 配置
max_failures = 3          # 最大失败次数
check_interval = 60       # 检测间隔（秒）

# 状态变量
consecutive_failures = 0  # 连续失败次数

# 逻辑
if vpn_connected:
    consecutive_failures = 0
else:
    consecutive_failures += 1
    if consecutive_failures >= max_failures:
        trigger_reconnect()
```

**设计考虑**:

- **避免误触发**: 偶发性网络波动不会立即触发重连
- **快速响应**: 连续失败 3 次（3 分钟）后触发重连
- **自动恢复**: 重连成功后重置计数器

### 6.2 驱动回退策略

```python
drivers = [atspi_driver, pyauto_driver, vision_driver]

for driver in drivers:
    try:
        if driver.click_connect():
            return True  # 成功，停止尝试
    except Exception as e:
        logger.error(f"{driver} 异常: {e}")
        continue  # 失败，尝试下一个

return False  # 所有驱动都失败
```

**设计考虑**:

- **优先级**: AT-SPI > PyAutoGUI > OpenCV
- **隔离性**: 单个驱动异常不影响其他驱动
- **完整性**: 所有驱动都失败才返回失败

### 6.3 重连失败处理

```python
def trigger_reconnect(self):
    """触发重连"""
    success = self.orchestrator.reconnect()

    if success:
        logger.info("✅ VPN 重连成功")
        self.consecutive_failures = 0  # 重置计数器
    else:
        logger.error("❌ VPN 重连失败")
        # 不重置计数器，下次循环继续尝试
```

**设计考虑**:

- **持续重试**: 重连失败后不放弃，下次检测循环继续尝试
- **避免死循环**: 每次重连之间有 `check_interval` 的间隔
- **日志记录**: 详细记录失败原因，便于排查

### 6.4 异常处理策略

```python
try:
    # 主逻辑
    ...
except KeyboardInterrupt:
    logger.info("收到中断信号，退出...")
    break
except Exception as e:
    logger.error(f"监控循环异常: {e}", exc_info=True)
    time.sleep(self.check_interval)
    # 继续循环，不退出
```

**设计考虑**:

- **优雅退出**: 捕获 Ctrl+C 信号，正常退出
- **容错性**: 捕获所有异常，避免程序崩溃
- **可观测性**: 记录完整的异常堆栈，便于调试

---

## 7. 配置系统

### 7.1 配置文件结构

```yaml
# config/config.yaml

# VPN 配置
vpn:
  process_name: forticlient
  launch_method: gui_click
  gui_sidebar_x: 40
  gui_sidebar_y: 200
  window_name: FortiClient
  window_width: 1200
  window_height: 800
  username: your_username
  password: your_password

# 网络检测配置
network:
  check_interval: 60
  check_hosts: [8.8.8.8, 1.1.1.1]
  ping_count: 2
  ping_timeout: 5
  vpn_interface: fctvpn16ec49c7 # FortiClient VPN 接口

# 重连策略配置
reconnect:
  max_failures: 3
  retry_delay: 10
  restart_delay: 2
  window_wait_timeout: 30
  gui_load_delay: 15
  vpn_connect_timeout: 60 # VPN 连接超时（秒），每 10 秒检查一次

# 按钮识别配置
button:
  hsv_lower: [100, 100, 100]
  hsv_upper: [130, 255, 255]
  min_area: 2000
  max_area: 50000
  min_width: 80
  max_width: 300
  min_height: 25
  max_height: 80

# 系统配置
system:
  display: ":1"
  sudo_password: your_password # 已弃用，使用 /etc/sudoers.d/forticlient
  screenshot_path: /tmp/vpn-screenshot.png
  log_level: INFO

# 飞书通知配置
feishu:
  enabled: true
  user_id: "ou_b3afb7d2133e4d689be523fc48f3d2b3"
  openclaw_bin: "/usr/bin/pnpm openclaw" # openclaw 命令路径

# 驱动配置
drivers:
  priority: [atspi, pyauto, vision]
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

### 7.2 配置加载流程

```python
# config_loader.py

import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'config.yaml'

def load_config(config_path=None):
    """加载配置文件"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config
```

**使用方式**:

```python
from core.config_loader import load_config

# 加载默认配置
config = load_config()

# 加载指定配置
config = load_config('/path/to/custom/config.yaml')

# 访问配置
check_interval = config['network']['check_interval']
```

### 7.3 配置验证

建议在生产环境中添加配置验证：

```python
def validate_config(config):
    """验证配置"""
    required_keys = [
        'vpn', 'network', 'reconnect', 'button', 'system', 'drivers'
    ]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"缺少必需的配置项: {key}")

    # 验证数值范围
    if config['network']['check_interval'] < 10:
        raise ValueError("check_interval 不能小于 10 秒")

    if config['reconnect']['max_failures'] < 1:
        raise ValueError("max_failures 不能小于 1")

    # 验证文件路径
    if config['drivers']['pyauto']['enabled']:
        button_image = config['drivers']['pyauto']['button_image']
        if not Path(button_image).exists():
            logger.warning(f"按钮图像不存在: {button_image}")

    return True
```

---

## 8. systemd 服务集成

### 8.1 服务文件

```ini
# vpn-auto.service

[Unit]
Description=VPN Auto Reconnect Service
After=network.target

[Service]
Type=simple
User=tsl
WorkingDirectory=/home/tsl/openclaw/vpn-auto/v2
ExecStart=/home/tsl/openclaw/vpn-auto/v2/run.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**关键配置项**:

- `Type=simple`: 简单服务类型，进程不会 fork
- `User=tsl`: 以 tsl 用户运行（需要访问 X11）
- `WorkingDirectory`: 工作目录（重要！）
- `ExecStart`: 启动脚本（使用绝对路径）
- `Restart=always`: 崩溃后自动重启
- `RestartSec=10`: 重启前等待 10 秒
- `StandardOutput=journal`: 日志输出到 systemd journal

### 8.2 服务管理命令

```bash
# 安装服务
sudo cp vpn-auto.service /etc/systemd/system/
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start vpn-auto.service

# 停止服务
sudo systemctl stop vpn-auto.service

# 重启服务
sudo systemctl restart vpn-auto.service

# 查看状态
sudo systemctl status vpn-auto.service

# 启用开机自启动
sudo systemctl enable vpn-auto.service

# 禁用开机自启动
sudo systemctl disable vpn-auto.service

# 查看日志
sudo journalctl -u vpn-auto.service -f

# 查看最近 100 行日志
sudo journalctl -u vpn-auto.service -n 100

# 查看今天的日志
sudo journalctl -u vpn-auto.service --since today
```

### 8.3 日志系统

系统使用双重日志机制：

1. **systemd journal**: 系统级日志
   - 位置: `/var/log/journal/`
   - 查看: `journalctl -u vpn-auto.service`
   - 优势: 集成到系统日志，支持过滤、搜索

2. **应用日志**: 应用级日志
   - 位置: `vpn-auto/v2/logs/vpn-*.log`
   - 格式: `[2024-01-15 10:30:25] [INFO] 消息内容`
   - 优势: 独立存储，便于归档和分析

**日志配置**:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('logs/vpn-watchdog.log'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
```

---

## 9. 故障排查指南

### 9.1 常见问题

#### 问题 1: 窗口未出现

**症状**:

```
等待 FortiClient 窗口出现（最多 30 秒）...
❌ 窗口未在 30 秒内出现
```

**可能原因**:

1. 左边栏图标坐标不正确
2. FortiClient 未安装或损坏
3. X11 DISPLAY 设置错误

**排查步骤**:

```bash
# 1. 检查 FortiClient 是否安装
which forticlient

# 2. 手动点击左边栏图标，观察坐标
xdotool getmouselocation

# 3. 检查 DISPLAY 环境变量
echo $DISPLAY

# 4. 手动启动 FortiClient
DISPLAY=:1 xdotool mousemove 40 200
DISPLAY=:1 xdotool click 1
```

**解决方案**:

- 调整 `config.yaml` 中的 `gui_sidebar_x` 和 `gui_sidebar_y`
- 确保 DISPLAY 设置正确（通常是 `:1`）

---

#### 问题 2: 未找到按钮

**症状**:

```
使用 AT-SPI 查找按钮...
未找到 FortiClient 应用或按钮
使用 PyAutoGUI 查找按钮...
未找到按钮
使用 OpenCV 查找按钮...
未找到按钮
所有驱动都失败了
```

**可能原因**:

1. GUI 加载时间不足
2. 按钮颜色/尺寸不匹配
3. 窗口大小异常

**排查步骤**:

```bash
# 1. 增加 GUI 加载延迟
# 编辑 config.yaml
gui_load_delay: 20  # 从 15 增加到 20

# 2. 手动截图检查按钮
DISPLAY=:1 scrot /tmp/test.png

# 3. 检查窗口大小
DISPLAY=:1 xdotool search --name FortiClient getwindowgeometry

# 4. 测试 OpenCV 颜色检测
python3 -c "
import cv2
import numpy as np
img = cv2.imread('/tmp/test.png')
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, np.array([100,100,100]), np.array([130,255,255]))
cv2.imwrite('/tmp/mask.png', mask)
print('颜色检测结果已保存到 /tmp/mask.png')
"
```

**解决方案**:

- 增加 `gui_load_delay`
- 调整 `button.hsv_lower` 和 `button.hsv_upper`
- 调整 `button.min_width`, `button.max_width` 等尺寸参数

---

#### 问题 3: VPN 未连接

**症状**:

```
等待 VPN 连接（30 秒）...
检查 VPN 状态...
⚠️  VPN 未连接
```

**可能原因**:

1. SAML 认证需要手动完成
2. 网络问题
3. VPN 服务器问题
4. 凭据错误

**排查步骤**:

```bash
# 1. 检查 ppp0 接口
ip addr show ppp0

# 2. 检查 FortiClient 日志
tail -f ~/.fortinet/forticlient.log

# 3. 手动测试 VPN 连接
# 打开 FortiClient GUI，手动点击连接

# 4. 检查网络连通性
ping 8.8.8.8
```

**解决方案**:

- 增加 `vpn_connect_timeout`（给 SAML 认证更多时间）
- 检查 VPN 凭据是否正确
- 手动完成 SAML 认证（浏览器弹窗）

---

#### 问题 4: 服务无法启动

**症状**:

```bash
sudo systemctl status vpn-auto.service
● vpn-auto.service - VPN Auto Reconnect Service
   Loaded: loaded (/etc/systemd/system/vpn-auto.service; enabled)
   Active: failed (Result: exit-code)
```

**可能原因**:

1. 路径错误
2. 权限问题
3. Python 依赖缺失

**排查步骤**:

```bash
# 1. 查看详细日志
sudo journalctl -u vpn-auto.service -n 50

# 2. 手动运行脚本
bash /home/tsl/openclaw/vpn-auto/v2/run.sh

# 3. 检查 Python 依赖
python3 -c "import pyatspi; import cv2; import numpy; import pyautogui"

# 4. 检查文件权限
ls -la /home/tsl/openclaw/vpn-auto/v2/
```

**解决方案**:

- 确保所有路径使用绝对路径
- 检查文件权限（`chmod +x run.sh`）
- 安装缺失的依赖（`sudo bash install.sh`）

---

### 9.2 调试技巧

#### 9.2.1 启用详细日志

```yaml
# config.yaml
system:
  log_level: DEBUG # 从 INFO 改为 DEBUG
```

#### 9.2.2 单步测试

```bash
# 测试网络检测
python3 -c "
from core.config_loader import load_config
from core.network_check import NetworkChecker
config = load_config()
checker = NetworkChecker(config)
print('VPN 接口:', checker.check_vpn_interface())
print('网络连通性:', checker.check_network_connectivity())
print('VPN 连接:', checker.is_vpn_connected())
"

# 测试驱动
python3 -c "
from core.config_loader import load_config
from drivers.atspi_driver import ATSPIDriver
config = load_config()
driver = ATSPIDriver(config)
print('驱动可用:', driver.available)
"

# 测试重连流程
python3 -c "
from core.config_loader import load_config
from core.orchestrator import ReconnectOrchestrator
config = load_config()
orchestrator = ReconnectOrchestrator(config)
result = orchestrator.reconnect()
print('重连结果:', result)
"
```

#### 9.2.3 截图调试

```bash
# 截取当前屏幕
DISPLAY=:1 scrot /tmp/debug-$(date +%s).png

# 查看截图
xdg-open /tmp/debug-*.png
```

#### 9.2.4 实时监控

```bash
# 监控日志
tail -f vpn-auto/v2/logs/vpn-*.log

# 监控 systemd 日志
sudo journalctl -u vpn-auto.service -f

# 监控网络接口
watch -n 1 'ip addr show ppp0'

# 监控进程
watch -n 1 'ps aux | grep forticlient'
```

---

### 9.3 性能优化

#### 9.3.1 减少检测间隔

```yaml
# config.yaml
network:
  check_interval: 30 # 从 60 秒减少到 30 秒
```

**权衡**:

- 优势: 更快发现 VPN 断开
- 劣势: 更高的 CPU 占用

#### 9.3.2 优化驱动顺序

```yaml
# config.yaml
drivers:
  priority:
    - atspi # 最快，优先使用
    - vision # 较慢，但更鲁棒
    - pyauto # 需要预先截图，最后尝试
```

#### 9.3.3 禁用不需要的驱动

```yaml
# config.yaml
drivers:
  atspi:
    enabled: true
  pyauto:
    enabled: false # 禁用
  vision:
    enabled: true
```

---

### 9.4 安全加固

#### 9.4.1 权限管理最佳实践

**当前方案**（推荐）:

1. **sudo 免密码配置**:

```bash
# /etc/sudoers.d/forticlient
tsl ALL=(ALL) NOPASSWD: /usr/bin/pkill -9 -f forticlient
```

2. **polkit 免密码配置**:

```ini
# /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
[Allow tsl to run FortiClient without password]
Identity=unix-user:tsl
Action=org.fortinet.forticlient.elevate;org.fortinet.fortitray.quit
ResultAny=yes
ResultInactive=yes
ResultActive=yes
```

**优势**:

- 不需要在配置文件中存储密码
- 更安全，只对特定命令/操作生效
- 符合 Linux 安全最佳实践

**配置方法**:

```bash
# 安装脚本会自动配置
sudo bash install.sh

# 或手动配置
sudo cp forticlient-sudoers /etc/sudoers.d/forticlient
sudo chmod 440 /etc/sudoers.d/forticlient
sudo cp forticlient-polkit.pkla /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
sudo chmod 644 /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
sudo systemctl restart polkit
```

详细文档请参考: `POLKIT-CONFIGURATION.md`

#### 9.4.2 文件权限

```bash
# 配置文件权限（只有所有者可读写）
chmod 600 config/config.yaml

# 脚本权限（只有所有者可执行）
chmod 700 run.sh

# 日志目录权限
chmod 700 logs/
```

#### 9.4.3 sudo 免密码（推荐）

```bash
# /etc/sudoers.d/forticlient
tsl ALL=(ALL) NOPASSWD: /usr/bin/pkill -9 -f forticlient
```

**优势**:

- 不需要在配置文件中存储 sudo 密码
- 更安全，只对特定命令生效
- 系统已默认配置

**配置方法**:

```bash
# 通过安装脚本自动配置
sudo bash install.sh

# 或手动配置
sudo cp forticlient-sudoers /etc/sudoers.d/forticlient
sudo chmod 440 /etc/sudoers.d/forticlient
```

---

## 10. 扩展性设计

### 10.1 添加新驱动

1. 在 `drivers/` 目录创建新驱动文件：

```python
# drivers/new_driver.py

import logging

logger = logging.getLogger(__name__)

class NewDriver:
    """新驱动"""

    def __init__(self, config):
        """初始化"""
        self.config = config
        self.available = True  # 检查依赖是否可用
        logger.info("新驱动已加载")

    def click_connect(self):
        """点击连接按钮"""
        try:
            logger.info("使用新驱动查找按钮...")

            # 实现你的逻辑
            # ...

            logger.info("✅ 新驱动点击成功")
            return True

        except Exception as e:
            logger.error(f"新驱动异常: {e}")
            return False
```

2. 在 `orchestrator.py` 中注册驱动：

```python
from drivers.new_driver import NewDriver

def _init_drivers(self):
    """初始化驱动"""
    drivers = []

    for driver_name in self.config['drivers']['priority']:
        # ...
        elif driver_name == 'new':
            drivers.append(NewDriver(self.config))
        # ...

    return drivers
```

3. 在 `config.yaml` 中配置驱动：

```yaml
drivers:
  priority:
    - atspi
    - new # 添加新驱动
    - pyauto
    - vision

  new:
    enabled: true
    # 新驱动的配置参数
```

### 10.2 支持多个 VPN

1. 创建多个配置文件：

```bash
config/
├── config-vpn1.yaml
├── config-vpn2.yaml
└── config-vpn3.yaml
```

2. 创建多个 systemd 服务：

```bash
# vpn-auto-1.service
[Service]
ExecStart=/home/tsl/openclaw/vpn-auto/v2/run.sh -c config/config-vpn1.yaml

# vpn-auto-2.service
[Service]
ExecStart=/home/tsl/openclaw/vpn-auto/v2/run.sh -c config/config-vpn2.yaml
```

3. 使用不同的 DISPLAY：

```yaml
# config-vpn1.yaml
system:
  display: ":1"

# config-vpn2.yaml
system:
  display: ":2"
```

### 10.3 集成到监控系统

#### 10.3.1 Prometheus 集成

```python
# metrics.py

from prometheus_client import Counter, Gauge, start_http_server

# 定义指标
vpn_status = Gauge('vpn_status', 'VPN connection status (1=connected, 0=disconnected)')
vpn_reconnect_total = Counter('vpn_reconnect_total', 'Total number of VPN reconnections')
vpn_reconnect_failures = Counter('vpn_reconnect_failures', 'Total number of failed reconnections')

# 启动 HTTP 服务器
start_http_server(8000)

# 在代码中更新指标
if self.network_checker.is_vpn_connected():
    vpn_status.set(1)
else:
    vpn_status.set(0)

if success:
    vpn_reconnect_total.inc()
else:
    vpn_reconnect_failures.inc()
```

#### 10.3.2 告警集成

```python
# alerting.py

import requests

def send_alert(message):
    """发送告警到飞书"""
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/..."

    payload = {
        "msg_type": "text",
        "content": {
            "text": f"VPN 告警: {message}"
        }
    }

    requests.post(webhook_url, json=payload)

# 在代码中调用
if self.consecutive_failures >= self.max_failures:
    send_alert(f"VPN 连续失败 {self.consecutive_failures} 次，正在尝试重连...")

if not success:
    send_alert("VPN 重连失败，请检查系统状态")
```

---

## 11. 总结

### 11.1 系统特点

1. **模块化设计**: 清晰的分层架构，易于维护和扩展
2. **多重保障**: 多重检测机制 + 多驱动备份方案
3. **生产就绪**: systemd 服务集成 + 详细日志 + 异常处理
4. **可配置性**: YAML 配置文件，灵活调整参数
5. **可观测性**: 双重日志系统，便于故障排查

### 11.2 技术亮点

1. **状态机设计**: 清晰的状态转换逻辑，避免误触发
2. **驱动回退策略**: 多种实现方案，提高成功率
3. **时序控制**: 精确的等待时间，确保流程稳定
4. **异常隔离**: 单个模块异常不影响整体运行
5. **自动化部署**: 一键安装脚本 + systemd 服务

### 11.3 适用场景

- ✅ 需要长期稳定运行的 VPN 连接
- ✅ 网络环境不稳定，经常断线
- ✅ 需要无人值守的自动化运维
- ✅ 需要详细的日志记录和监控
- ✅ 需要灵活的配置和扩展

### 11.4 未来改进方向

1. **智能重连**: 根据历史数据优化重连策略
2. **多 VPN 支持**: 同时管理多个 VPN 连接
3. **Web 管理界面**: 提供可视化的配置和监控
4. **移动端通知**: 支持推送通知到手机
5. **机器学习**: 使用 ML 预测 VPN 断线时间

---

## 12. 参考资料

### 12.1 技术文档

- [AT-SPI 文档](https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/)
- [xdotool 文档](https://www.semicomplete.com/projects/xdotool/)
- [OpenCV Python 教程](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)
- [PyAutoGUI 文档](https://pyautogui.readthedocs.io/)
- [systemd 服务管理](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Python logging 文档](https://docs.python.org/3/library/logging.html)

### 12.2 相关项目

- [pyatspi2](https://gitlab.gnome.org/GNOME/pyatspi2)
- [python-xlib](https://github.com/python-xlib/python-xlib)
- [opencv-python](https://github.com/opencv/opencv-python)

---

## 附录

### A. 完整的依赖列表

```bash
# 系统依赖
sudo apt-get install -y \
    python3 \
    python3-pip \
    xdotool \
    scrot \
    python3-pyatspi

# Python 依赖
pip3 install \
    pyyaml \
    opencv-python \
    numpy \
    pyautogui \
    pillow
```

### B. 目录结构

```
vpn-auto/v2/
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── watchdog.py        # 状态机核心
│   ├── network_check.py   # 网络检测
│   ├── orchestrator.py    # 重连编排
│   ├── config_loader.py   # 配置加载
│   └── feishu_notifier.py # 飞书通知
├── drivers/               # 驱动模块
│   ├── __init__.py
│   ├── atspi_driver.py    # AT-SPI 驱动
│   ├── pyauto_driver.py   # PyAutoGUI 驱动
│   └── vision_driver.py   # OpenCV 驱动
├── services/              # 服务脚本
│   ├── xvfb.sh           # 虚拟桌面
│   └── forti.sh          # FortiClient 管理
├── config/                # 配置文件
│   ├── config.yaml       # 主配置
│   └── button.png        # 按钮图像（可选）
├── logs/                  # 日志目录
│   └── vpn-*.log
├── run.sh                 # 入口脚本
├── install.sh             # 安装脚本
├── vpn-auto.service      # systemd 服务
├── forticlient-sudoers   # sudo 免密码配置
├── forticlient-polkit.pkla # polkit 免密码配置
├── README.md             # 使用说明
├── ARCHITECTURE.md       # 本文档
├── POLKIT-CONFIGURATION.md # polkit 配置文档
└── FEISHU-NOTIFICATION.md  # 飞书通知文档
```

### C. 快速参考

```bash
# 安装
sudo bash install.sh

# 测试运行
bash run.sh

# 安装服务
sudo cp vpn-auto.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vpn-auto.service

# 查看状态
sudo systemctl status vpn-auto.service

# 查看日志
sudo journalctl -u vpn-auto.service -f

# 重启服务
sudo systemctl restart vpn-auto.service
```

---

**文档版本**: v2.0  
**最后更新**: 2026-03-03  
**作者**: VPN Auto Reconnect Team

**更新日志**:

- v2.0 (2026-03-03): 添加 polkit 配置、飞书通知、光标管理、窗口等待优化、FortiClient 状态检测
- v1.0 (2024-01-15): 初始版本
