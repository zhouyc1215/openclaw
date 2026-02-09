# 问题定位和解决方案

## 问题根本原因

通过日志分析，问题已经明确：

### 核心问题：Agent 返回工具调用后没有执行工具

**正常流程**：
```
用户消息 → Agent 决定调用工具 → 执行工具 → 将结果返回 Agent → Agent 生成文本回复 → 发送给用户
```

**当前流程**：
```
用户消息 → Agent 决定调用工具 → ❌ 直接将工具调用 JSON 发送给用户 → 结束
```

### 关键证据

1. **queuedFinal=false**：表示这不是最终回复，应该还有后续步骤
2. **replies=0**：没有文本回复被发送
3. **工具调用 JSON 被直接发送**：`{"name": "exec", "arguments": {...}}`
4. **没有工具执行日志**：日志中没有看到工具执行的记录

## 可能的原因

### 原因 1：通义千问模型的工具调用格式不兼容

**分析**：
- Clawdbot 可能是为 OpenAI 的工具调用格式设计的
- 通义千问的工具调用格式可能略有不同
- 导致 Clawdbot 无法识别和执行工具调用

**验证方法**：
查看通义千问 API 返回的原始响应格式

### 原因 2：工具执行循环被禁用

**分析**：
- 配置中可能禁用了工具执行
- 或者 `maxToolRoundtrips` 设置为 0

**验证方法**：
```bash
pnpm clawdbot config get agents.defaults | grep -i tool
```

### 原因 3：飞书频道的特殊处理逻辑

**分析**：
- 飞书插件可能有特殊的消息处理逻辑
- 可能在工具调用时直接返回而不是继续执行

## 解决方案

### 方案 1：禁用工具调用（临时方案）

修改配置，禁用工具：

```json
{
  "agents": {
    "defaults": {
      "maxToolRoundtrips": 0
    }
  }
}
```

或者：

```json
{
  "agents": {
    "defaults": {
      "tools": {
        "enabled": false
      }
    }
  }
}
```

**优点**：立即解决问题，Agent 会直接返回文本回复
**缺点**：失去工具调用能力

### 方案 2：修改系统提示词

如果系统提示词包含工具定义，可能需要移除或调整，避免模型倾向于调用工具。

### 方案 3：修复工具执行逻辑（根本解决）

需要查看源代码，修复工具执行循环的问题。

可能需要修改的文件：
- `src/agents/pi-embedded-runner/run/attempt.ts`
- `src/auto-reply/reply/dispatch-from-config.ts`
- 飞书插件的消息处理代码

### 方案 4：切换到 Ollama 模型（临时方案）

如果通义千问的工具调用格式不兼容，可以暂时切换回 Ollama：

```bash
cp ~/.clawdbot/clawdbot.json.backup ~/.clawdbot/clawdbot.json
systemctl --user restart clawdbot-gateway.service
```

## 立即行动

### 步骤 1：禁用工具（最快解决）

```bash
# 备份当前配置
cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.before-disable-tools

# 添加配置禁用工具
cat ~/.clawdbot/clawdbot.json | jq '.agents.defaults.maxToolRoundtrips = 0' > /tmp/config.json
cp /tmp/config.json ~/.clawdbot/clawdbot.json

# 重启服务
systemctl --user restart clawdbot-gateway.service
```

### 步骤 2：测试

在飞书发送简单消息：
```
你好
```

预期结果：应该返回正常的文本回复，而不是工具调用 JSON

### 步骤 3：验证

查看日志确认：
```bash
tail -f /tmp/clawdbot/clawdbot-*.log | grep "feishu deliver"
```

应该看到文本回复而不是工具调用 JSON

## 总结

**问题**：Agent 返回工具调用后没有执行工具，直接将 JSON 发送给用户

**临时解决方案**：禁用工具调用（`maxToolRoundtrips: 0`）

**根本解决方案**：需要修复工具执行循环的代码，或者确保通义千问的工具调用格式与 Clawdbot 兼容

**建议**：先使用临时方案快速恢复服务，然后再深入研究根本解决方案
