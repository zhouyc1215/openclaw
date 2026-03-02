# FortiClient GUI 自动化指南

## 概述

使用图像识别技术自动点击 FortiClient 的连接按钮，实现半自动 VPN 连接。

## 工作原理

1. **图像识别**：使用 PyAutoGUI + OpenCV 识别屏幕上的连接按钮
2. **自动点击**：找到按钮后自动点击
3. **MFA 认证**：用户在手机上完成 Microsoft MFA 认证
4. **连接完成**：VPN 自动连接成功

## 安装步骤

### 1. 安装依赖

```bash
cd /home/tsl/openclaw/vpn-auto
./install-gui-automation.sh
```

这将安装：

- pyautogui（GUI 自动化）
- opencv-python-headless（图像识别）
- pillow（图像处理）
- scrot（屏幕截图工具）
- python3-tk（GUI 支持）

### 2. 捕获连接按钮图像

**重要**：必须先捕获连接按钮的图像，才能使用自动化功能。

```bash
cd /home/tsl/openclaw/vpn-auto
python3 capture-button.py
```

按照提示操作：

1. 打开 FortiClient 窗口
2. 将鼠标移动到"连接"按钮的左上角
3. 按 Enter 键
4. 将鼠标移动到"连接"按钮的右下角
5. 按 Enter 键

图像将保存到 `images/connect_button.png`

### 3. 测试自动连接

```bash
python3 gui-auto-connect.py
```

如果成功，你会看到：

- ✅ FortiClient GUI 已启动
- ✅ 成功点击连接按钮
- ✅ VPN 连接已触发
- 请在手机上完成 MFA 认证

## 使用方法

### 方法 1：手动测试

```bash
cd /home/tsl/openclaw/vpn-auto
python3 gui-auto-connect.py
```

### 方法 2：集成到监控服务

监控脚本 `vpn-monitor.sh` 已经集成了 GUI 自动化功能。

安装监控服务：

```bash
cd /home/tsl/openclaw/vpn-auto
./install-monitor.sh
```

启动服务：

```bash
sudo systemctl start vpn-monitor
```

查看日志：

```bash
# 系统日志
journalctl -u vpn-monitor -f

# 文件日志
tail -f /home/tsl/openclaw/vpn-auto/monitor.log
```

## 工作流程

```
VPN 断开检测
    ↓
启动 FortiClient GUI
    ↓
图像识别查找连接按钮
    ↓
自动点击连接按钮
    ↓
发送飞书通知
    ↓
等待用户完成 MFA 认证
    ↓
VPN 连接成功
```

## 故障排查

### 问题 1：找不到连接按钮

**原因**：按钮图像未捕获或图像不匹配

**解决方案**：

1. 重新运行 `capture-button.py` 捕获按钮图像
2. 确保 FortiClient 窗口可见且未被遮挡
3. 降低匹配置信度（编辑 `gui-auto-connect.py`，修改 `CONFIDENCE = 0.7`）

### 问题 2：无法截图

**原因**：缺少 scrot 工具或 DISPLAY 环境变量未设置

**解决方案**：

```bash
sudo apt-get install scrot
export DISPLAY=:0
```

### 问题 3：Python 依赖缺失

**原因**：依赖未安装

**解决方案**：

```bash
pip3 install --user pyautogui opencv-python-headless pillow
```

### 问题 4：GUI 自动化失败，回退到命令行

**现象**：日志显示"GUI 自动化失败，尝试命令行方式..."

**原因**：图像识别失败或按钮位置变化

**解决方案**：

1. 重新捕获按钮图像
2. 检查 FortiClient 窗口是否可见
3. 手动完成连接

## 调试技巧

### 1. 捕获全屏截图

```bash
python3 capture-button.py --fullscreen
```

查看 `fullscreen.png` 确认屏幕内容

### 2. 查看调试截图

运行 `gui-auto-connect.py` 后，会生成 `debug_screen.png`，可以查看识别时的屏幕状态

### 3. 降低置信度

如果按钮识别不准确，可以降低匹配置信度：

编辑 `gui-auto-connect.py`：

```python
CONFIDENCE = 0.7  # 从 0.8 降低到 0.7
```

### 4. 添加多个按钮图像

如果按钮在不同状态下外观不同，可以捕获多个图像：

```bash
# 捕获第一个状态
python3 capture-button.py
# 图像保存为 images/connect_button.png

# 手动重命名
mv images/connect_button.png images/connect_button_alt.png

# 捕获第二个状态
python3 capture-button.py
```

## 高级配置

### 自定义图像路径

编辑 `gui-auto-connect.py`：

```python
connect_images = [
    os.path.join(IMAGES_DIR, "connect_button.png"),
    os.path.join(IMAGES_DIR, "connect_button_alt.png"),
    os.path.join(IMAGES_DIR, "connect_button_zh.png"),  # 中文界面
]
```

### 调整重试次数和延迟

编辑 `gui-auto-connect.py`：

```python
MAX_RETRIES = 5  # 增加重试次数
RETRY_DELAY = 3  # 增加重试延迟（秒）
```

### 调整匹配置信度

编辑 `gui-auto-connect.py`：

```python
CONFIDENCE = 0.75  # 0.0-1.0，越高越严格
```

## 文件说明

- `gui-auto-connect.py` - GUI 自动化主脚本
- `capture-button.py` - 按钮图像捕获工具
- `install-gui-automation.sh` - 依赖安装脚本
- `images/connect_button.png` - 连接按钮图像（需要捕获）
- `debug_screen.png` - 调试截图（自动生成）
- `fullscreen.png` - 全屏截图（可选）

## 安全建议

1. **图像文件权限**：

   ```bash
   chmod 600 images/*.png
   ```

2. **不要提交到 Git**：
   - 按钮图像可能包含敏感信息
   - 已添加到 `.gitignore`

3. **定期更新图像**：
   - FortiClient 更新后，按钮外观可能变化
   - 需要重新捕获图像

## 性能优化

- **图像大小**：捕获的按钮图像越小，识别越快
- **置信度**：适当降低置信度可以提高识别成功率
- **重试策略**：合理设置重试次数和延迟

## 总结

GUI 自动化方案的优势：

- ✅ 无需修改 FortiClient
- ✅ 适用于任何 GUI 应用
- ✅ 图像识别比坐标点击更可靠
- ✅ 易于调试和维护

局限性：

- ❌ 需要图形界面（X11）
- ❌ 按钮外观变化需要重新捕获
- ❌ 仍需手动完成 MFA 认证

---

**创建时间**: 2026-03-02  
**版本**: 1.0  
**作者**: Kiro AI Assistant
