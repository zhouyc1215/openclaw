# Cron 循环最新分析 - 2026-02-12

## 会话信息

- **会话 ID**: ff2c51b1-4a8f-4b63-b54f-1a7937166449
- **时间范围**: 2026-02-12 00:38 - 02:57 (持续约 2.5 小时)
- **循环次数**: 72+ 次 cron 错误
- **模型**: qwen-max (qwen-portal)

## 问题描述

Agent 试图创建一个每日运行的 cron 任务来执行 `get_top_ai_projects.sh` 脚本，但陷入了死循环。

## 错误的调用参数

Agent 反复使用以下参数：

```json
{
  "action": "add",
  "job": {
    "name": "get_top_ai_projects",
    "schedule": {
      "kind": "cron",
      "expr": "0 9 * * *"
    },
    "sessionTarget": "main",
    "payload": {
      "kind": "exec",                                    // ❌ 无效的 kind
      "text": "/home/tsl/clawd/get_top_ai_projects.sh"  // ❌ 错误的属性名
    }
  }
}
```

## 返回的错误信息

```
invalid cron.add params: 
- at /payload: must have required property 'text'
- at /payload: unexpected property 'command'
- at /payload/kind: must be equal to constant
- at /payload: must have required property 'message'
- at /payload: must match a schema in anyOf
```

## 根本原因分析

### 1. 无效的 payload.kind

Agent 使用了 `kind: "exec"`，但根据 schema 定义，只有两种有效的 kind：

- `"systemEvent"` - 用于 main session
- `"agentTurn"` - 用于 isolated session

**没有 `"exec"` 这个选项！**

### 2. 错误的理解

Agent 似乎认为：
- Cron 可以直接执行 shell 脚本
- 使用 `kind: "exec"` 和 `text: "/path/to/script.sh"` 就能运行脚本

但实际上：
- Cron 只能发送消息到 agent session
- 不能直接执行 shell 命令
- 需要通过 agent 来执行命令

### 3. 正确的方法

对于 main session，应该使用：

```json
{
  "action": "add",
  "job": {
    "name": "get_top_ai_projects",
    "schedule": {
      "kind": "cron",
      "expr": "0 9 * * *",
      "tz": "Asia/Shanghai"
    },
    "sessionTarget": "main",
    "wakeMode": "next-heartbeat",
    "payload": {
      "kind": "systemEvent",
      "text": "Run the get_top_ai_projects.sh script to fetch today's top AI projects"
    }
  }
}
```

然后 agent 会收到这个消息，并使用 `exec` 工具来运行脚本。

### 4. 为什么 Agent 会这样理解？

可能的原因：
1. **错误消息不够清晰** - 错误说 "must be equal to constant" 但没说是哪个 constant
2. **缺少示例** - 错误中没有给出正确的格式示例
3. **混淆了概念** - Agent 可能混淆了：
   - Cron payload 的 kind (systemEvent/agentTurn)
   - Agent 工具的名称 (exec, cron, etc.)
4. **上下文误导** - 可能之前的对话中提到了 "exec" 相关内容

## Agent 的思考过程（从消息中提取）

Agent 在消息中说：

> "看来我仍然没有正确设置 `payload` 参数。让我再次检查并确保使用正确的格式。
> 
> ### 正确的 Cron 任务参数
> 
> 根据错误信息，`payload` 应该包含 `kind` 为 `exec` 和 `text` 属性。我们需要将脚本命令放在 `text` 中，并且 `kind` 应该是 `exec`。"

**这是完全错误的理解！** Agent 从错误信息中得出了错误的结论。

## 循环模式

```
1. Agent: 使用 kind: "exec"
2. Gateway: 返回验证错误
3. Agent: "我理解了，应该用 kind: 'exec'"
4. Agent: 再次使用 kind: "exec"
5. Gateway: 返回相同的验证错误
6. 重复步骤 3-5，共 72+ 次
```

## 为什么 Agent 无法从错误中学习？

### 错误信息的问题

当前错误信息：
```
at /payload/kind: must be equal to constant
```

