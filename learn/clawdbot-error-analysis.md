# Clawdbot 错误分析报告

## 🔴 错误信息

```
Gateway agent failed; falling back to embedded: Error: Error: Missing workspace template: AGENTS.md (/home/tsl/docs/reference/templates/AGENTS.md). Ensure docs/reference/templates are packaged.
```

## 🔍 根本原因分析

### 1. **Gateway 服务启动失败** ⚠️ 主要问题

**核心问题**: 旧的 Gateway 进程 (PID 97715) 仍在占用端口 18789，导致新的 Gateway 无法启动。

**日志证据**:
```
Gateway failed to start: another gateway instance is already listening on ws://127.0.0.1:18789
Port 18789 is already in use.
- pid 97715 tsl: openclaw-gateway (127.0.0.1:18789)
Runtime: stopped (state activating, sub auto-restart, last exit 1, reason 1)
```

**结果**: 
- Gateway 模式失败
- Fallback 到 embedded 模式
- Embedded 模式也失败（模板路径问题）

### 2. **路径解析错误** ⚠️ 次要问题

**问题**: Clawdbot 在 embedded 模式下尝试从 **当前工作目录** 加载模板文件，而不是从安装目录。

**代码逻辑** (`src/agents/workspace.ts:31-34`):
```typescript
const TEMPLATE_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../docs/reference/templates",
);
```

这个路径是相对于 **编译后的 JS 文件位置** 计算的：
- 开发环境: `src/agents/workspace.ts` → `../../docs/reference/templates` ✅
- 全局安装: `/usr/lib/node_modules/clawdbot/dist/agents/workspace.js` → `../../docs/reference/templates` ✅
- **当前目录运行**: `/home/tsl/openclaw` → 尝试访问 `/home/tsl/docs/reference/templates/` ❌

### 2. **为什么会 fallback 到 embedded 模式？**

从错误信息看，有两个阶段的失败：

**阶段 1**: Gateway agent 失败
```
Gateway agent failed; falling back to embedded
```

**阶段 2**: Embedded 模式也失败
```
Error: Missing workspace template: AGENTS.md (/home/tsl/docs/reference/templates/AGENTS.md)
```

### 3. **实际文件位置**

✅ **模板文件存在于**:
- 源码目录: `/home/tsl/openclaw/docs/reference/templates/AGENTS.md`
- 全局安装: `/usr/lib/node_modules/clawdbot/docs/reference/templates/AGENTS.md`

✅ **工作空间文件存在于**:
- `~/clawd/AGENTS.md` (已创建)
- `~/clawd/SOUL.md`
- `~/clawd/TOOLS.md`
- 等等...

❌ **错误路径** (不存在):
- `/home/tsl/docs/reference/templates/AGENTS.md`

## 📊 测试结果对比

### 测试 1: 直接使用 Ollama ✅
```bash
time ollama run qwen2.5:3b "什么是 MSTP 协议？请用一句话简要回答。"
```
**结果**: 
- 响应时间: **8.762 秒**
- 状态: **成功**
- 回答: "MSTP（多生成树协议）是一种在以太网交换机中实现冗余和负载均衡的网络管理技术。"

### 测试 2: 使用 Clawdbot ❌
```bash
time clawdbot agent --agent main --message "什么是 MSTP 协议？请用一句话简要回答。" --thinking low
```
**结果**:
- 响应时间: **超时 (>90秒)**
- 状态: **失败**
- 错误: Gateway 失败 → embedded 模式失败 → 模板文件缺失

## 💡 解决方案

### 方案 1: 杀死旧的 Gateway 进程并重启 ⭐⭐⭐ (推荐)

```bash
# 杀死旧进程
kill -9 97715

# 或者使用 pkill
pkill -9 -f "openclaw-gateway"

# 重启 Gateway 服务
clawdbot gateway stop
clawdbot gateway start

# 验证状态
clawdbot gateway status
```

**原理**: 清除占用端口的旧进程，让新的 Gateway 正常启动。

### 方案 2: 在正确的目录运行 ⭐⭐

```bash
# 切换到 clawd 工作空间目录
cd ~/clawd

# 然后运行 clawdbot
clawdbot agent --agent main --message "你的问题" --thinking low
```

**原理**: 在工作空间目录运行时，Clawdbot 会优先使用本地的 AGENTS.md 文件。

### 方案 2: 使用 Gateway 模式 (需要先启动 Gateway)

```bash
# 确保 Gateway 正在运行
clawdbot gateway status

# 如果没运行，启动它
clawdbot gateway start

# 然后使用 agent 命令
clawdbot agent --agent main --message "你的问题"
```

**原理**: Gateway 模式不依赖当前工作目录的模板文件。

### 方案 3: 使用 TUI 模式 ⭐⭐ (交互式)

```bash
clawdbot tui
```

**原理**: TUI 模式有不同的初始化路径，可能不会触发这个错误。

### 方案 4: 创建符号链接 (临时解决)

```bash
# 在当前目录创建 docs 目录结构
mkdir -p /home/tsl/docs/reference
ln -s /usr/lib/node_modules/clawdbot/docs/reference/templates /home/tsl/docs/reference/templates
```

**警告**: 这只是临时解决方案，不推荐。

### 方案 5: 直接使用 Ollama (最简单) ⭐⭐⭐

```bash
# 对于简单查询，直接使用 Ollama
ollama run qwen2.5:3b "你的问题"
```

**优点**: 
- 速度快 (8.7秒 vs >90秒)
- 无需额外配置
- 内存占用低

## 🎯 推荐使用方式

### 场景 1: 快速查询 (推荐)
```bash
ollama run qwen2.5:3b "你的问题"
```
**性能**: ⭐⭐⭐⭐⭐ (8.7秒)

### 场景 2: 需要 Clawdbot 功能
```bash
# 方法 A: 在工作空间目录运行
cd ~/clawd
clawdbot agent --agent main --message "你的问题" --thinking low

# 方法 B: 使用 TUI
clawdbot tui
```
**性能**: ⭐⭐ (待测试，预计 >30秒)

### 场景 3: 交互式对话
```bash
clawdbot tui
```
**性能**: ⭐⭐⭐ (保持上下文)

## 📝 总结

**核心问题**: 
1. Gateway 模式失败（原因未知）
2. Fallback 到 embedded 模式时，从错误的路径加载模板文件
3. 系统内存不足 (7.6GB) 导致性能问题

**最佳实践**:
- ✅ 简单查询: 直接使用 `ollama run qwen2.5:3b`
- ✅ 需要 Clawdbot: 在 `~/clawd` 目录运行或使用 `clawdbot tui`
- ❌ 避免: 在非工作空间目录使用 `clawdbot agent` 命令

**性能对比**:
- Ollama 直接调用: **8.7秒** ⚡
- Clawdbot (当前): **超时** 🐌
- 性能差距: **>10倍**

**建议**: 
1. 短期: 使用 Ollama CLI 进行查询
2. 中期: 在 ~/clawd 目录测试 Clawdbot
3. 长期: 升级内存到 16GB 以获得最佳体验
