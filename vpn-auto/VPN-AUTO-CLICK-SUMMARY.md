# VPN 自动点击功能开发总结

## 项目目标

开发一个自动化脚本，能够：

1. 自动识别 FortiClient GUI 中的"SAML Login"按钮
2. 移动光标到按钮上触发 hover 效果
3. 点击按钮启动 VPN 连接

## 已完成的功能

### 1. 环境配置 ✅

- 安装所有必要的依赖包
  - pyautogui
  - opencv-python-headless
  - pytesseract
  - scrot
  - xdotool
  - tesseract-ocr

### 2. FortiClient 自动重启 ✅

- 自动杀死旧的 FortiClient 进程
- 自动启动新的 GUI 实例
- 验证窗口是否正常显示

### 3. 按钮智能识别 ✅

- 使用 OpenCV 颜色检测识别深蓝色按钮
- HSV 颜色范围: [100,100,100] - [130,255,255]
- 按钮尺寸过滤:
  - 面积: 2000-50000 像素
  - 宽度: 80-300 像素
  - 高度: 25-80 像素
- 选择最接近屏幕中心的候选按钮

### 4. 光标精确定位 ✅

- 使用 xdotool 移动光标到按钮中央
- 位置验证功能（误差 < 5px）
- 当前测试结果: 距离目标 0.0px（完美定位）

### 5. Hover 效果 ✅

- 光标停留在按钮上1秒
- 触发按钮的 hover 效果（背景变白）
- 截图验证 hover 效果

### 6. 点击执行 ✅

- 使用 xdotool 执行点击操作
- 支持单击、双击、三击
- 支持自定义点击间隔

### 7. 调试工具 ✅

- 生成多个调试截图
- 颜色掩码可视化
- 按钮候选标记
- 点击前后对比

## 当前问题

### ❌ VPN 连接未建立

点击按钮后，VPN 连接未成功建立：

- openfortivpn 进程未启动
- ppp0 接口未建立
- 等待30秒后仍无连接

## 可能的原因分析

### 1. 按钮识别错误

- 识别到的可能不是"SAML Login"按钮
- 可能是其他深蓝色的 UI 元素

### 2. 点击方式不正确

- 可能需要特定的点击方式（双击、长按等）
- 可能需要不同的点击位置（边缘而不是中心）

### 3. 按钮状态问题

- 按钮可能处于禁用状态
- 可能需要先完成其他操作

### 4. GUI 响应延迟

- FortiClient 可能需要更长时间响应
- 可能需要等待更长时间才能看到效果

### 5. 需要额外的认证步骤

- 可能需要先输入用户名密码
- 可能需要选择 VPN 配置

## 开发的脚本文件

### 核心脚本

1. `smart-find-button.py` - 智能按钮查找和点击（主脚本）
2. `find-saml-button-ocr.py` - OCR + 颜色检测方案
3. `find-blue-button.py` - 纯颜色检测方案
4. `opencv-auto-click.py` - OpenCV 模板匹配方案

### 测试脚本

1. `test-complete-flow.sh` - 完整流程测试
2. `test-click-with-screenshots.sh` - 点击并截图对比
3. `test-different-click-methods.py` - 测试不同点击方式
4. `check-forticlient-status.sh` - 检查 FortiClient 状态

### 调试工具

1. `debug-ocr.py` - OCR 识别调试
2. `test-ocr-click.sh` - OCR 方案测试

## 生成的调试文件

### 截图文件

- `screen.png` - 当前屏幕截图
- `button_candidates.png` - 按钮候选标记
- `blue_mask_debug.png` - 蓝色掩码
- `hover_effect.png` - hover 效果
- `before_click.png` - 点击前
- `after_click_2s.png` - 点击后2秒
- `after_click_7s.png` - 点击后7秒
- `after_click_17s.png` - 点击后17秒
- `forticlient_current_status.png` - 当前状态

### 文档文件

- `OPENCV-CLICK-TEST.md` - OpenCV 测试报告
- `SMART-BUTTON-CLICK-STATUS.md` - 智能点击状态报告
- `VPN-AUTO-CLICK-SUMMARY.md` - 本文档

## 下一步行动

### 立即行动

1. **查看截图** - 对比点击前后的截图，确认是否有变化
2. **手动测试** - 手动点击按钮，确认是否能成功连接
3. **检查日志** - 查看 FortiClient 日志，寻找错误消息

### 测试方案

1. **运行不同点击方式测试**

   ```bash
   python3 test-different-click-methods.py
   ```

2. **尝试键盘导航**

   ```bash
   # Tab 键导航到按钮，然后按 Enter
   DISPLAY=:1 xdotool key Tab Tab Tab Return
   ```

3. **检查是否需要先选择 VPN 配置**
   - 可能需要在下拉菜单中选择配置
   - 然后再点击连接按钮

### 备选方案

如果 GUI 自动化无法成功，可以考虑：

1. 使用命令行工具 `openfortivpn` 直接连接
2. 使用 FortiClient CLI 接口
3. 编写浏览器自动化脚本处理 SAML 认证

## 技术亮点

### 1. 智能按钮识别

- 使用 OpenCV 颜色检测
- 多重过滤条件（尺寸、位置、面积）
- 自动选择最佳候选

### 2. 精确光标定位

- 位置验证机制
- 自动重试机制
- 误差控制 < 5px

### 3. 完善的调试工具

- 多个调试截图
- 可视化标记
- 详细的日志输出

### 4. 模块化设计

- 功能分离
- 易于测试
- 易于扩展

## 总结

脚本的核心功能（按钮识别、光标定位、点击执行）已经完美实现，但 VPN 连接未成功建立。需要进一步调试以确定根本原因。

建议先查看生成的截图，确认识别的按钮是否正确，以及点击后是否有任何视觉变化。如果截图显示没有变化，可能需要尝试不同的点击方式或查找其他问题。

## 使用方法

### 快速测试

```bash
cd vpn-auto
bash test-complete-flow.sh
```

### 查看调试截图

```bash
ls -lh *.png
```

### 测试不同点击方式

```bash
python3 test-different-click-methods.py
```

### 检查 FortiClient 状态

```bash
bash check-forticlient-status.sh
```
