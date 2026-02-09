# Clawdbot 性能分析报告

## 📊 问题描述

**现象**: 直接使用 Ollama 调用模型很快（~4.6秒），但通过 Clawdbot 调用就很卡顿（>60秒超时）

## 🔍 根本原因分析

### 1. **内存不足** ⚠️ 主要原因

你的系统配置：
- 总内存: 7.6GB
- 当前使用: 53.2%
- 可用内存: 3.2GB

内存需求分析：
- Ollama 模型 (qwen2.5:3b): ~2GB
- Clawdbot Gateway: ~300-500MB
- Agent Runner: ~300-500MB  
- 系统开销: ~1-2GB
- **总需求: ~4-5GB**

**结论**: 7.6GB 内存勉强够用，但没有足够的缓冲空间，导致频繁的内存交换（swap），严重影响性能。

### 2. **多层架构开销**

**直接调用 Ollama**:
```
用户 → Ollama API → 模型
层级: 2 层
延迟: 低 (~4.6秒)
```

**通过 Clawdbot 调用**:
```
用户 → Clawdbot CLI → Gateway → Agent Runner → Ollama API → 模型
层级: 5 层
延迟: 高 (>60秒)
```

每一层都增加了：
- 进程间通信开销
- 序列化/反序列化开销
- WebSocket 通信延迟
- 会话管理开销

### 3. **并发配置过高**

当前配置：
- `maxConcurrent: 4`
- `subagents.maxConcurrent: 8`

在低内存系统上，高并发设置会导致：
- 多个 Agent Runner 同时运行
- 内存竞争加剧
- CPU 上下文切换频繁

### 4. **CPU 资源竞争**

当前状态：
- Ollama runner: 426% CPU（正在处理其他任务）
- Clawdbot 进程: 196% CPU
- 总 CPU 使用: 超过 600%

在 6 核 CPU 上，这已经接近饱和。

### 5. **模板文件缺失**

错误信息：
```
Missing workspace template: AGENTS.md
```

这导致 Clawdbot fallback 到 embedded 模式，增加了额外的初始化开销。

## 💡 解决方案

### 立即可行的优化

#### 1. ✅ 已完成：降低并发设置

```json
{
  "agents": {
    "defaults": {
      "maxConcurrent": 1,
      "subagents": {
        "maxConcurrent": 1
      }
    }
  }
}
```

#### 2. ✅ 已完成：切换到更小的模型

- 从 qwen2.5:7b (4.7GB) 切换到 qwen2.5:3b (1.9GB)
- 节省约 2.8GB 内存

#### 3. 重启服务应用配置

```bash
# 停止所有 Clawdbot 进程
pkill -f clawdbot

# 重启网关
clawdbot gateway start
```

#### 4. 对于简单查询，直接使用 Ollama

```bash
# 快速查询（推荐）
ollama run qwen2.5:3b "你的问题"

# 或使用 Clawdbot TUI（交互式）
clawdbot tui
```

### 长期解决方案

#### 1. 升级内存到 16GB ⭐⭐⭐

这是最根本的解决方案，可以：
- 消除内存瓶颈
- 支持更大的模型
- 允许更高的并发设置
- 提升整体系统性能

#### 2. 使用 GPU 加速

如果有 NVIDIA GPU：
- 配置 CUDA 支持
- 大幅提升推理速度
- 减少 CPU 负载

#### 3. 使用更轻量的部署方式

考虑：
- 只运行 Ollama，不运行 Clawdbot Gateway
- 使用 Ollama CLI 或 API 直接调用
- 减少中间层开销

## 📈 性能对比

| 方法 | 延迟 | 内存占用 | CPU 占用 | 推荐度 |
|------|------|----------|----------|--------|
| Ollama CLI | ~4.6秒 | 低 (~2GB) | 中等 | ⭐⭐⭐ |
| Clawdbot (优化后) | 待测试 | 高 (~4-5GB) | 高 | ⭐⭐ |
| Clawdbot (优化前) | >60秒 | 很高 | 很高 | ❌ |

## 🎯 推荐使用方式

### 场景 1: 简单查询
```bash
ollama run qwen2.5:3b "你的问题"
```
**优点**: 快速、低开销、直接

### 场景 2: 交互式对话
```bash
clawdbot tui
```
**优点**: 保持上下文、支持工具调用

### 场景 3: 集成到工作流
使用 Ollama API:
```bash
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "qwen2.5:3b",
  "prompt": "你的问题",
  "stream": false
}'
```

## 📝 总结

**核心问题**: 7.6GB 内存不足以流畅运行 Clawdbot + Ollama 的完整架构

**已采取的措施**:
1. ✅ 切换到 qwen2.5:3b (节省 2.8GB)
2. ✅ 降低并发设置 (减少内存竞争)
3. ✅ 优化配置文件

**建议**:
- 短期：直接使用 Ollama CLI 进行查询
- 长期：升级内存到 16GB

**性能提升预期**:
- 优化后 Clawdbot 性能应该有所改善
- 但仍然会比直接调用 Ollama 慢（架构特性）
- 升级内存后可以获得最佳体验