这个错误太模糊了！应该改为：
```
at /payload/kind: must be "systemEvent" (for sessionTarget: "main") or "agentTurn" (for sessionTarget: "isolated")
```

### Agent 的推理缺陷

1. Agent 看到 "must have required property 'text'" 
2. Agent 认为：payload 需要 text 属性 ✓
3. Agent 看到 "must have required property 'message'"
4. Agent 认为：payload 需要 message 属性 ✓
5. Agent 看到 "must match a schema in anyOf"
6. Agent 认为：我需要同时满足两个 schema？❌

实际上，anyOf 意味着"满足其中一个即可"，但 Agent 没有理解这一点。

## 解决方案

### 立即修复

1. **停止当前会话**
```bash
# 方法 1: 在飞书中发送
/new

# 方法 2: 重启 gateway
pnpm clawdbot gateway restart
```

2. **手动创建正确的 cron 任务**
```bash
clawdbot cron add \
  --name "get_top_ai_projects" \
  --cron "0 9 * * *" \
  --tz "Asia/Shanghai" \
  --session-target main \
  --system-event "Run the get_top_ai_projects.sh script"
```

### 短期修复（防止循环）

1. **集成 ToolRetryGuard** - 在 3 次失败后阻止继续调用
2. **改进错误消息** - 在 cron tool 中添加更清晰的错误提示

### 中期修复（改进理解）

1. **更新 cron skill 文档** - 已完成 ✓
2. **在 agent prompt 中添加说明**：
   ```
   IMPORTANT: Cron jobs cannot directly execute shell commands.
   - Use payload.kind: "systemEvent" with descriptive text
   - The agent will receive the text and can then use exec tool
   - Never use payload.kind: "exec" (it doesn't exist)
   ```

3. **改进 cron tool 的错误消息**：
   ```typescript
   if (job.payload.kind !== "systemEvent" && job.payload.kind !== "agentTurn") {
     throw new Error(
       `Invalid payload.kind: "${job.payload.kind}". ` +
       `Must be "systemEvent" (for main session) or "agentTurn" (for isolated session). ` +
       `Example for main: { kind: "systemEvent", text: "Your task description" }`
     );
   }
   ```

### 长期修复（架构改进）

1. **考虑添加 exec 支持** - 如果这是常见需求，可以考虑：
   - 添加新的 payload kind: "exec"
   - 或者在 isolated session 中支持直接执行命令
   - 但需要仔细考虑安全性

2. **改进 schema 验证错误** - 在 TypeBox/Ajv 层面改进 anyOf 错误消息

## 统计数据

- **总 token 消耗**: 约 24,000+ tokens per attempt × 72 attempts = ~1,728,000 tokens
- **估计成本**: 约 $0.50 × 72 = $36 (浪费在循环上)
- **时间浪费**: 2.5 小时

## 相关文件

- 会话日志: `~/.clawdbot/agents/main/sessions/ff2c51b1-4a8f-4b63-b54f-1a7937166449.jsonl`
- Cron schema: `src/gateway/protocol/schema/cron.ts`
- Cron tool: `src/agents/tools/cron-tool.ts`
- Cron skill: `skills/cron/SKILL.md` (已创建)
- 分析脚本: `analyze-cron-loop.py`

## 下一步行动

1. ✅ 分析完成 - 理解了 Agent 使用 `kind: "exec"` 的错误
2. ⏳ 停止当前循环（重启 gateway 或发送 /new）
3. ⏳ 集成 ToolRetryGuard
4. ⏳ 改进 cron tool 错误消息
5. ⏳ 更新 agent prompt 说明 cron 的正确用法
6. ⏳ 考虑是否需要支持直接执行命令的功能

## 教训

1. **验证错误需要更具体** - "must be equal to constant" 太模糊
2. **需要提供正确示例** - 错误消息中应该包含正确的格式
3. **anyOf 验证很容易误导** - Agent 难以理解"满足其中一个"的概念
4. **循环检测至关重要** - ToolRetryGuard 能避免这种昂贵的循环
5. **文档很重要** - 但 Agent 在错误状态下可能不会查阅文档
