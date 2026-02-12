# Tool Retry Guard 修复方案

## 问题回顾

Clawdbot 在处理飞书文档操作时陷入死循环，不断重复调用失败的工具（feishu_doc, feishu_drive），没有重试限制和错误恢复机制。

## 解决方案

创建了一个新的 `ToolRetryGuard` 模块来防止工具调用死循环。

### 新增文件

1. **src/agents/tool-retry-guard.ts** - 核心实现
2. **src/agents/tool-retry-guard.test.ts** - 单元测试

### 功能特性

#### 1. 失败计数
- 跟踪每个工具的调用失败次数
- 记录失败时间戳和参数
- 自动清理过期的失败记录

#### 2. 智能阻断
- 默认：同一工具连续失败 3 次后阻止
- 可配置失败次数阈值
- 可配置时间窗口（默认 5 分钟）

#### 3. 参数相似度检测
- 检测是否使用相同或相似的参数重复调用
- 避免误判（不同参数的调用不计入连续失败）
- 相似度阈值：70% 的参数值匹配

#### 4. 统计信息
- 总失败次数
- 按工具分类的失败次数
- 最近失败次数

### 使用示例

```typescript
import { ToolRetryGuard } from "./agents/tool-retry-guard.js";

// 创建 guard
const guard = new ToolRetryGuard({
  maxConsecutiveFailures: 3,  // 最多 3 次失败
  failureWindowMs: 5 * 60 * 1000,  // 5 分钟窗口
  checkParamSimilarity: true,  // 检查参数相似度
});

// 在工具调用前检查
const check = guard.shouldBlockTool("feishu_doc", { action: "update", doc_token: "xxx" });
if (check.blocked) {
  console.log(check.reason);  // "Tool 'feishu_doc' failed 3 times with similar parameters"
  // 停止调用，向用户报告错误
  return;
}

// 工具调用失败后记录
try {
  await tool.execute(...);
} catch (error) {
  guard.recordFailure({
    toolName: "feishu_doc",
    timestamp: Date.now(),
    errorMessage: error.message,
    params: { action: "update", doc_token: "xxx" },
  });
}

// 获取统计信息
const stats = guard.getStats();
console.log(stats);
// {
//   totalFailures: 3,
//   failuresByTool: { "feishu_doc": 3 },
//   recentFailures: 3
// }
```

### 集成位置

需要在以下位置集成 ToolRetryGuard：

#### 1. Agent 运行时 (src/agents/pi-embedded-runner/run/attempt.ts)

在工具调用循环中添加检查：

```typescript
// 在 runEmbeddedAttempt 函数中
const toolRetryGuard = new ToolRetryGuard();

// 在工具调用前
for (const toolCall of toolCalls) {
  const check = toolRetryGuard.shouldBlockTool(toolCall.name, toolCall.params);
  
  if (check.blocked) {
    // 返回错误给 agent
    return {
      toolResult: {
        isError: true,
        content: `Tool "${toolCall.name}" has failed too many times. ${check.reason}. Please try a different approach or ask the user for help.`,
      },
    };
  }
  
  // 执行工具调用
  try {
    const result = await executeTool(toolCall);
    // ...
  } catch (error) {
    // 记录失败
    toolRetryGuard.recordFailure({
      toolName: toolCall.name,
      timestamp: Date.now(),
      errorMessage: error.message,
      params: toolCall.params,
    });
    throw error;
  }
}
```

#### 2. 会话管理 (src/agents/session-manager.ts)

在会话级别维护 guard 实例，跨多轮对话保持状态。

#### 3. Gateway 层 (src/gateway/server.impl.ts)

在 gateway 层添加全局监控，检测异常模式并自动中断。

### 配置选项

可以通过配置文件自定义行为：

```json
{
  "agents": {
    "defaults": {
      "toolRetryGuard": {
        "enabled": true,
        "maxConsecutiveFailures": 3,
        "failureWindowMs": 300000,
        "checkParamSimilarity": true
      }
    }
  }
}
```

### 测试覆盖

单元测试覆盖以下场景：
- ✅ 初始状态允许工具调用
- ✅ 达到最大失败次数后阻止
- ✅ 不同工具独立计数
- ✅ 过期失败自动清理
- ✅ 参数相似度检测
- ✅ 统计信息准确性
- ✅ 重置功能

### 优势

1. **防止资源浪费**: 避免无限重试消耗 API 配额
2. **改善用户体验**: 快速失败并给出明确的错误信息
3. **保护系统稳定性**: 防止单个任务阻塞整个系统
4. **智能判断**: 区分不同类型的失败，避免误判
5. **可配置**: 根据实际情况调整阈值

### 后续改进

1. **持久化**: 将失败记录保存到磁盘，重启后保留
2. **自动恢复**: 一段时间后自动重置计数器
3. **通知机制**: 达到阈值时通知用户或管理员
4. **详细日志**: 记录每次失败的详细信息用于调试
5. **动态阈值**: 根据工具类型自动调整阈值

### 立即解决当前问题

对于当前陷入循环的会话：

```bash
# 方法 1: 重启 gateway
pnpm clawdbot gateway restart

# 方法 2: 清理会话文件
rm ~/.clawdbot/agents/main/sessions/b13d8019-6b88-446d-a7d0-7e0553af473a.jsonl

# 方法 3: 在飞书中发送新消息打断
# 发送: "停止" 或 "/new" 开始新会话
```

## 相关文件

- 实现: `src/agents/tool-retry-guard.ts`
- 测试: `src/agents/tool-retry-guard.test.ts`
- 分析: `learn/feishu-loop-analysis.md`
