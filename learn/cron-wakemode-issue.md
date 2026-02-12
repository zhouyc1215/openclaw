# Cron WakeMode 问题分析

## 问题描述

用户手动触发定时任务后，任务显示"已成功触发"，但一直没有收到执行结果。

## 根本原因

### 1. WakeMode 机制

定时任务配置了 `wakeMode: "next-heartbeat"`：

```json
{
  "sessionTarget": "main",
  "wakeMode": "next-heartbeat",
  "payload": {
    "kind": "systemEvent",
    "text": "Get 3-day weather forecast for Xi'an"
  }
}
```

这意味着：
- 任务触发时，只是将事件加入队列
- 事件会在**下一个心跳**时才真正发送到主会话
- 心跳间隔是 **30分钟**（1800000ms）

### 2. 执行流程

1. **06:19:35** - 用户通过 `cron run` 触发任务
2. **06:19:35** - 任务被标记为"已执行"（`lastRunAtMs: 1770877175803`）
3. **等待中** - 系统事件在队列中等待下一个心跳
4. **06:39:06** - 下一个心跳触发（30分钟后）
5. **06:39:06** - 系统事件发送到主会话
6. **06:39:06+** - Agent 接收事件并执行实际工作
7. **06:39:06+** - 结果发送回飞书

### 3. 为什么 durationMs 是 0

```json
{
  "lastRunAtMs": 1770877175803,
  "lastStatus": "ok",
  "lastDurationMs": 0
}
```

`durationMs: 0` 表示：
- 任务触发成功（状态 ok）
- 但实际工作还没开始（等待心跳）
- 这是 `wakeMode: "next-heartbeat"` 的正常行为

## WakeMode 选项对比

### next-heartbeat（当前配置）
- **优点**：批量处理，减少系统负载
- **缺点**：延迟高（最多30分钟）
- **适用场景**：非紧急的定时任务

### now（推荐用于手动触发）
- **优点**：立即执行，无延迟
- **缺点**：每次触发都会立即唤醒 agent
- **适用场景**：手动触发、紧急任务

## 解决方案

### 方案 1：修改任务配置（推荐）

将 `wakeMode` 改为 `"now"`，这样手动触发时会立即执行：

```bash
clawdbot cron update \
  --id bad3205a-ddab-4efe-9426-1703b9b757c4 \
  --patch '{"wakeMode":"now"}'

clawdbot cron update \
  --id 440648af-dcab-4cc7-8086-45c0f87263c6 \
  --patch '{"wakeMode":"now"}'
```

### 方案 2：使用 isolated 会话

将任务改为 `sessionTarget: "isolated"`，这样任务会在独立会话中执行，不受心跳限制：

```json
{
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Get 3-day weather forecast for Xi'an",
    "deliver": true,
    "channel": "last"
  }
}
```

### 方案 3：等待下一个心跳

如果不修改配置，任务会在下一个心跳时自动执行（约30分钟后）。

## 最佳实践建议

### 1. 根据场景选择 wakeMode

- **定时任务（自动触发）**：使用 `"next-heartbeat"`
  - 例如：每天早上8点的天气预报
  - 不需要立即执行，可以等待心跳

- **手动触发任务**：使用 `"now"`
  - 例如：用户主动请求"立即执行任务"
  - 需要立即看到结果

### 2. 考虑使用 isolated 会话

对于耗时任务或需要立即反馈的任务：
- 使用 `sessionTarget: "isolated"`
- 设置 `deliver: true` 和 `channel: "last"`
- 这样任务会在独立会话中执行，结果会发送回原频道

### 3. 文档改进

在 `skills/cron/SKILL.md` 中添加关于 wakeMode 的说明：

```markdown
## WakeMode 说明

- **next-heartbeat**：事件在下一个心跳时发送（默认30分钟间隔）
  - 适用于定时任务
  - 批量处理，减少系统负载
  
- **now**：事件立即发送
  - 适用于手动触发
  - 立即执行，无延迟
```

## 相关代码

- `src/cron/service/ops.ts` - Cron 服务实现
- `src/gateway/heartbeat.ts` - 心跳机制
- `src/agents/tools/cron-tool.ts` - Cron 工具
- `skills/cron/SKILL.md` - Cron 文档

## 验证

修改配置后，再次手动触发任务：

```bash
# 修改 wakeMode
clawdbot cron update --id <job-id> --patch '{"wakeMode":"now"}'

# 手动触发
clawdbot cron run --id <job-id> --mode force

# 应该立即看到结果（几秒内）
```
