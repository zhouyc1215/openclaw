# FortiClient VPN 自动连接技术文档

## 概述

本文档详细介绍 FortiClient VPN 自动连接脚本的实现原理、技术细节和代码逻辑。该解决方案通过 GUI 自动化技术实现 FortiClient 的自动重启和 SAML 登录按钮的自动点击。

## 系统架构

### 组件结构

```
vpn-auto/
├── final-complete-auto-connect.sh  # 主控制脚本（Bash）
└── simple-click-button.py          # 按钮识别和点击脚本（Python）
```

### 技术栈

- **Shell Script (Bash)**: 流程控制和系统命令执行
- **Python 3**: 图像处理和按钮识别
- **xdotool**: X11 GUI 自动化工具
- **OpenCV (cv2)**: 计算机视觉库，用于按钮识别
- **scrot**: 屏幕截图工具

## 工作流程

### 整体流程图

```
开始
  ↓
1. 停止 FortiClient 进程
  ↓
2. GUI 自动输入 sudo 密码
  ↓
3. 点击左边栏图标启动 FortiClient
  ↓
4. 等待窗口出现（最多 30 秒）
  ↓
5. 等待 GUI 完全加载（15 秒）
  ↓
6. 调用 Python 脚本识别并点击 SAML Login 按钮
  ↓
7. 等待 VPN 连接（30 秒）
  ↓
8. 检查 VPN 连接状态
  ↓
结束
```

## 详细实现

### 第一部分：主控制脚本 (final-complete-auto-connect.sh)

#### 1. 环境配置

```bash
DISPLAY=:1
SUDO_PASSWORD="tsl123"
```

**说明**:

- `DISPLAY=:1`: 指定 X11 显示服务器，FortiClient GUI 运行在 DISPLAY :1 上
- `SUDO_PASSWORD`: sudo 密码（用于停止 FortiClient 进程）

#### 2. 日志函数

```bash
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}
```

**功能**: 输出带时间戳的日志信息

**实现原理**:

- 使用 `date` 命令获取当前时间
- 格式化为 `YYYY-MM-DD HH:MM:SS`
- 与日志消息拼接输出

#### 3. 停止 FortiClient 进程

```bash
# 启动 sudo 命令（会弹出密码输入窗口）
sudo pkill -9 -f forticlient 2>/dev/null &
SUDO_PID=$!

# 等待密码输入窗口出现
sleep 2

# 在 GUI 模式下自动输入密码
log "自动输入密码..."
DISPLAY=$DISPLAY xdotool type "tsl123"
sleep 0.5
DISPLAY=$DISPLAY xdotool key Return
sleep 1

# 等待 sudo 命令完成
wait $SUDO_PID 2>/dev/null || true
sleep 2
```

**实现原理**:

1. **后台执行 sudo 命令**
   - `sudo pkill -9 -f forticlient &`: 在后台执行，不阻塞脚本
   - `SUDO_PID=$!`: 保存后台进程 PID
   - `-9`: 强制终止信号（SIGKILL）
   - `-f forticlient`: 匹配进程命令行中包含 "forticlient" 的进程

2. **GUI 密码输入自动化**
   - `sleep 2`: 等待 GUI 密码输入窗口出现
   - `xdotool type "tsl123"`: 模拟键盘输入密码
   - `xdotool key Return`: 模拟按下回车键

3. **等待命令完成**
   - `wait $SUDO_PID`: 等待 sudo 命令执行完成
   - `|| true`: 即使 wait 失败也继续执行

**关键技术点**:

- 使用后台进程 + GUI 自动化解决 sudo 密码输入问题
- xdotool 可以在 X11 环境中模拟键盘和鼠标操作

#### 4. 启动 FortiClient

```bash
SIDEBAR_X=40
BUTTON_Y=200  # 第三个按钮的 Y 坐标

DISPLAY=$DISPLAY xdotool mousemove --sync $SIDEBAR_X $BUTTON_Y
sleep 0.5
DISPLAY=$DISPLAY xdotool click 1
sleep 2
```

**实现原理**:

1. **坐标计算**
   - 左边栏位于屏幕左侧，X 坐标固定为 40
   - 第三个按钮的 Y 坐标计算：
     ```
     Y = top_margin + (button_number - 1) * (button_size + button_spacing) + button_size / 2
     Y = 20 + (3 - 1) * (64 + 10) + 64 / 2 = 200
     ```

2. **鼠标操作**
   - `mousemove --sync`: 移动鼠标到指定坐标，`--sync` 确保移动完成后再继续
   - `click 1`: 模拟鼠标左键点击（1 = 左键，2 = 中键，3 = 右键）

**关键技术点**:

- GUI 元素定位：通过固定坐标定位左边栏图标
- 同步操作：使用 `--sync` 确保操作顺序

