# 飞书消息处理流程分析

## 时间线：2026-02-08 14:21:44 - 14:26:45

## 完整处理流程

### 1. 消息接收阶段 (06:21:44.990)
```
feishu: received message from ou_b3afb7d2133e4d689be523fc48f3d2b3 in oc_acffe3c669016db989b35175a7889b4a (p2p)
```
- **触发点**: 用户在飞书中发送消息
- **消息类型**: P2P（点对点私聊）
- **用户ID**: `ou_b3afb7d2133e4d689be523fc48f3d2b3`
- **会话ID**: `oc_acffe3c669016db989b35175a7889b4a`

### 2. 消息分发阶段 (06:21:45.008)
```
feishu: dispatching to agent (session=agent:main:main)
```
- **分发目标**: 主 Agent (`agent:main:main`)
- **耗时**: 18ms（从接收到分发）

### 3. 用户反馈阶段 (06:21:45.484)
```
feishu: added typing indicator reaction
```
- **用户体验**: 在飞书中显示"正在输入"指示器
- **目的**: 让用户知道 Bot 正在处理消息

### 4. Agent 启动阶段 (06:21:45.515)
```
embedded run start: runId=43199dd9-ebc8-4d3d-977f-0b6a06be7b67 
sessionId=a562eea8-efca-4aeb-8c9b-e24266d84d1d 
provider=ollama 
model=qwen2.5:3b 
thinking=low 
messageChannel=feishu
```
- **运行ID**: `43199dd9-ebc8-4d3d-977f-0b6a06be7b67`（唯一标识这次执行）
- **会话ID**: `a562eea8-efca-4aeb-8c9b-e24266d84d1d`（持久化会话）
- **模型**: `ollama/qwen2.5:3b`
- **思考级别**: `low`（低延迟模式）
- **消息渠道**: `feishu`

### 5. Prompt 处理开始 (06:21:45.547)
```
embedded run prompt start: runId=43199dd9-ebc8-4d3d-977f-0b6a06be7b67
```
- **耗时**: 32ms（从 Agent 启动到 Prompt 开始）

### 6. Agent 会话创建 (06:21:45.551)
```
embedded run agent start: runId=43199dd9-ebc8-4d3d-977f-0b6a06be7b67
```
- **关键点**: 这里是之前出错的地方！
- **现在**: 成功创建 Agent 会话（因为模型定义中有 `input: ["text"]`）
- **耗时**: 4ms（会话创建）

### 7. 心跳保持阶段 (06:21:51 - 06:23:39)
```
feishu: added typing indicator reaction (每隔 6 秒)
```
- **目的**: 保持"正在输入"状态，让用户知道 Bot 还在工作
- **频率**: 约每 6 秒刷新一次
- **持续时间**: 约 2 分钟

### 8. 工具调用阶段

#### 8.1 Memory Search (06:24:03.303 - 06:24:03.621)
```
embedded run tool start: tool=memory_search toolCallId=call_sabh8lr2
embedded run tool end: tool=memory_search toolCallId=call_sabh8lr2
```
- **工具**: `memory_search`（搜索会话记忆）
- **耗时**: 318ms
- **目的**: 查找之前的对话上下文

#### 8.2 Web Search (06:26:17.710 - 06:26:17.714)
```
embedded run tool start: tool=web_search toolCallId=call_6xy8ddf7
embedded run tool end: tool=web_search toolCallId=call_6xy8ddf7
```
- **工具**: `web_search`（网络搜索）
- **耗时**: 4ms（可能是缓存或快速失败）
- **时间点**: 在 memory_search 之后 2 分 14 秒

### 9. 超时终止 (06:26:45.551)
```
embedded run timeout: runId=43199dd9-ebc8-4d3d-977f-0b6a06be7b67 
sessionId=a562eea8-efca-4aeb-8c9b-e24266d84d1d 
timeoutMs=300000
```
- **超时时间**: 300,000ms = 5 分钟
- **原因**: 配置的 `timeoutSeconds: 300`
- **状态**: Agent 被强制终止

### 10. 执行完成 (06:26:45.569)
```
embedded run prompt end: durationMs=300015
embedded run done: durationMs=300079 aborted=true
```
- **总耗时**: 300,079ms ≈ 5 分钟
- **状态**: `aborted=true`（因超时而中止）

### 11. 清理阶段 (06:26:45.579)
```
feishu: dispatch complete (queuedFinal=false, replies=0)
feishu: removed typing indicator reaction
```
- **回复数**: 0（因为超时，没有生成完整回复）
- **清理**: 移除"正在输入"指示器

## 关键时间节点

