# OpenClaw 文档索引

本目录包含 OpenClaw 的完整文档和工具，帮助你快速上手和解决问题。

---

## 📖 核心文档

### 架构与技术

| 文档                                                   | 说明                  | 大小 |
| ------------------------------------------------------ | --------------------- | ---- |
| [OPENCLAW-ARCHITECTURE.md](./OPENCLAW-ARCHITECTURE.md) | OpenClaw 完整架构文档 | 26KB |
| [OPENCLAW-TECH-STACK.md](./OPENCLAW-TECH-STACK.md)     | 技术栈详解            | 17KB |

**适合人群：** 开发者、架构师、需要二次开发的用户

**内容包括：**

- 项目概述和核心架构
- 8 个核心模块详解
- 数据流与通信机制
- 扩展开发指南
- 技术栈选型和性能对比

---

## 🔧 配置指南

### Gateway 配置

| 文档                                                           | 说明                   | 大小  |
| -------------------------------------------------------------- | ---------------------- | ----- |
| [GATEWAY-LAN-ACCESS-SETUP.md](./GATEWAY-LAN-ACCESS-SETUP.md)   | Gateway 局域网访问配置 | 5.7KB |
| [CONTROL-UI-SETUP-COMPLETE.md](./CONTROL-UI-SETUP-COMPLETE.md) | Control UI 设置指南    | 7.5KB |

**适合人群：** 系统管理员、运维人员

**内容包括：**

- Gateway 配置步骤
- 局域网访问设置
- Control UI 构建和部署
- 验证和测试方法

---

## 🐛 问题修复

### WebSocket 连接问题

| 文档                                                         | 说明               | 大小  | 推荐度     |
| ------------------------------------------------------------ | ------------------ | ----- | ---------- |
| [QUICK-FIX-GUIDE.md](./QUICK-FIX-GUIDE.md)                   | 快速修复指南       | 4KB   | ⭐⭐⭐⭐⭐ |
| [WEBSOCKET-CONNECTION-FIX.md](./WEBSOCKET-CONNECTION-FIX.md) | 详细修复指南       | 4.4KB | ⭐⭐⭐⭐   |
| [WEBSOCKET-PROTOCOL-GUIDE.md](./WEBSOCKET-PROTOCOL-GUIDE.md) | WebSocket 协议详解 | 23KB  | ⭐⭐⭐     |

**适合人群：** 所有用户

**问题症状：**

- 错误信息：`disconnected (1008): invalid connect params`
- Control UI 页面可以打开但无法连接
- WebSocket 连接失败

**解决方案：**

1. 强制刷新（Ctrl + F5）
2. 清除浏览器缓存
3. 使用无痕模式
4. 使用 WebSocket 拦截器（高级）

---

## 🛠️ 工具

### 诊断工具

| 工具                                                                   | 说明                 | 类型       |
| ---------------------------------------------------------------------- | -------------------- | ---------- |
| [scripts/diagnose-websocket.sh](./scripts/diagnose-websocket.sh)       | WebSocket 诊断脚本   | Bash       |
| [tools/websocket-interceptor.js](./tools/websocket-interceptor.js)     | WebSocket 拦截器脚本 | JavaScript |
| [tools/websocket-interceptor.html](./tools/websocket-interceptor.html) | 拦截器可视化工具     | HTML       |

**使用方法：**

```bash
# 运行诊断脚本
bash scripts/diagnose-websocket.sh

# 在浏览器中打开拦截器工具
# 直接打开 tools/websocket-interceptor.html
```

---

## 📋 任务总结

| 文档                                 | 说明         | 大小  |
| ------------------------------------ | ------------ | ----- |
| [TASK-SUMMARY.md](./TASK-SUMMARY.md) | 完整任务总结 | 6.9KB |

**内容包括：**

- 任务概述和问题描述
- 已完成的工作清单
- 当前状态和解决方案
- 技术细节和后续建议