#### 5. 等待窗口出现

```bash
for i in {1..30}; do
    if DISPLAY=$DISPLAY xdotool search --name "FortiClient" > /dev/null 2>&1; then
        log "✅ 窗口已出现（等待 $i 秒）"
        break
    fi
    sleep 1
done

if ! DISPLAY=$DISPLAY xdotool search --name "FortiClient" > /dev/null 2>&1; then
    log "❌ FortiClient 窗口未出现"
    exit 1
fi
```

**实现原理**:

1. **窗口检测循环**
   - 循环 30 次，每次间隔 1 秒
   - `xdotool search --name "FortiClient"`: 搜索窗口标题包含 "FortiClient" 的窗口
   - 找到窗口后立即 `break` 退出循环

2. **超时处理**
   - 循环结束后再次检查窗口是否存在
   - 如果不存在，输出错误并退出（exit 1）

**关键技术点**:

- 轮询机制：定期检查窗口状态
- 超时保护：避免无限等待

#### 6. 等待 GUI 加载

```bash
log "等待 GUI 完全加载（15 秒）..."
sleep 15
log "✅ GUI 应该已完全加载"
```

**实现原理**:

- 固定等待 15 秒，确保 FortiClient GUI 完全加载
- 这是一个经验值，根据实际测试确定

**优化建议**:

- 可以改为检测特定 GUI 元素是否出现，而不是固定等待

#### 7. 调用 Python 脚本点击按钮

```bash
cd "$(dirname "$0")"
python3 simple-click-button.py
```

**实现原理**:

- `dirname "$0"`: 获取脚本所在目录
- `cd`: 切换到脚本目录，确保相对路径正确
- 调用 Python 脚本执行按钮识别和点击

#### 8. 检查 VPN 连接状态

```bash
if ip addr show ppp0 2>/dev/null | grep -q "inet "; then
    log "✅ VPN 已连接！"
    ip addr show ppp0 | grep "inet "
    exit 0
else
    log "⚠️  VPN 未连接，可能需要手动完成 SAML 认证"
    exit 1
fi
```

**实现原理**:

1. **网络接口检查**
   - `ip addr show ppp0`: 显示 ppp0 网络接口信息
   - VPN 连接成功后会创建 ppp0 接口
   - `grep -q "inet "`: 检查是否有 IP 地址分配

2. **返回状态**
   - 成功：exit 0
   - 失败：exit 1

**关键技术点**:

- Linux 网络接口：VPN 连接通常使用 ppp0 接口
- 状态检测：通过 IP 地址判断连接状态

### 第二部分：按钮识别脚本 (simple-click-button.py)

#### 1. 配置参数

```python
SCREENSHOT = "screen.png"
DISPLAY = ":1"

# 深蓝色的 HSV 范围
BLUE_LOWER = np.array([100, 100, 100])
BLUE_UPPER = np.array([130, 255, 255])

# 按钮尺寸范围
MIN_BUTTON_AREA = 2000
MAX_BUTTON_AREA = 50000
MIN_BUTTON_WIDTH = 80
MAX_BUTTON_WIDTH = 300
MIN_BUTTON_HEIGHT = 25
MAX_BUTTON_HEIGHT = 80
```

**说明**:

1. **HSV 颜色空间**
   - H (Hue): 色调，100-130 对应蓝色
   - S (Saturation): 饱和度，100-255 表示较高饱和度
   - V (Value): 明度，100-255 表示较亮

2. **按钮尺寸约束**
   - 面积：2000-50000 像素
   - 宽度：80-300 像素
   - 高度：25-80 像素

**为什么使用 HSV 而不是 RGB**:

- HSV 对光照变化更鲁棒
- 更容易定义颜色范围
- H 通道直接表示颜色，便于筛选

#### 2. 窗口检查和调整

```python
def check_forticlient_running():
    """检查 FortiClient 是否运行"""
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        return result.returncode == 0 and result.stdout.strip()
    except Exception:
        return False
```

**实现原理**:

- 使用 xdotool 搜索窗口
- 返回值为 0 且有输出表示窗口存在

```python
def resize_window_if_needed():
    """如果窗口太小，调整大小"""
    # 获取窗口 ID
    window_id = result.stdout.strip().split('\n')[0]

    # 获取窗口几何信息
    geom_result = subprocess.run(
        ["xdotool", "getwindowgeometry", window_id],
        ...
    )

    # 检查是否需要调整
    if "10x10" in geom_result.stdout:
        # 移动窗口
        subprocess.run(["xdotool", "windowmove", window_id, "100", "100"], ...)
        # 调整大小
        subprocess.run(["xdotool", "windowsize", window_id, "1200", "800"], ...)
```

**实现原理**:

- FortiClient 启动时窗口可能只有 10x10 像素
- 需要调整为 1200x800 以便正确显示和截图