| 阶段 | 时间戳 | 相对时间 | 说明 |
|------|--------|----------|------|
| 消息接收 | 06:21:44.990 | 0s | 用户发送消息 |
| 消息分发 | 06:21:45.008 | +0.018s | 分发到 Agent |
| Agent 启动 | 06:21:45.515 | +0.525s | 开始处理 |
| Prompt 开始 | 06:21:45.547 | +0.557s | 准备调用 LLM |
| Agent 会话创建 | 06:21:45.551 | +0.561s | **之前失败的地方** |
| Memory Search | 06:24:03.303 | +2m18s | 第一个工具调用 |
| Web Search | 06:26:17.710 | +4m32s | 第二个工具调用 |
| 超时终止 | 06:26:45.551 | +5m0s | 达到超时限制 |
| 执行完成 | 06:26:45.575 | +5m0s | 清理资源 |

## 性能分析

### 1. 启动性能
- **消息接收到 Agent 启动**: 525ms
- **Agent 会话创建**: 4ms（非常快！）
- **总启动时间**: < 1 秒

### 2. LLM 响应时间
- **第一次 LLM 调用**: 约 2 分 18 秒（到 memory_search）
- **第二次 LLM 调用**: 约 2 分 14 秒（到 web_search）
- **总 LLM 时间**: 约 4 分 32 秒

### 3. 工具执行时间
- **memory_search**: 318ms
- **web_search**: 4ms
- **总工具时间**: 322ms

### 4. 超时配置
- **配置值**: 300 秒（5 分钟）
- **实际执行**: 300.079 秒
- **结果**: 因超时而中止，未生成完整回复

## 问题分析

### 为什么超时？

1. **LLM 响应慢**: qwen2.5:3b 在 CPU 上运行很慢
   - 第一次调用: 2 分 18 秒
   - 第二次调用: 2 分 14 秒
   - 总计: 4 分 32 秒

2. **多次工具调用**: Agent 需要多次与 LLM 交互
   - 初始理解 → memory_search
   - 搜索结果分析 → web_search
   - 最终回复生成 → **超时前未完成**

3. **超时设置**: 5 分钟对于 CPU 上的 3B 模型来说太短了

### 为什么之前失败？

**根本原因**: `qwen2.5:3b` 模型定义缺少 `input` 字段

```javascript
// 之前的状态
{
  id: "qwen2.5:3b",
  name: "Qwen 2.5 3B",
  // input 字段缺失！
}

// 修复后的状态
{
  id: "qwen2.5:3b",
  name: "Qwen 2.5 3B",
  input: ["text"],  // ✅ 添加了这个字段
}
```

**错误链**:
1. 配置文件中 `primary: "ollama/qwen2.5:3b"`
2. 但 `models` 数组中没有定义这个模型
3. 系统尝试加载模型，但没有 `input` 字段
4. 传递给 `createAgentSession` 时，`model.input` 为 `undefined`
5. 外部 SDK 调用 `model.input.includes("image")` 崩溃
6. 错误被捕获并作为 Assistant 消息返回

## 优化建议

### 1. 增加超时时间
```json
{
  "agents": {
    "defaults": {
      "timeoutSeconds": 600  // 从 300 增加到 600（10 分钟）
    }
  }
}
```

### 2. 使用更快的模型
- **当前**: qwen2.5:3b（CPU 上很慢）
- **建议**: qwen2.5:1.5b（更快，但质量稍低）
- **或者**: 使用 GPU 加速 Ollama

### 3. 减少工具调用
- 配置 Agent 减少不必要的工具调用
- 或者禁用某些工具（如 web_search）

### 4. 调整思考级别
```json
{
  "agents": {
    "defaults": {
      "thinkingDefault": "off"  // 从 "low" 改为 "off"
    }
  }
}
```

## 成功标志

✅ **Agent 会话创建成功**: 从 2-3ms 失败变为正常启动
✅ **模型定义完整**: `input: ["text"]` 字段存在
✅ **工具调用正常**: memory_search 和 web_search 都成功执行
✅ **没有错误消息**: 不再返回 "Cannot read properties of undefined"

## 当前状态

**问题**: Agent 因超时而中止，未生成完整回复
**原因**: qwen2.5:3b 在 CPU 上运行太慢，5 分钟不够
**解决方案**: 增加超时时间或使用更快的模型

## 总结

修复成功！问题从"立即崩溃"变为"正常运行但超时"。这是一个巨大的进步：

- **之前**: Agent 在 2-3ms 内崩溃，返回错误消息
- **现在**: Agent 正常运行 5 分钟，调用工具，只是因为模型太慢而超时

下一步需要优化性能配置，让 Agent 能在超时前完成回复。
