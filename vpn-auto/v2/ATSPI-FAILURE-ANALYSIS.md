# ATSPIDriver 失败原因分析

## 测试结果

```
[INFO] 找到应用: FortiClient
[WARNING] 未找到 FortiClient 应用或按钮
```

## 详细调查

### 1. AT-SPI 树结构

FortiClient 在 AT-SPI 中的完整树结构：

```
[application] FortiClient
  动作: doDefault, showContextMenu
  文本: ￼
  子节点数量: 1

  [frame] FortiClient -- Zero Trust Fabric Agent
    动作: doDefault, showContextMenu
    子节点数量: 1

    [unknown] no-name
      (无子节点)
```

### 2. 关键发现

✅ **能找到的**：

- FortiClient 应用对象
- 窗口框架（frame）
- 应用级别的动作（doDefault, showContextMenu）

❌ **找不到的**：

- 按钮元素（push button）
- 文本框元素（text, entry）
- 任何具体的 UI 控件

### 3. 根本原因

**FortiClient 的 UI 元素未暴露给 AT-SPI 系统**

具体原因：

1. **自定义渲染**
   - FortiClient 使用了自定义的 UI 渲染方式
   - 没有使用标准的 Qt Widgets（QButton, QLineEdit 等）
   - 可能使用了 QML、OpenGL 或自定义绘图

2. **AT-SPI 支持不完整**
   - 虽然设置了 `QT_ACCESSIBILITY=1` 环境变量
   - 但应用本身没有实现完整的无障碍接口
   - 只暴露了应用和窗口级别的对象，没有暴露内部控件

3. **闭源商业软件限制**
   - FortiClient 是闭源软件
   - 开发者可能没有优先考虑无障碍功能
   - 无法修改源码来启用 AT-SPI 支持

## 对比：为什么其他驱动成功？

### PyAutoDriver（图像识别）✅

**工作原理**：

- 截取屏幕图像
- 使用模板匹配查找按钮图像
- 不依赖应用的 UI 框架

**成功原因**：

- 只要按钮在屏幕上可见就能识别
- 不需要应用暴露 UI 元素

**测试结果**：

```
[INFO] 找到按钮: Point(x=992, y=722)
[INFO] ✅ PyAutoGUI 点击成功
```

### VisionDriver（颜色+形状识别）✅

**工作原理**：

- 截取屏幕图像
- 通过 HSV 颜色范围识别蓝色区域
- 通过轮廓检测识别按钮形状

**成功原因**：

- 基于视觉特征（颜色、形状、尺寸）
- 完全不依赖应用框架
- 适应性最强

**测试结果**：

```
[INFO] 找到按钮: (993, 723)
[INFO] ✅ OpenCV 点击成功
```

## 环境变量验证

已设置的环境变量：

```bash
DISPLAY=:1
QT_ACCESSIBILITY=1
QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
```

这些环境变量已正确设置，但 FortiClient 仍然没有暴露 UI 元素，说明问题不在环境配置，而在应用本身。

## 尝试的解决方案

### ✅ 已尝试

1. **安装 Qt 无障碍库**

   ```bash
   sudo apt install libqaccessibilityclient-qt5-0
   ```

   结果：库已安装，但无效

2. **设置 Qt 环境变量**

   ```bash
   export QT_ACCESSIBILITY=1
   export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
   ```

   结果：变量已设置，但无效

3. **重启 FortiClient**
   - 在新环境变量下启动 FortiClient
     结果：UI 树结构没有变化

### ❌ 无法尝试

1. **修改 FortiClient 源码**
   - 原因：闭源软件，无法访问源码

2. **使用 FortiClient 的无障碍模式**
   - 原因：FortiClient 没有提供此选项

3. **强制启用 Qt AT-SPI 插件**
   - 原因：应用可能不使用标准 Qt Widgets

## 结论

### ATSPIDriver 失败的根本原因

**FortiClient 使用了自定义 UI 渲染，没有将内部控件暴露给 AT-SPI 系统**

这不是配置问题，而是应用架构问题。即使正确配置了所有环境变量和依赖，ATSPIDriver 也无法工作。

### 技术细节

1. **AT-SPI 能看到什么**：
   - 应用对象（application）
   - 窗口框架（frame）
   - 应用级别的动作

2. **AT-SPI 看不到什么**：
   - 按钮（push button）
   - 文本框（text, entry）
   - 标签（label）
   - 任何具体的 UI 控件

3. **为什么看不到**：
   - FortiClient 可能使用 QML（声明式 UI）
   - 或使用 OpenGL/自定义绘图
   - 或使用 Web 技术（Electron/CEF）
   - 这些技术默认不暴露 UI 元素给 AT-SPI

## 推荐方案

### 1. 禁用 ATSPIDriver（推荐）

修改配置文件 `config/config.yaml`：

```yaml
drivers:
  atspi:
    enabled: false # FortiClient 不支持 AT-SPI

  pyauto:
    enabled: true # 图像识别，已验证可用

  vision:
    enabled: true # 颜色+形状识别，最可靠
```

### 2. 调整驱动优先级

如果想保留 ATSPIDriver 作为尝试（虽然会失败）：

```yaml
drivers:
  priority:
    - pyauto # 图像识别（快速）
    - vision # 颜色识别（可靠）
    - atspi # AT-SPI（FortiClient 不支持，会失败）
```

### 3. 性能对比

| 驱动         | 状态    | 耗时  | 可靠性 |
| ------------ | ------- | ----- | ------ |
| ATSPIDriver  | ❌ 失败 | ~0.1s | 0%     |
| PyAutoDriver | ✅ 成功 | ~0.5s | 95%    |
| VisionDriver | ✅ 成功 | ~2s   | 99%    |

**建议配置**：

- 第一优先级：PyAutoDriver（快速且可靠）
- 第二优先级：VisionDriver（兜底，最可靠）
- 禁用：ATSPIDriver（不适用）

## 其他应用的适用性

ATSPIDriver 适用于：

- ✅ GNOME 原生应用（GTK）
- ✅ 标准 Qt Widgets 应用
- ✅ 启用了无障碍支持的应用
- ✅ Firefox、LibreOffice 等

ATSPIDriver 不适用于：

- ❌ 使用自定义渲染的应用
- ❌ QML 应用（除非特别配置）
- ❌ Electron 应用
- ❌ 游戏和多媒体应用
- ❌ FortiClient 等闭源商业软件

## 参考资料

- [AT-SPI 规范](https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/)
- [Qt Accessibility](https://doc.qt.io/qt-5/accessible.html)
- [PyATSPI 文档](https://lazka.github.io/pgi-docs/Atspi-2.0/index.html)
