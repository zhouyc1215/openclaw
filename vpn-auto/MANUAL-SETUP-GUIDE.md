# GUI 自动化手动配置指南

## 当前状态

✅ **所有依赖已安装**

- Python 3.8.10
- pyautogui 0.9.54
- opencv 4.13.0
- PIL/Pillow
- scrot

✅ **X11 权限已配置**

- DISPLAY=:1
- xhost 权限已添加

✅ **FortiClient 正在运行**

⏸️ **待完成：捕获连接按钮图像**

## 下一步：捕获连接按钮图像

### 方法 1：使用捕获工具（推荐）

1. 打开终端，运行：

   ```bash
   cd /home/tsl/openclaw/vpn-auto
   export DISPLAY=:1
   python3 capture-button.py
   ```

2. 按照提示操作：
   - 确保 FortiClient 窗口可见
   - 将鼠标移动到"连接"按钮的左上角
   - 按 Enter 键
   - 将鼠标移动到"连接"按钮的右下角
   - 按 Enter 键

3. 图像将保存到 `images/connect_button.png`

### 方法 2：手动截图（备选）

如果自动捕获工具无法使用，可以手动截图：

1. 打开 FortiClient 窗口

2. 使用截图工具（如 GNOME Screenshot）：

   ```bash
   gnome-screenshot -a
   ```

3. 选择连接按钮区域并保存

4. 将图像保存为：
   ```bash
   /home/tsl/openclaw/vpn-auto/images/connect_button.png
   ```

### 方法 3：使用全屏截图手动裁剪

1. 查看已保存的全屏截图：

   ```bash
   eog /home/tsl/openclaw/vpn-auto/fullscreen.png
   ```

2. 找到 FortiClient 连接按钮的位置

3. 使用图像编辑工具（如 GIMP）裁剪按钮区域：

   ```bash
   gimp /home/tsl/openclaw/vpn-auto/fullscreen.png
   ```

4. 裁剪后保存为：
   ```bash
   /home/tsl/openclaw/vpn-auto/images/connect_button.png
   ```

## 测试 GUI 自动化

捕获按钮图像后，测试自动连接：

```bash
cd /home/tsl/openclaw/vpn-auto
export DISPLAY=:1
python3 gui-auto-connect.py
```

预期输出：

```
[2026-03-02 14:50:00] ========================================
[2026-03-02 14:50:00] 开始 VPN 自动连接
[2026-03-02 14:50:00] ========================================
[2026-03-02 14:50:00] 设置 DISPLAY=:1
[2026-03-02 14:50:00] FortiClient 已在运行
[2026-03-02 14:50:02] 截图已保存: debug_screen.png
[2026-03-02 14:50:02] 尝试 1/3...
[2026-03-02 14:50:03] 找到图像 images/connect_button.png 在位置: (x, y)
[2026-03-02 14:50:03] 点击坐标: (x, y)
[2026-03-02 14:50:03] ✅ 成功点击连接按钮
[2026-03-02 14:50:05] ✅ VPN 连接已触发
[2026-03-02 14:50:05] 请在手机上完成 MFA 认证
```

## 安装监控服务

测试成功后，安装监控服务：

```bash
cd /home/tsl/openclaw/vpn-auto
./install-monitor.sh
```

按提示操作，选择立即启动服务。

## 验证服务运行

```bash
# 查看服务状态
sudo systemctl status vpn-monitor

# 查看实时日志
journalctl -u vpn-monitor -f

# 查看文件日志
tail -f /home/tsl/openclaw/vpn-auto/monitor.log
```

## 故障排查

### 问题 1：找不到按钮图像

**症状**：

```
[2026-03-02 14:50:02] 未找到图像: images/connect_button.png
[2026-03-02 14:50:02] ❌ 未能找到连接按钮
```

**解决方案**：

1. 检查图像文件是否存在：

   ```bash
   ls -lh vpn-auto/images/connect_button.png
   ```

2. 查看调试截图，确认按钮可见：

   ```bash
   eog vpn-auto/debug_screen.png
   ```

3. 重新捕获按钮图像，确保：
   - FortiClient 窗口完全可见
   - 按钮未被遮挡
   - 截图区域准确

4. 降低匹配置信度（编辑 `gui-auto-connect.py`）：
   ```python
   CONFIDENCE = 0.7  # 从 0.8 降低到 0.7
   ```

### 问题 2：X11 权限错误

**症状**：

```
Can't connect to display ":1"
```

**解决方案**：

```bash
export DISPLAY=:1
xhost +SI:localuser:tsl
```

### 问题 3：FortiClient 未运行

**症状**：

```
[2026-03-02 14:50:00] ❌ FortiClient GUI 启动失败
```

**解决方案**：

```bash
# 手动启动 FortiClient
/opt/forticlient/fortitray &

# 等待 3 秒
sleep 3

# 再次测试
python3 gui-auto-connect.py
```

## 按钮图像要求

### 最佳实践

1. **图像大小**：
   - 宽度：50-200 像素
   - 高度：30-80 像素
   - 越小越快，但要包含完整按钮

2. **图像内容**：
   - 只包含按钮本身
   - 不要包含过多背景
   - 确保文字清晰可见

3. **多状态支持**：
   如果按钮在不同状态下外观不同，可以捕获多个图像：
   - `connect_button.png` - 默认状态
   - `connect_button_hover.png` - 鼠标悬停状态
   - `connect_button_zh.png` - 中文界面

### 示例按钮图像

FortiClient 连接按钮通常包含：

- 文字："Connect" 或 "连接"
- 图标：VPN 图标或箭头
- 颜色：蓝色或绿色背景

## 完成配置后

配置完成后，系统将：

1. **自动监控 VPN 状态**（每 60 秒）
2. **检测到断开时**：
   - 启动 FortiClient GUI（如果未运行）
   - 使用图像识别查找连接按钮
   - 自动点击连接按钮
   - 发送飞书通知
3. **等待 MFA 认证**（用户在手机上完成）
4. **VPN 连接成功**

## 总结

当前进度：

- ✅ 依赖安装完成
- ✅ X11 权限配置完成
- ✅ FortiClient 运行中
- ⏸️ 需要捕获连接按钮图像
- ⏸️ 需要测试 GUI 自动化
- ⏸️ 需要安装监控服务

下一步：按照上述方法捕获连接按钮图像，然后测试和安装服务。

---

**创建时间**: 2026-03-02 14:50  
**状态**: 依赖已安装，等待捕获按钮图像
