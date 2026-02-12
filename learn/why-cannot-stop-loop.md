# 为什么在循环中无法通过飞书命令停止任务？

## 问题描述

当 Agent 陷入工具调用循环（如反复创建 cron 任务失败）时，用户在飞书中发送"停止"、"取消"等命令，Agent 无法响应，继续执行循环。

## 根本原因

### 1. Agent 执行模型：单线程处理

从 `src/agents/pi-embedded-runner/runs.ts` 可以看到：

```typescript
const ACTIVE_EMBEDDED_RUNS = new Map<string, EmbeddedPiQueueHandle>();

export function queueEmbeddedPiMessage(sessionId: string, text: string): boolean {
  const handle = ACTIVE_EMBEDDED_RUNS.get(sessionId);
  if (!handle) {
    return false;  // 没有活动的运行
  }
  if (!handle.isStreaming()) {
    return false;  // 不在流式输出状态
  }
  if (handle.isCompacting()) {
    return false;  // 正在压缩会话
  }
  void handle.queueMessage(text);
  return true;
}
```

**关键点**：
- 每个 session 同时只能有一个活动的 agent run
- 新消息只能在特定状态下排队（streaming 且非 compacting）
- 如果 agent 正在执行工具调用，新消息无法被处理

### 2. 工具调用是同步阻塞的

Agent 的执行流程：

```
1. 收到用户消息
2. Agent 开始思考
3. Agent 决定调用工具（如 cron）
4. 执行工具调用 ← 阻塞在这里
5. 等待工具返回结果
6. Agent 处理结果
7. 决定下一步（可能再次调用工具）
8. 重复步骤 3-7
```

在步骤 4-6 期间：
- Agent 正在等待工具执行完成
- **不会检查新消息**
- 用户的"停止"命令被忽略或排队

### 3. 循环中的状态

当 Agent 陷入循环时：

```
循环开始
  ↓
调用 cron 工具 (阻塞)
  ↓
收到错误结果
  ↓
Agent 思考："我需要修正参数"
  ↓
再次调用 cron 工具 (阻塞) ← 用户发送"停止"
  ↓
收到相同错误
  ↓
Agent 思考："再试一次"
  ↓
继续循环...
```

用户的"停止"消息：
- 可能在工具调用期间到达 → 被忽略
- 可能在 Agent 思考期间到达 → 被排队，但 Agent 已经决定了下一步
- 无法中断当前的执行流程

### 4. 消息队列的限制

从代码可以看到，消息只能在以下条件下排队：

```typescript
if (!handle.isStreaming()) {
  return false;  // 不在流式输出状态
}
if (handle.isCompacting()) {
  return false;  // 正在压缩会话
}
```

在工具调用循环中：
- Agent 可能不在 streaming 状态
- 或者正在 compacting（压缩会话历史）
- 导致新消息无法排队

## 为什么其他场景可以中断？

### 场景 1: Agent 正在输出长文本

```
Agent 开始输出
  ↓
流式输出第 1 段
  ↓
流式输出第 2 段 ← 用户发送"停止"
  ↓
检查队列，发现新消息
  ↓
停止输出，处理新消息 ✓
```

这种情况下可以中断，因为：
- Agent 在 streaming 状态
- 每输出一段都会检查队列
- 可以及时响应新消息

### 场景 2: Agent 等待用户输入

```
Agent: "需要更多信息，请提供..."
  ↓
等待用户响应 ← 用户发送"停止"
  ↓
收到新消息
  ↓
处理"停止"命令 ✓
```

这种情况下可以中断，因为：
- Agent 已经完成当前 turn
- 处于空闲状态
- 可以立即处理新消息

## 为什么循环特别难以中断？

### 1. 工具调用频率高

```
工具调用 → 结果 → 思考 → 工具调用 → 结果 → 思考 → ...
   ↑                      ↑                      ↑
  阻塞                   阻塞                   阻塞
```

每次循环都有多个阻塞点，用户消息很难在合适的时机到达。

### 2. Agent 已经"决定"了下一步

即使用户消息被排队，Agent 在处理工具结果后：
- 已经生成了下一个工具调用
- 不会检查队列中的新消息
- 继续执行预定的操作

### 3. 上下文窗口被错误填满

循环 72 次后：
- 会话历史包含 72 次失败的工具调用
- 每次都有相同的错误消息
- Agent 的上下文被这些重复内容占满
- 即使收到"停止"消息，也可能被淹没在错误历史中

## 现有的中断机制

### 1. abort 功能

```typescript
export function abortEmbeddedPiRun(sessionId: string): boolean {
  const handle = ACTIVE_EMBEDDED_RUNS.get(sessionId);
  if (!handle) return false;
  handle.abort();
  return true;
}
```

但这个功能：
- 需要外部调用（不是通过用户消息）
- 可能没有暴露给用户
- 飞书消息无法触发这个 abort

### 2. 超时机制

Agent 执行有超时限制，但：
- 默认超时可能很长（几分钟到几十分钟）
- 每次工具调用都很快完成（即使失败）
- 不会触发超时