---

## 🚀 快速开始

### 新用户

1. 阅读 [OPENCLAW-ARCHITECTURE.md](./OPENCLAW-ARCHITECTURE.md) 了解系统架构
2. 按照 [GATEWAY-LAN-ACCESS-SETUP.md](./GATEWAY-LAN-ACCESS-SETUP.md) 配置 Gateway
3. 按照 [CONTROL-UI-SETUP-COMPLETE.md](./CONTROL-UI-SETUP-COMPLETE.md) 设置 Control UI

### 遇到 WebSocket 连接问题

1. 查看 [QUICK-FIX-GUIDE.md](./QUICK-FIX-GUIDE.md) 快速修复
2. 如果问题仍然存在，查看 [WEBSOCKET-CONNECTION-FIX.md](./WEBSOCKET-CONNECTION-FIX.md)
3. 运行诊断脚本：`bash scripts/diagnose-websocket.sh`
4. 如果需要深入了解，阅读 [WEBSOCKET-PROTOCOL-GUIDE.md](./WEBSOCKET-PROTOCOL-GUIDE.md)

### 开发者

1. 阅读 [OPENCLAW-ARCHITECTURE.md](./OPENCLAW-ARCHITECTURE.md) 了解架构
2. 阅读 [OPENCLAW-TECH-STACK.md](./OPENCLAW-TECH-STACK.md) 了解技术栈
3. 查看 [WEBSOCKET-PROTOCOL-GUIDE.md](./WEBSOCKET-PROTOCOL-GUIDE.md) 了解协议细节

---

## 📊 文档统计

| 类型     | 数量   | 总大小    |
| -------- | ------ | --------- |
| 核心文档 | 2      | 43KB      |
| 配置指南 | 2      | 13.2KB    |
| 问题修复 | 3      | 31.4KB    |
| 工具     | 3      | -         |
| 总结     | 1      | 6.9KB     |
| **总计** | **11** | **~95KB** |

---

## 🔗 相关链接

- **项目仓库：** https://github.com/openclaw/openclaw
- **官方文档：** https://docs.openclaw.ai/
- **问题反馈：** https://github.com/openclaw/openclaw/issues

---

## 📝 文档更新日志

### 2026-02-25

- ✅ 创建完整的架构文档
- ✅ 创建技术栈详解
- ✅ 创建 Gateway 配置指南
- ✅ 创建 Control UI 设置指南
- ✅ 创建 WebSocket 协议详解
- ✅ 创建 WebSocket 连接修复指南
- ✅ 创建快速修复指南
- ✅ 创建诊断工具
- ✅ 创建 WebSocket 拦截器工具
- ✅ 创建任务总结
- ✅ 创建文档索引

---

## 💡 使用建议

### 按角色查看

**系统管理员：**

1. GATEWAY-LAN-ACCESS-SETUP.md
2. CONTROL-UI-SETUP-COMPLETE.md
3. QUICK-FIX-GUIDE.md

**开发者：**

1. OPENCLAW-ARCHITECTURE.md
2. OPENCLAW-TECH-STACK.md
3. WEBSOCKET-PROTOCOL-GUIDE.md

**普通用户：**

1. QUICK-FIX-GUIDE.md
2. WEBSOCKET-CONNECTION-FIX.md

**调试人员：**

1. scripts/diagnose-websocket.sh
2. tools/websocket-interceptor.html
3. WEBSOCKET-PROTOCOL-GUIDE.md

### 按问题查看

**无法访问 Control UI：**
→ GATEWAY-LAN-ACCESS-SETUP.md

**WebSocket 连接失败：**
→ QUICK-FIX-GUIDE.md

**需要了解架构：**
→ OPENCLAW-ARCHITECTURE.md

**需要调试连接：**
→ tools/websocket-interceptor.html

---

**最后更新：** 2026-02-25  
**维护者：** OpenClaw Team