#### 3. 屏幕截图

```python
def take_screenshot():
    """截图"""
    os.environ['DISPLAY'] = DISPLAY
    result = subprocess.run(["scrot", SCREENSHOT], capture_output=True)
    return result.returncode == 0
```

**实现原理**:

- 使用 scrot 工具截取整个屏幕
- 保存为 PNG 格式
- 返回值表示是否成功

#### 4. 按钮识别算法

```python
def find_button(img):
    """查找按钮"""
    # 1. 颜色空间转换
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 2. 颜色范围筛选
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)

    # 3. 形态学处理
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 4. 轮廓检测
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. 候选筛选
    candidates = []
    screen_center_x = img.shape[1] // 2
    screen_center_y = img.shape[0] // 2

    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)

        # 尺寸约束
        if (MIN_BUTTON_AREA <= area <= MAX_BUTTON_AREA and
            MIN_BUTTON_WIDTH <= w <= MAX_BUTTON_WIDTH and
            MIN_BUTTON_HEIGHT <= h <= MAX_BUTTON_HEIGHT):

            center_x = x + w // 2
            center_y = y + h // 2
            distance = np.sqrt((center_x - screen_center_x)**2 +
                             (center_y - screen_center_y)**2)

            candidates.append({
                'center_x': center_x,
                'center_y': center_y,
                'distance': distance
            })

    # 6. 选择最接近屏幕中心的候选
    candidates.sort(key=lambda c: c['distance'])
    return candidates[0] if candidates else None
```

**算法详解**:

**步骤 1: 颜色空间转换**

- BGR → HSV
- OpenCV 默认使用 BGR 格式，需要转换为 HSV

**步骤 2: 颜色范围筛选**

- `cv2.inRange()`: 创建二值掩码
- 在范围内的像素设为 255（白色）
- 范围外的像素设为 0（黑色）

**步骤 3: 形态学处理**

- **MORPH_CLOSE (闭运算)**: 填充小孔洞
  - 先膨胀后腐蚀
  - 连接相邻的区域
- **MORPH_OPEN (开运算)**: 去除小噪点
  - 先腐蚀后膨胀
  - 消除孤立的小点

**步骤 4: 轮廓检测**

- `cv2.findContours()`: 查找所有连通区域的轮廓
- `RETR_EXTERNAL`: 只检测外部轮廓
- `CHAIN_APPROX_SIMPLE`: 压缩轮廓，节省内存

**步骤 5: 候选筛选**

- 计算每个轮廓的面积和边界框
- 应用尺寸约束过滤
- 计算到屏幕中心的距离

**步骤 6: 选择最佳候选**

- 按距离排序
- 选择最接近屏幕中心的按钮
- 假设：SAML Login 按钮通常在屏幕中央附近

**关键技术点**:

- 计算机视觉：颜色检测 + 形态学处理
- 启发式规则：尺寸约束 + 位置优先级

#### 5. 按钮点击

```python
def click_button(x, y):
    """点击按钮"""
    os.environ['DISPLAY'] = DISPLAY

    # 移动光标
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)],
                   env={"DISPLAY": DISPLAY})
    time.sleep(1.0)

    # 点击
    subprocess.run(["xdotool", "click", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)

    # 按 Enter
    subprocess.run(["xdotool", "key", "Return"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
```

**实现原理**:

1. **移动鼠标**
   - `mousemove --sync`: 同步移动到目标坐标
   - 等待 1 秒，确保 hover 效果触发

2. **点击**
   - `click 1`: 模拟鼠标左键点击
   - 等待 0.5 秒

3. **按 Enter**
   - `key Return`: 模拟回车键
   - 某些按钮需要回车确认

**为什么需要 Enter 键**:

- 有些 Web 表单按钮需要回车触发
- 增加操作的可靠性

## 技术难点和解决方案

### 难点 1: sudo 密码自动输入

**问题**: sudo 命令需要密码，但脚本无法直接传递

**解决方案**:

1. 后台执行 sudo 命令
2. 等待 GUI 密码输入窗口出现
3. 使用 xdotool 模拟键盘输入密码

**代码**:

```bash
sudo pkill -9 -f forticlient &
sleep 2
xdotool type "password"
xdotool key Return
```

### 难点 2: FortiClient 窗口大小异常

**问题**: FortiClient 启动时窗口只有 10x10 像素

**解决方案**:

1. 检测窗口大小
2. 如果太小，使用 xdotool 调整为 1200x800

**代码**:

```python
if "10x10" in geom_result.stdout:
    subprocess.run(["xdotool", "windowsize", window_id, "1200", "800"])
```

### 难点 3: 按钮颜色和位置不固定

**问题**: SAML Login 按钮的颜色和位置可能变化

**解决方案**:

1. 使用 HSV 颜色空间，对光照变化更鲁棒
2. 设置宽松的颜色范围
3. 使用形态学处理去噪
4. 优先选择靠近屏幕中心的按钮

### 难点 4: GUI 加载时间不确定

**问题**: FortiClient GUI 加载时间不固定

**解决方案**:

1. 使用轮询机制检测窗口出现
2. 设置超时时间（30 秒）
3. 固定等待 15 秒确保完全加载

## 性能优化

### 1. 并发执行

- sudo 命令后台执行，不阻塞主流程
- 使用 `&` 和 `wait` 实现异步操作

### 2. 超时保护

- 所有等待操作都有超时限制
- 避免无限等待导致脚本挂起

### 3. 错误处理

- 每个关键步骤都有错误检查
- 失败时输出明确的错误信息并退出

## 依赖项

### 系统工具

- **xdotool**: X11 GUI 自动化

  ```bash
  sudo apt-get install xdotool
  ```

- **scrot**: 屏幕截图
  ```bash
  sudo apt-get install scrot
  ```

### Python 库

- **OpenCV**: 图像处理

  ```bash
  pip3 install opencv-python-headless
  ```

- **NumPy**: 数值计算
  ```bash
  pip3 install numpy
  ```

## 使用方法

### 基本用法

```bash
bash vpn-auto/final-complete-auto-connect.sh
```

### 返回值

- **0**: VPN 连接成功
- **1**: VPN 连接失败或需要手动完成 SAML 认证

### 日志输出

脚本会输出详细的执行日志，包括：

- 每个步骤的开始和结束
- 等待时间和超时信息
- 成功/失败状态

## 故障排查

### 问题 1: 窗口未出现

**可能原因**:

- 左边栏图标位置不正确
- FortiClient 未安装或路径错误

**解决方法**:

- 检查 SIDEBAR_X 和 BUTTON_Y 坐标
- 手动启动 FortiClient 验证

### 问题 2: 未找到按钮

**可能原因**:

- GUI 未完全加载
- 按钮颜色不在检测范围内
- 窗口大小不正确

**解决方法**:

- 增加等待时间
- 调整颜色范围参数
- 检查窗口大小

### 问题 3: VPN 未连接

**可能原因**:

- SAML 认证需要手动完成
- 网络问题
- VPN 服务器不可达

**解决方法**:

- 在浏览器中手动完成 SAML 认证
- 检查网络连接
- 联系 IT 支持

## 安全考虑

### 密码存储

**当前实现**:

- 密码明文存储在脚本中

**安全建议**:

1. 使用环境变量存储密码
2. 使用加密存储（如 keyring）
3. 配置 sudo 免密码（仅限特定命令）

**改进示例**:

```bash
# 使用环境变量
SUDO_PASSWORD="${VPN_SUDO_PASSWORD:-tsl123}"

# 或使用 sudo 免密码配置
# /etc/sudoers.d/forticlient
# tsl ALL=(ALL) NOPASSWD: /usr/bin/pkill -9 -f forticlient
```

### 权限控制

- 脚本应设置适当的文件权限（600 或 700）
- 避免在共享环境中使用

## 扩展性

### 支持多个 VPN 配置

可以通过参数传递不同的配置：

```bash
#!/bin/bash
VPN_NAME="${1:-default}"
CONFIG_FILE="~/.vpn-configs/${VPN_NAME}.conf"

source "$CONFIG_FILE"
# 使用配置文件中的参数
```

### 支持不同的认证方式

可以扩展支持其他认证方式：

- 用户名/密码认证
- 证书认证
- 双因素认证

### 集成到系统服务

可以创建 systemd 服务自动运行：

```ini
[Unit]
Description=VPN Auto Connect
After=network.target

[Service]
Type=oneshot
ExecStart=/path/to/final-complete-auto-connect.sh
User=tsl

[Install]
WantedBy=multi-user.target
```

## 总结

本脚本通过以下技术实现 FortiClient VPN 的自动连接：

1. **GUI 自动化**: 使用 xdotool 模拟鼠标和键盘操作
2. **计算机视觉**: 使用 OpenCV 识别 SAML Login 按钮
3. **流程控制**: Bash 脚本协调整个流程
4. **错误处理**: 完善的超时和错误检查机制

该解决方案具有以下特点：

- ✅ 完全自动化，无需人工干预
- ✅ 鲁棒性强，能处理各种异常情况
- ✅ 可扩展性好，易于修改和维护
- ✅ 日志详细，便于故障排查

## 参考资料

- [xdotool 文档](https://www.semicomplete.com/projects/xdotool/)
- [OpenCV Python 教程](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)
- [HSV 颜色空间](https://en.wikipedia.org/wiki/HSL_and_HSV)
- [形态学图像处理](https://docs.opencv.org/master/d9/d61/tutorial_py_morphological_ops.html)
