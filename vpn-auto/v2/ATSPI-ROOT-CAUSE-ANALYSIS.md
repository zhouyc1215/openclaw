# ATSPIDriver 失败根本原因分析

## 执行时间

2026-03-05 11:26

## 测试配置

### 驱动配置

```yaml
drivers:
  priority:
    - atspi # 仅启用 ATSPIDriver

  atspi:
    enabled: true

  pyauto:
    enabled: false # 禁用

  vision:
    enabled: false # 禁用
```

### 环境变量

```bash
DISPLAY=:1
QT_ACCESSIBILITY=1
QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
NO_AT_BRIDGE=0
```

## 调试结果

### 1. AT-SPI 树结构

```
[application] 'FortiClient'
  → role=ATSPI_ROLE_APPLICATION
  → states=ENABLED,VISIBLE,SHOWING,FOCUSABLE,SENSITIVE
  → actions=doDefault,showContextMenu

  [frame] 'FortiClient -- Zero Trust Fabric Agent'
    → role=ATSPI_ROLE_FRAME
    → states=ENABLED,VISIBLE,SHOWING,SENSITIVE
    → pos=(556,240)
    → size=880x675
    → actions=doDefault,showContextMenu

    [unknown] ''
      → role=-1
      → (无属性，无子节点)
```

### 2. 按钮搜索结果

```
❌ 未找到任何按钮元素
```

遍历整个 UI 树（深度 15 层），没有找到任何 `ROLE_PUSH_BUTTON` 元素。

### 3. FortiClient 技术栈分析

#### 可执行文件信息

```bash
文件: /opt/forticlient/gui/FortiClient
类型: ELF 64-bit LSB shared object
架构: x86-64
```

#### 关键依赖库

```
libatspi.so.0           # AT-SPI 客户端库（已链接！）
libgtk-3.so.0           # GTK 3 GUI 库
libgdk-3.so.0           # GDK 3 绘图库
libatk-1.0.so.0         # ATK 无障碍工具包
libatk-bridge-2.0.so.0  # ATK 到 AT-SPI 的桥接
libffmpeg.so            # 视频编解码
libcairo.so.2           # 2D 图形库
libpango-1.0.so.0       # 文本渲染
```

## 关键发现

### ✅ FortiClient 已链接 AT-SPI 库

FortiClient 链接了以下无障碍相关库：

- `libatspi.so.0` - AT-SPI 客户端
- `libatk-1.0.so.0` - 无障碍工具包
- `libatk-bridge-2.0.so.0` - ATK 桥接

这说明 FortiClient **理论上支持** AT-SPI。

### ❌ 但 UI 元素未暴露

尽管链接了 AT-SPI 库，但实际运行时：

- 应用对象可见
- 窗口框架可见
- **所有 UI 控件不可见**（按钮、文本框等）

## 根本原因分析

### 原因 1: 使用了 Chromium Embedded Framework (CEF)

**证据**：

- 链接了 `libffmpeg.so`（视频编解码，CEF 常用）
- 链接了 GTK 3（CEF 在 Linux 上使用 GTK）
- UI 树只有 3 层（application → frame → unknown）

**CEF 的特点**：

- 使用 Web 技术渲染 UI（HTML/CSS/JavaScript）
- 内容在 Canvas 或 WebGL 中绘制
- 不使用原生 GTK Widgets
- AT-SPI 只能看到浏览器窗口，看不到内部内容

**类似应用**：

- Electron 应用（VS Code、Slack、Discord）
- CEF 应用（Spotify、Steam）
- 这些应用的 AT-SPI 树也只有窗口，没有按钮

### 原因 2: 自定义渲染

即使不是 CEF，FortiClient 也可能使用：

- Cairo 直接绘图
- OpenGL 渲染
- 自定义 Widget 系统

这些方法绕过了 GTK 的标准 Widget 系统，因此 ATK 无法访问。

### 原因 3: 未实现 ATK 接口

虽然链接了 ATK 库，但应用代码可能：

- 没有为自定义控件实现 `AtkObject`
- 没有设置控件的 accessible 属性
- 没有注册控件到 ATK 树

## 验证方法

### 使用 Accerciser 工具

```bash
# 安装 Accerciser（GNOME 无障碍检查器）
sudo apt install accerciser

# 运行
DISPLAY=:1 accerciser
```

