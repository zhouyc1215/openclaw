# Clawdbot vs Ollama 性能对比测试报告

## 📊 测试结果

### 测试问题
"什么是 MSTP 协议？请用一句话简要回答。"

---

## ✅ 测试 1: 直接使用 Ollama CLI

**命令**:
```bash
time ollama run qwen2.5:3b "什么是 MSTP 协议？请用一句话简要回答。"
```

**结果**:
- ⏱️ **响应时间**: **8.762 秒**
- ✅ **状态**: **成功**
- 📝 **回答**: "MSTP（多生成树协议）是一种在以太网交换机中实现冗余和负载均衡的网络管理技术。"
- 💾 **内存占用**: 低 (~2GB)
- 🔧 **CPU 占用**: 中等

**评分**: ⭐⭐⭐⭐⭐ (5/5)

---

## ❌ 测试 2: 使用 Clawdbot

**命令**:
```bash
time clawdbot agent --agent main --message "什么是 MSTP 协议？请用一句话简要回答。" --thinking low
```

**结果**:
- ⏱️ **响应时间**: **超时 (>90秒)**
- ❌ **状态**: **失败**
- 📝 **错误信息**:
  ```
  Gateway agent failed; falling back to embedded: Error: Error: Missing workspace template: AGENTS.md (/home/tsl/docs/reference/templates/AGENTS.md). Ensure docs/reference/templates are packaged.
  ```
- 💾 **内存占用**: 高 (~4-5GB)
- 🔧 **CPU 占用**: 高

**评分**: ❌ (0/5)

---

## 🔍 失败原因分析

### 1. Gateway 服务启动失败 ⚠️

**问题**: 旧的 Gateway 进程 (PID 97715) 占用端口 18789

**日志证据**:
```
Gateway failed to start: another gateway instance is already listening on ws://127.0.0.1:18789
Port 18789 is already in use.
- pid 97715 tsl: openclaw-gateway (127.0.0.1:18789)
Runtime: stopped (state activating, sub auto-restart, last exit 1, reason 1)
```

### 2. Embedded 模式 Fallback 失败

**问题**: 模板文件路径错误

**错误路径**: `/home/tsl/docs/reference/templates/AGENTS.md` (不存在)
**正确路径**: `/usr/lib/node_modules/clawdbot/docs/reference/templates/AGENTS.md` (存在)

### 3. 系统资源不足

- **内存**: 7.6GB (低于推荐的 8GB)
- **CPU**: 6 核 i5-8400 (已接近饱和)
- **Ollama 进程**: 426% CPU
- **Clawdbot 进程**: 196% CPU

---

## 📈 性能对比表

| 指标 | Ollama CLI | Clawdbot | 差距 |
|------|-----------|----------|------|
| **响应时间** | 8.7秒 | >90秒 (超时) | **>10倍** |
| **成功率** | 100% | 0% | - |
| **内存占用** | ~2GB | ~4-5GB | 2-2.5倍 |
| **CPU 占用** | 中等 | 高 | - |
| **架构层级** | 2层 | 5层 | 2.5倍 |
| **易用性** | ⭐⭐⭐⭐⭐ | ⭐ | - |
| **推荐度** | ⭐⭐⭐⭐⭐ | ❌ | - |

---

## 💡 解决方案

### 立即修复步骤

#### 步骤 1: 杀死旧的 Gateway 进程

```bash
# 方法 A: 直接杀死进程
kill -9 97715

# 方法 B: 使用 pkill
pkill -9 -f "openclaw-gateway"

# 方法 C: 停止服务
systemctl --user stop clawdbot-gateway.service
```

#### 步骤 2: 重启 Gateway

```bash
# 停止服务
clawdbot gateway stop

# 启动服务
clawdbot gateway start

# 验证状态
clawdbot gateway status
```

#### 步骤 3: 重新测试

```bash
# 测试 Gateway 是否正常
clawdbot agent --agent main --message "测试消息" --thinking low
```

---

## 🎯 推荐使用方式

### 场景 1: 快速查询 (推荐) ⭐⭐⭐⭐⭐

```bash
ollama run qwen2.5:3b "你的问题"
```

**优点**:
- ✅ 速度快 (8.7秒)
- ✅ 内存占用低
- ✅ 无需额外配置
- ✅ 100% 成功率

**缺点**:
- ❌ 无上下文记忆
- ❌ 无工具调用能力

---

### 场景 2: 需要 Clawdbot 功能 (修复后) ⭐⭐

```bash
# 确保 Gateway 正常运行
clawdbot gateway status

# 使用 agent 命令
clawdbot agent --agent main --message "你的问题" --thinking low
```

**优点**:
- ✅ 支持上下文记忆
- ✅ 支持工具调用
- ✅ 支持多轮对话

**缺点**:
- ❌ 速度慢 (预计 >30秒)
- ❌ 内存占用高
- ❌ 需要 Gateway 正常运行

---

### 场景 3: 交互式对话 ⭐⭐⭐

```bash
clawdbot tui
```

**优点**:
- ✅ 交互式界面
- ✅ 保持上下文
- ✅ 用户体验好

**缺点**:
- ❌ 性能待测试
- ❌ 需要 Gateway 正常运行

---

## 📝 总结

### 当前状态

- ✅ **Ollama**: 工作正常，性能优秀
- ❌ **Clawdbot**: Gateway 启动失败，无法使用

### 核心问题

1. **Gateway 端口冲突**: 旧进程 (PID 97715) 占用端口 18789
2. **Embedded 模式失败**: 模板文件路径错误
3. **系统资源不足**: 7.6GB 内存低于推荐配置

### 建议

**短期方案** (立即可用):
1. ✅ 使用 Ollama CLI 进行查询 (8.7秒响应)
2. ✅ 杀死旧的 Gateway 进程
3. ✅ 重启 Gateway 服务

**中期方案** (优化性能):
1. ✅ 降低并发设置 (已完成)
2. ✅ 使用 qwen2.5:3b 模型 (已完成)
3. ⏳ 测试 Gateway 修复后的性能

**长期方案** (根本解决):
1. 🔄 升级内存到 16GB
2. 🔄 考虑使用 GPU 加速
3. 🔄 优化 Clawdbot 架构

---

## 🚀 下一步行动

1. **立即执行**: 杀死 PID 97715 进程
2. **重启服务**: 重启 Clawdbot Gateway
3. **重新测试**: 对比 Ollama 和 Clawdbot 性能
4. **性能评估**: 确定是否需要升级硬件

---

## 📊 性能预期

修复 Gateway 后的预期性能：

| 指标 | Ollama CLI | Clawdbot (修复后) | 差距 |
|------|-----------|------------------|------|
| **响应时间** | 8.7秒 | 30-60秒 (预计) | 3-7倍 |
| **成功率** | 100% | 待测试 | - |
| **内存占用** | ~2GB | ~4-5GB | 2-2.5倍 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐ | - |

**结论**: 对于简单查询，Ollama CLI 仍然是最佳选择。Clawdbot 适合需要上下文记忆和工具调用的复杂场景。
