# Cron Empty Heartbeat 问题

## 问题描述

修改 `wakeMode` 为 `"now"` 后，手动触发任务仍然没有执行结果。检查执行历史发现任务被跳过，错误信息为 `"empty-heartbeat-file"`。

## 执行历史

```json
{
  "ts": 1770877848906,
  "jobId": "bad3205a-ddab-4efe-9426-1703b9b757c4",
  "action": "finished",
  "status": "skipped",
  "error": "empty-heartbeat-file",
  "summary": "Get 3-day weather forecast for Xi'an",
  "runAtMs": 1770877848905,
  "durationMs": 0
}
```

## 根本原因

### 什么是 Heartbeat File？

Heartbeat 文件记录了当前活跃的会话和频道信息。当 cron 任务需要发送 `systemEvent` 到主会话时，它会：

1. 读取 heartbeat 文件
2. 找到主会话的目标频道
3. 将事件发送到该频道

### 为什么是 Empty？

可能的原因：
1. **没有活跃的用户会话** - 用户没有通过任何频道与 agent 交互
2. **Heartbeat 文件过期** - 文件内容已过期或被清空
3. **会话状态不同步** - 主会话没有关联的活跃频道

### WakeMode 的影响

- `wakeMode: "next-heartbeat"` - 等待下一个心跳周期，此时会有活跃会话
- `wakeMode: "now"` - 立即执行，但如果没有活跃会话，会被跳过

## 解决方案

### 方案 1：使用 Isolated 会话（推荐）

将任务改为在独立会话中执行，并指定结果发送到特定频道：

```bash
# 获取飞书 chat ID
# 在飞书中发送消息给 bot，从日志中找到 chat ID

# 修改任务配置
clawdbot cron edit bad3205a-ddab-4efe-9426-1703b9b757c4 \
  --session isolated \
  --message "Get 3-day weather forecast for Xi'an" \
  --deliver \
  --to "oc_acffe3c669016db989b35175a7889b4a"  # 飞书 chat ID
```

完整配置示例：

```json
{
  "name": "get_xian_weather_forecast",
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Get 3-day weather forecast for Xi'an",
    "deliver": true,
    "channel": "feishu",
    "to": "oc_acffe3c669016db989b35175a7889b4a"
  }
}
```

### 方案 2：保持 Main 会话 + next-heartbeat

如果必须使用主会话，保持 `wakeMode: "next-heartbeat"`：

```bash
clawdbot cron edit bad3205a-ddab-4efe-9426-1703b9b757c4 \
  --wake next-heartbeat
```

这样任务会在下一个心跳时执行，此时通常会有活跃会话。

### 方案 3：确保有活跃会话

在触发任务前，先通过飞书发送一条消息给 bot，确保有活跃会话：

1. 在飞书中发送消息："ping"
2. 等待 bot 回复
3. 立即触发 cron 任务

## 最佳实践

### 1. 定时任务配置建议

| 场景 | sessionTarget | wakeMode | payload.kind | 说明 |
|------|---------------|----------|--------------|------|
| 定时提醒（主会话） | main | next-heartbeat | systemEvent | 等待心跳，确保有活跃会话 |
| 定时报告（独立会话） | isolated | now | agentTurn | 立即执行，指定发送目标 |
| 手动触发（主会话） | main | now | systemEvent | 需要确保有活跃会话 |
| 手动触发（独立会话） | isolated | now | agentTurn | 推荐，不依赖活跃会话 |

### 2. Isolated 会话的优势

- ✅ 不依赖主会话状态
- ✅ 可以指定明确的发送目标
- ✅ 立即执行，无延迟
- ✅ 独立的执行上下文，不影响主会话

### 3. Main 会话的限制

- ⚠️ 依赖 heartbeat 文件
- ⚠️ 需要有活跃的用户会话
- ⚠️ `wakeMode: "now"` 可能因为 empty-heartbeat 而跳过

## 验证步骤

### 1. 检查 Heartbeat 文件

```bash
# 查找 heartbeat 文件位置
find ~/.clawdbot -name "*heartbeat*" -type f

# 查看内容
cat ~/.clawdbot/heartbeat.json
```

### 2. 测试 Isolated 会话

```bash
# 创建测试任务
clawdbot cron add \
  --name "test_isolated" \
  --cron "*/5 * * * *" \
  --session isolated \
  --message "Test isolated session" \
  --deliver \
  --to "oc_acffe3c669016db989b35175a7889b4a"

# 手动触发
clawdbot cron run <job-id> --force

# 检查执行历史
clawdbot cron runs --id <job-id> --limit 1
```

### 3. 监视日志

```bash
tail -f /tmp/clawdbot/clawdbot-*.log | grep -E "cron|systemEvent|agentTurn"
```

## 相关代码

- `src/cron/service/ops.ts` - Cron 执行逻辑
- `src/gateway/heartbeat.ts` - Heartbeat 管理
- `src/agents/sessions.ts` - 会话管理
- `skills/cron/SKILL.md` - Cron 文档

## 总结

`empty-heartbeat-file` 错误表明主会话没有活跃的目标频道。对于需要立即执行并返回结果的任务，推荐使用 `isolated` 会话配置，这样可以避免依赖主会话状态，并且可以明确指定结果发送目标。
