# 飞书定时任务结果通知修复

## 问题描述

定时任务执行成功，但飞书没有收到任务结果通知。

## 根本原因

在 `src/agents/subagent-announce.ts` 中，有两处硬编码的 60 秒超时：

1. **第 132 行** - `sendAnnounce` 函数中的 `callGateway` 调用
2. **第 539 行** - `runSubagentAnnounceFlow` 函数中的 `callGateway` 调用

定时任务流程：

- 定时任务在 `isolated` 模式下运行，创建一个子代理（subagent）
- 任务完成后，子代理需要通过 `runSubagentAnnounceFlow` 将结果通知主代理
- 主代理再将结果发送到飞书

问题在于：

- 虽然任务级别的 `timeoutSeconds` 已经配置（120-240 秒）
- 但 `runSubagentAnnounceFlow` 内部的 `callGateway` 调用仍然使用硬编码的 60 秒超时
- 当任务执行时间超过 60 秒时，announce 流程超时，结果无法送达飞书

## 修复方案

### 1. 修改 `sendAnnounce` 函数

```typescript
// 修改前
async function sendAnnounce(item: AnnounceQueueItem) {
  // ...
  await callGateway({
    // ...
    timeoutMs: 60_000, // 硬编码
  });
}

// 修改后
async function sendAnnounce(item: AnnounceQueueItem, timeoutMs = 60_000) {
  // ...
  await callGateway({
    // ...
    timeoutMs, // 使用参数
  });
}
```

### 2. 修改 `maybeQueueSubagentAnnounce` 函数

```typescript
// 添加 timeoutMs 参数
async function maybeQueueSubagentAnnounce(params: {
  requesterSessionKey: string;
  triggerMessage: string;
  summaryLine?: string;
  requesterOrigin?: DeliveryContext;
  timeoutMs?: number; // 新增
}): Promise<"steered" | "queued" | "none"> {
  // ...
  const timeoutMs = params.timeoutMs ?? 60_000;
  enqueueAnnounce({
    // ...
    send: (item) => sendAnnounce(item, timeoutMs), // 传递 timeout
  });
  // ...
}
```

### 3. 修改 `runSubagentAnnounceFlow` 函数

```typescript
// 修改前
await callGateway({
  // ...
  timeoutMs: 60_000, // 硬编码
});

// 修改后
await callGateway({
  // ...
  timeoutMs: params.timeoutMs, // 使用参数
});

// 调用 maybeQueueSubagentAnnounce 时传递 timeout
const queued = await maybeQueueSubagentAnnounce({
  requesterSessionKey: params.requesterSessionKey,
  triggerMessage,
  summaryLine: taskLabel,
  requesterOrigin,
  timeoutMs: params.timeoutMs, // 传递 timeout
});
```

## 数据流

```
定时任务配置 (jobs.json)
  └─> timeoutSeconds: 120-240
       └─> runCronIsolatedAgentTurn
            └─> timeoutMs = resolveAgentTimeoutMs(...)
                 └─> runSubagentAnnounceFlow({ timeoutMs })
                      ├─> maybeQueueSubagentAnnounce({ timeoutMs })
                      │    └─> sendAnnounce(item, timeoutMs)
                      │         └─> callGateway({ timeoutMs })  ✅ 现在使用配置的超时
                      └─> callGateway({ timeoutMs })  ✅ 现在使用配置的超时
```

## 测试验证

修复后，定时任务的 announce 流程将使用任务配置的超时时间，而不是硬编码的 60 秒：

- `get_top_ai_projects`: 120 秒
- `get_xian_weather_forecast`: 180 秒
- `auto-commit-openclaw`: 180 秒
- `backup_cron_results`: 240 秒

这样即使任务执行时间较长，announce 流程也有足够的时间完成，飞书将能够收到任务结果通知。

## 相关文件

- `src/agents/subagent-announce.ts` - 修复 announce 超时问题
- `src/cron/isolated-agent/run.ts` - 调用 runSubagentAnnounceFlow 并传递 timeoutMs
- `~/.openclaw/cron/jobs.json` - 定时任务配置（包含 timeoutSeconds）

## 下一步

1. 重启 Gateway
2. 等待下一次定时任务执行
3. 验证飞书是否收到任务结果通知
