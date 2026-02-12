# Cron Run Mode Fix

## 问题描述

用户尝试通过飞书消息"立即执行所有定时任务"时，遇到了以下问题：

1. Agent 尝试使用 `message` 工具发送消息来触发任务，而不是使用 `cron` 工具的 `run` 动作
2. 即使使用了 `cron run`，也会因为缺少 `mode` 参数而导致任务不会立即执行（只在到期时执行）
3. 发送消息时出现 400 错误：`invalid receive_id`

## 根本原因

### 1. Agent 行为问题
Agent 没有正确理解如何"立即执行"定时任务。它尝试发送消息而不是调用 `cron run`。

### 2. Cron Tool 缺少 runMode 参数
`cron-tool.ts` 的 `run` 动作没有支持 `mode` 参数，导致：
- 默认行为是只在任务到期时执行（`mode: "due"`）
- 无法强制立即执行任务（`mode: "force"`）

### 3. Gateway 实现
Gateway 的 `cron.run` 方法支持可选的 `mode` 参数：
- `mode: "due"` - 只在任务到期时执行（默认）
- `mode: "force"` - 强制立即执行，无论是否到期

但 cron-tool 没有暴露这个参数给 agent。

## 解决方案

### 1. 添加 runMode 参数支持

修改 `src/agents/tools/cron-tool.ts`：

```typescript
// 添加 CRON_RUN_MODES 常量
const CRON_RUN_MODES = ["due", "force"] as const;

// 更新 schema，添加 runMode 参数
const CronToolSchema = Type.Object({
  // ... 其他字段
  mode: Type.Optional(Type.String()),  // 用于 wake 动作
  runMode: optionalStringEnum(CRON_RUN_MODES),  // 用于 run 动作
  // ...
});

// 更新 run 动作实现
case "run": {
  const id = readStringParam(params, "jobId") ?? readStringParam(params, "id");
  if (!id) {
    throw new Error("jobId required (id accepted for backward compatibility)");
  }
  const runMode =
    params.runMode === "due" || params.runMode === "force" ? params.runMode : "force";
  return jsonResult(await callGatewayTool("cron.run", gatewayOpts, { id, mode: runMode }));
}
```

### 2. 更新工具描述

```typescript
description:
  "Manage Gateway cron jobs (status/list/add/update/remove/run/runs) and send wake events. " +
  "Use `jobId` as the canonical identifier; `id` is accepted for compatibility. " +
  "Use `contextMessages` (0-10) to add previous messages as context to the job text. " +
  "For `run` action, use `runMode: 'force'` to execute immediately or `runMode: 'due'` to only run if due (default: 'force').",
```

### 3. 更新文档

修改 `skills/cron/SKILL.md`：

```markdown
### run
Manually trigger a job (ignores schedule).

\`\`\`json
{
  "action": "run",
  "jobId": "job-id-here",
  "runMode": "force"  // "force" (default) = run immediately, "due" = only run if due
}
\`\`\`
```

## 技术细节

### 参数命名
- `mode` - 用于 `wake` 动作（值：`"now"` | `"next-heartbeat"`）
- `runMode` - 用于 `run` 动作（值：`"due"` | `"force"`）

分开命名避免了参数冲突，因为两个动作使用不同的枚举值。

### 默认行为
- 默认 `runMode: "force"` - 这样 agent 调用 `cron run` 时会立即执行任务
- 如果需要只在到期时执行，可以显式指定 `runMode: "due"`

### Gateway 实现
Gateway 的 `cron.run` 方法：
```typescript
async run(id: string, mode?: "due" | "force") {
  const due = isJobDue(job, now, { forced: mode === "force" });
  if (!due) return { ok: true, ran: false, reason: "not-due" };
  await executeJob(state, job, now, { forced: mode === "force" });
  return { ok: true, ran: true };
}
```

## 验证

1. 编译成功：`pnpm build`
2. Gateway 启动成功
3. Agent 现在可以使用 `cron run` 工具立即执行任务：
   ```json
   {
     "action": "run",
     "jobId": "bad3205a-ddab-4efe-9426-1703b9b757c4",
     "runMode": "force"
   }
   ```

## 影响

- Agent 现在可以正确地立即执行定时任务
- 向后兼容：如果不指定 `runMode`，默认为 `"force"`（立即执行）
- 文档已更新，说明如何使用新参数

## 相关文件

- `src/agents/tools/cron-tool.ts` - 添加 runMode 参数支持
- `skills/cron/SKILL.md` - 更新文档
- `src/gateway/server-methods/cron.ts` - Gateway 实现（未修改）
- `src/cron/service/ops.ts` - Cron service 实现（未修改）
