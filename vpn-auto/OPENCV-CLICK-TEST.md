# OpenCV 模板匹配测试报告

## 测试时间

2026-03-02 16:18:06

## 测试方法

使用 OpenCV `cv2.matchTemplate` 进行模板匹配 + xdotool 点击

## 测试结果

### ✅ 模板匹配成功

```
屏幕尺寸: 1920x1080
模板尺寸: 768x324
匹配度: 1.000 (完美匹配！)
找到按钮位置: (960, 810)
左上角: (576, 648)
```

### ✅ 点击执行成功

```
移动鼠标到 (960, 810)
点击坐标 (960, 810)
```

### ❌ VPN 未连接

```
Status: Not Running
```

## 问题分析

### 为什么点击没有触发连接？

1. **点击位置可能不准确**
   - 模板图像太大（768x324），包含了按钮周围的大量区域
   - 点击中心点 (960, 810) 可能不在实际按钮的可点击区域内

2. **窗口焦点问题**
   - FortiClient 窗口可能没有获得焦点
   - 需要先激活窗口再点击

3. **按钮状态问题**
   - 按钮可能处于禁用状态
   - 需要先执行其他操作（如输入用户名密码）

## 解决方案

### 方案 1: 使用更小的模板图像 ✅

重新捕获只包含按钮本身的小图像：

```bash
# 使用之前创建的工具
python3 recapture-small-button.py
```

这会创建一个 120x34 的小按钮图像，更精确。

### 方案 2: 先激活窗口再点击 ✅

```python
# 查找 FortiClient 窗口
window_id = subprocess.check_output(
    ["xdotool", "search", "--name", "FortiClient"]
).decode().strip().split('\n')[0]

# 激活窗口
subprocess.run(["xdotool", "windowactivate", window_id])
time.sleep(0.5)

# 然后点击
subprocess.run(["xdotool", "mousemove", str(x), str(y)])
subprocess.run(["xdotool", "click", "1"])
```

### 方案 3: 使用命令行工具（最可靠）✅

```bash
# 直接使用 openfortivpn
echo "tsl123" | sudo -S openfortivpn -c /etc/openfortivpn/config &
```

## 对比：不同方案的效果

| 方案                  | 模板匹配  | 点击执行 | VPN 连接 | 可靠性 |
| --------------------- | --------- | -------- | -------- | ------ |
| pyautogui             | ✅        | ✅       | ❌       | 低     |
| OpenCV + xdotool      | ✅ (完美) | ✅       | ❌       | 中     |
| OpenCV + 小模板       | 待测试    | 待测试   | 待测试   | 中     |
| 命令行 (openfortivpn) | N/A       | N/A      | ✅       | 高     |

## 下一步测试

### 1. 测试小模板图像

```bash
cd /home/tsl/openclaw/vpn-auto

# 创建小模板
python3 recapture-small-button.py

# 修改脚本使用小模板
# TEMPLATE = "images/saml_button_small.png"

# 重新测试
python3 opencv-auto-click.py
```

### 2. 添加窗口激活

修改 `opencv-auto-click.py` 添加窗口激活逻辑

### 3. 验证按钮是否可点击

- 检查按钮是否处于禁用状态
- 查看 FortiClient 窗口的实际状态
- 可能需要先完成其他步骤（如选择 VPN 配置）

## 技术优势

### OpenCV 模板匹配的优点

1. ✅ 匹配精度高（1.000 完美匹配）
2. ✅ 不依赖特定的 GUI 库
3. ✅ 可以调整阈值适应不同情况
4. ✅ 返回准确的坐标位置

### xdotool 的优点

1. ✅ 轻量级，不需要 Python 库
2. ✅ 可以激活窗口
3. ✅ 支持相对坐标和绝对坐标
4. ✅ 可以模拟键盘输入

## 总结

✅ **OpenCV 模板匹配技术验证成功**

- 完美匹配度（1.000）
- 准确定位按钮位置
- 成功执行点击操作

❌ **VPN 连接未成功**

- 可能是点击位置不够精确（模板太大）
- 可能是窗口焦点问题
- 建议使用更小的模板图像或命令行工具

**推荐方案：**

1. 短期：使用 `openfortivpn` 命令行工具（最可靠）
2. 长期：优化 GUI 自动化（使用小模板 + 窗口激活）