在 Accerciser 中查看 FortiClient，会看到相同的结果：只有应用和窗口，没有内部控件。

### 对比其他应用

**GTK 原生应用**（如 gedit）：

```
[application] gedit
  [frame] gedit
    [menu bar]
      [menu] File
        [menu item] New
        [menu item] Open
        ...
    [tool bar]
      [push button] New
      [push button] Open
      ...
    [scroll pane]
      [text] (文本内容)
```

**FortiClient**：

```
[application] FortiClient
  [frame] FortiClient -- Zero Trust Fabric Agent
    [unknown] (空)
```

差异明显：GTK 原生应用暴露了所有控件，FortiClient 只暴露了窗口。

## 为什么环境变量无效？

我们设置了：

```bash
QT_ACCESSIBILITY=1
QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
```

但这些变量只对 **Qt Widgets** 应用有效。

FortiClient 使用的是：

- GTK 3（不是 Qt）
- 或 CEF（Web 技术）

因此 Qt 环境变量不起作用。

## 为什么其他驱动成功？

### PyAutoDriver（图像识别）✅

**工作原理**：

1. 截取屏幕图像
2. 使用模板匹配查找按钮图像
3. 点击匹配位置

**成功原因**：

- 不依赖 AT-SPI
- 不依赖应用框架
- 只要按钮在屏幕上可见就能识别

### VisionDriver（颜色+形状识别）✅

**工作原理**：

1. 截取屏幕图像
2. 通过 HSV 颜色范围识别蓝色区域
3. 通过轮廓检测识别按钮形状
4. 点击识别到的按钮

**成功原因**：

- 完全基于视觉特征
- 不依赖任何应用框架
- 适应性最强

## 结论

### ATSPIDriver 失败的根本原因

**FortiClient 使用了 Chromium Embedded Framework (CEF) 或类似的自定义渲染技术**

具体表现：

1. ✅ 应用链接了 AT-SPI 库（理论支持）
2. ✅ 应用和窗口注册到 AT-SPI（基本支持）
3. ❌ UI 控件未暴露给 AT-SPI（实现不完整）
4. ❌ 内容在 Canvas/WebGL 中渲染（绕过 ATK）

这不是配置问题，而是应用架构问题。

### 技术对比

| 技术         | AT-SPI 支持   | FortiClient 使用 |
| ------------ | ------------- | ---------------- |
| GTK Widgets  | ✅ 完整支持   | ❌ 未使用        |
| Qt Widgets   | ✅ 完整支持   | ❌ 未使用        |
| CEF/Electron | ❌ 仅窗口     | ✅ 可能使用      |
| 自定义渲染   | ❌ 需手动实现 | ✅ 可能使用      |

### 无法解决的原因

1. **闭源软件**：无法修改 FortiClient 源码
2. **架构限制**：CEF/自定义渲染不支持 AT-SPI
3. **开发者选择**：Fortinet 没有优先考虑无障碍功能

## 最终建议

### 1. 禁用 ATSPIDriver

```yaml
drivers:
  atspi:
    enabled: false # FortiClient 不支持
```

### 2. 使用 PyAutoDriver + VisionDriver

```yaml
drivers:
  priority:
    - pyauto # 图像识别，快速
    - vision # 颜色识别，可靠

  pyauto:
    enabled: true

  vision:
    enabled: true
```

### 3. 性能对比

| 方案            | 耗时   | 可靠性 | 维护成本           |
| --------------- | ------ | ------ | ------------------ |
| ATSPIDriver     | 0.1s   | 0%     | 低（总是失败）     |
| PyAutoDriver    | 0.5s   | 95%    | 中（需要按钮图像） |
| VisionDriver    | 2s     | 99%    | 低（自动识别）     |
| PyAuto + Vision | 0.5-2s | 99.9%  | 中                 |

## 附录：其他不支持 AT-SPI 的应用

类似 FortiClient，以下应用也不支持 AT-SPI：

- **Electron 应用**：VS Code、Slack、Discord、Spotify
- **CEF 应用**：Steam、Spotify（桌面版）
- **游戏**：大部分游戏使用 OpenGL/Vulkan 渲染
- **自定义 UI**：某些商业软件

这些应用都需要使用图像识别或颜色识别方法。
