# Cron 任务创建失败循环分析

## 问题描述

Agent 在创建 cron 任务时反复失败，陷入循环试错过程。每次尝试都使用相同的无效参数，导致相同的验证错误。

## 错误模式

从会话日志中可以看到，Agent 反复尝试使用以下无效的 payload 结构：

```json
{
  "action": "add",
  "job": {
    "name": "...",
    "schedule": { "kind": "cron", "expr": "..." },
    "sessionTarget": "isolated",
    "wakeMode": "next-heartbeat",
    "payload": {
      "command": "...",      // ❌ 无效属性
      "atMs": 123456789,     // ❌ 无效属性
      "text": "...",         // ❌ 无效属性（对于 agentTurn）
      "kind": "invalid"      // ❌ 无效的 kind 值
    }
  }
}
```

## 验证错误信息

```
Validation errors:
- Unexpected property: 'command'
- Unexpected property: 'atMs'
- Unexpected property: 'text'
- Missing required property: 'message'
- Invalid 'kind' value
- Payload doesn't match any schema in anyOf
```

## 根本原因

### 1. Payload Schema 理解错误

根据 `src/gateway/protocol/schema/cron.ts` 和 `src/cron/types.ts`，cron payload 只有两种有效格式：

#### 格式 A: systemEvent (用于 main session)
```typescript
{
  kind: "systemEvent",
  text: string  // 必需，非空字符串
}
```

#### 格式 B: agentTurn (用于 isolated session)
```typescript
{
  kind: "agentTurn",
  message: string,           // 必需，非空字符串
  model?: string,            // 可选
  thinking?: string,         // 可选
  timeoutSeconds?: number,   // 可选
  deliver?: boolean,         // 可选
  channel?: string,          // 可选
  to?: string,              // 可选
  bestEffortDeliver?: boolean // 可选
}
```

### 2. SessionTarget 与 Payload Kind 的强制关系

从 `src/cron/service/jobs.ts` 可以看到严格的验证规则：

```typescript
export function assertSupportedJobSpec(job: Pick<CronJob, "sessionTarget" | "payload">) {
  if (job.sessionTarget === "main" && job.payload.kind !== "systemEvent") {
    throw new Error('main cron jobs require payload.kind="systemEvent"');
  }
  if (job.sessionTarget === "isolated" && job.payload.kind !== "agentTurn") {
    throw new Error('isolated cron jobs require payload.kind="agentTurn"');
  }
}
```

**关键规则：**
- `sessionTarget: "main"` → 必须使用 `payload.kind: "systemEvent"`
- `sessionTarget: "isolated"` → 必须使用 `payload.kind: "agentTurn"`

### 3. Agent 的错误理解

Agent 似乎混淆了以下概念：

1. **Schedule 的 kind** (at/every/cron) 与 **Payload 的 kind** (systemEvent/agentTurn)
2. **Schedule 的 atMs** 属性被错误地放到了 payload 中
3. 使用了不存在的 `command` 属性
4. 对于 `isolated` session，使用了 `text` 而不是 `message`

## 正确的使用示例

### 示例 1: Main Session 的系统事件提醒

```json
{
  "action": "add",
  "job": {
    "name": "Daily Weather Check",
    "enabled": true,
    "schedule": {
      "kind": "cron",
      "expr": "0 9 * * *",
      "tz": "Asia/Shanghai"
    },
    "sessionTarget": "main",
    "wakeMode": "next-heartbeat",
    "payload": {
      "kind": "systemEvent",
      "text": "Check today's weather forecast"
    }
  }
}
```

### 示例 2: Isolated Session 的独立任务

```json
{
  "action": "add",
  "job": {
    "name": "Hourly Status Report",
    "enabled": true,
    "schedule": {
      "kind": "every",
      "everyMs": 3600000
    },
    "sessionTarget": "isolated",
    "wakeMode": "now",
    "payload": {
      "kind": "agentTurn",
      "message": "Generate system status report",
      "deliver": true,
      "channel": "last"
    }
  }
}
```