## 解决方案

### 短期方案：外部中断

**方法 1: 重启 Gateway**
```bash
pkill -9 -f "clawdbot.*gateway"
pnpm clawdbot gateway run --bind loopback --port 18789 --force
```

**方法 2: 使用 /new 命令**
```
在飞书中发送: /new
```
这会创建新会话，放弃当前循环。

**方法 3: 删除会话文件**
```bash
rm ~/.clawdbot/agents/main/sessions/<session-id>.jsonl
```

### 中期方案：改进消息处理

**1. 在工具调用前检查队列**

```typescript
// 在 src/agents/pi-embedded-runner/run/attempt.ts
async function executeToolCall(tool, params) {
  // 检查是否有新消息
  if (hasQueuedMessages()) {
    const newMessage = getNextQueuedMessage();
    if (isStopCommand(newMessage)) {
      throw new UserInterruptError("User requested stop");
    }
  }
  
  // 执行工具调用
  return await tool.execute(params);
}
```

**2. 添加特殊的中断命令**

```typescript
// 识别紧急中断命令
const INTERRUPT_COMMANDS = [
  "/stop",
  "/cancel", 
  "/abort",
  "停止",
  "取消",
  "中断"
];

function isInterruptCommand(text: string): boolean {
  const normalized = text.trim().toLowerCase();
  return INTERRUPT_COMMANDS.some(cmd => 
    normalized === cmd || normalized.startsWith(cmd + " ")
  );
}
```

**3. 在每次工具调用后检查**

```typescript
// 在工具调用循环中
for (const toolCall of toolCalls) {
  const result = await executeToolCall(toolCall);
  
  // 检查中断请求
  if (checkInterruptRequested()) {
    return {
      status: "interrupted",
      message: "Execution stopped by user request"
    };
  }
}
```

### 长期方案：ToolRetryGuard + 自动停止

**1. 集成 ToolRetryGuard**

```typescript
const guard = session.toolRetryGuard;

// 在工具调用前检查
if (!guard.checkAndRecord(toolName, params, false)) {
  // 自动停止循环
  return {
    status: "blocked",
    message: `Tool ${toolName} has failed too many times. Stopping execution.`
  };
}
```

**2. 添加循环检测提示**

当检测到循环时，自动向用户发送提示：

```typescript
if (guard.getConsecutiveFailures(toolName) >= 2) {
  await sendNotification({
    channel: "feishu",
    message: "检测到重复失败，可以发送 /stop 停止执行"
  });
}
```

**3. 自动停止阈值**

```typescript
const MAX_CONSECUTIVE_FAILURES = 3;

if (guard.getConsecutiveFailures(toolName) >= MAX_CONSECUTIVE_FAILURES) {
  // 自动停止，不需要用户干预
  throw new ToolRetryLimitError(
    `Tool ${toolName} failed ${MAX_CONSECUTIVE_FAILURES} times. ` +
    `Stopping execution to prevent infinite loop.`
  );
}
```

## 架构改进建议

### 1. 异步消息处理

将 Agent 执行改为事件驱动：

```typescript
class AgentExecutor {
  private messageQueue: Queue<Message>;
  private currentExecution: Promise<void> | null;
  
  async processMessage(message: Message) {
    // 高优先级消息（如中断命令）
    if (isInterruptCommand(message)) {
      this.interrupt();
      return;
    }
    
    // 普通消息排队
    this.messageQueue.enqueue(message);
  }
  
  private interrupt() {
    if (this.currentExecution) {
      this.currentExecution.abort();
    }
  }
}
```

### 2. 工具调用超时

为每个工具调用设置合理的超时：

```typescript
const result = await Promise.race([
  executeToolCall(tool, params),
  timeout(TOOL_TIMEOUT_MS),
  checkInterrupt()  // 定期检查中断请求
]);
```

### 3. 用户控制面板

提供 Web UI 或命令行工具：

```bash
# 查看活动的 agent 执行
clawdbot agent status

# 中断特定会话
clawdbot agent interrupt <session-id>

# 查看工具调用历史
clawdbot agent history <session-id> --last 10
```

## 总结

### 为什么无法停止？

1. **单线程执行** - Agent 同时只处理一个任务
2. **工具调用阻塞** - 在等待工具结果时不检查新消息
3. **消息队列限制** - 只在特定状态下接受新消息
4. **循环快速执行** - 没有合适的中断点

### 当前最佳实践

1. **预防循环** - 集成 ToolRetryGuard（最重要）
2. **改进错误消息** - 帮助 Agent 快速理解错误（已完成）
3. **外部中断** - 重启 Gateway 或使用 /new 命令
4. **监控告警** - 检测异常的工具调用频率

### 优先级

1. 🔴 **高优先级** - 集成 ToolRetryGuard（防止循环发生）
2. 🟡 **中优先级** - 添加中断命令检查（改进用户体验）
3. 🟢 **低优先级** - 架构重构（长期改进）

最有效的解决方案是**防止循环发生**，而不是依赖用户中断。ToolRetryGuard 应该是第一优先级。