### 示例 3: 一次性定时任务

```json
{
  "action": "add",
  "job": {
    "name": "One-time Reminder",
    "enabled": true,
    "deleteAfterRun": true,
    "schedule": {
      "kind": "at",
      "atMs": 1739347200000
    },
    "sessionTarget": "isolated",
    "wakeMode": "now",
    "payload": {
      "kind": "agentTurn",
      "message": "Meeting reminder: Team standup in 5 minutes"
    }
  }
}
```

## 循环问题的本质

这是 **ToolRetryGuard 需要解决的典型场景**：

1. Agent 使用错误的参数调用工具
2. 工具返回验证错误
3. Agent 没有正确理解错误信息
4. Agent 使用**完全相同**的错误参数重试
5. 重复步骤 2-4，形成无限循环

## 解决方案

### 短期修复（已实现但未集成）

使用 `ToolRetryGuard` 检测并阻止重复失败：

```typescript
// 在 src/agents/pi-embedded-runner/run/attempt.ts 中
const guard = session.toolRetryGuard;
const canProceed = guard.checkAndRecord(toolName, params, false);

if (!canProceed) {
  throw new Error(
    `Tool ${toolName} has failed ${guard.maxFailures} times with similar parameters. ` +
    `Please review the error messages and adjust your approach.`
  );
}
```

### 长期修复

1. **改进 Cron Tool 的错误消息**

在 `src/agents/tools/cron-tool.ts` 中添加更友好的错误提示：

```typescript
case "add": {
  if (!params.job || typeof params.job !== "object") {
    throw new Error(
      "job required. Example: { name: '...', schedule: { kind: 'cron', expr: '...' }, " +
      "sessionTarget: 'isolated', wakeMode: 'next-heartbeat', " +
      "payload: { kind: 'agentTurn', message: '...' } }"
    );
  }
  // ... 现有代码
}
```

2. **添加 Payload 验证提示**

在验证失败时，提供具体的修复建议：

```typescript
// 在 normalizeCronJobCreate 中
if (job.sessionTarget === "isolated" && job.payload?.kind !== "agentTurn") {
  throw new Error(
    'Isolated cron jobs require payload.kind="agentTurn" with a "message" field. ' +
    'Example: { kind: "agentTurn", message: "Your task description" }'
  );
}
```

3. **改进 Agent Prompt**

在 agent 的系统提示中添加 cron 工具使用指南：

```markdown
## Cron Tool Usage

When creating cron jobs, follow these rules:

1. For main session jobs (sessionTarget: "main"):
   - Use payload: { kind: "systemEvent", text: "..." }
   
2. For isolated session jobs (sessionTarget: "isolated"):
   - Use payload: { kind: "agentTurn", message: "..." }

3. Schedule types:
   - Cron expression: { kind: "cron", expr: "0 9 * * *", tz: "Asia/Shanghai" }
   - Interval: { kind: "every", everyMs: 3600000 }
   - One-time: { kind: "at", atMs: 1739347200000 }

4. Common mistakes to avoid:
   - Don't put "command", "atMs", or "text" in the payload for agentTurn
   - Don't confuse schedule.kind with payload.kind
   - Always use "message" (not "text") for agentTurn payloads
```

## 相关文件

- `src/gateway/protocol/schema/cron.ts` - Cron schema 定义
- `src/cron/types.ts` - Cron 类型定义
- `src/agents/tools/cron-tool.ts` - Cron 工具实现
- `src/cron/service/jobs.ts` - Cron 任务验证逻辑
- `src/agents/tool-retry-guard.ts` - 重试保护机制（待集成）

## 下一步行动

1. ✅ 分析完成 - 理解了 cron payload 的正确格式
2. ⏳ 集成 ToolRetryGuard 到 agent runtime
3. ⏳ 改进 cron tool 的错误消息
4. ⏳ 添加 cron 使用指南到 agent prompt 或 skill
5. ⏳ 创建 cron skill 文档，提供清晰的使用示例
