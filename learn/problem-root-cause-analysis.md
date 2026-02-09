# 问题根本原因分析

## 问题现象

所有飞书消息都返回**工具调用 JSON** 而不是文本回复：

### 调用记录

| 时间 | 工具调用 | 状态 |
|------|---------|------|
| 11:29:14 | `{"name": "session_status", "arguments": {}}` | queuedFinal=false, replies=0 |
| 11:34:20 | `{"name": "exec", "arguments": {"command": "date '+%Y-%m-%d %H:%M:%S %Z'"}}` | queuedFinal=false, replies=0 |
| 11:36:15 | `{"name": "exec", "arguments": {"command": "free -h && echo && top -bn1 \| head -20"}}` | queuedFinal=false, replies=0 |

## 关键发现

### 1. Agent 执行流程正常
```
✅ 消息接收正常
✅ Agent 启动正常
✅ API 调用成功（无 HTTP 400 错误）
✅ 执行时间正常（2-2.3 秒）
✅ Agent 正常结束
```

### 2. 但返回内容异常
```
❌ 返回的是工具调用 JSON
❌ 工具调用没有被执行
❌ 没有文本回复
❌ queuedFinal=false（表示不是最终回复）
❌ replies=0（没有回复）
```

### 3. 缺失的步骤

**正常流程应该是**：
```
1. Agent 收到消息
2. Agent 决定调用工具
3. 🔧 执行工具（缺失！）
4. 🔧 将工具结果返回给 Agent（缺失！）
5. 🔧 Agent 生成最终文本回复（缺失！）
6. 发送文本回复给用户
```

**当前流程**：
```
1. Agent 收到消息
2. Agent 决定调用工具
3. ❌ 直接将工具调用 JSON 发送给用户
4. ❌ 结束（没有后续步骤）
```

## 根本原因

### 原因 1：工具执行循环被禁用或损坏

**证据**：
- Agent 返回工具调用后立即结束
- 没有看到工具执行的日志
- `queuedFinal=false` 表示 Agent 知道这不是最终回复
- 但没有继续执行

**可能的配置问题**：
```json
{
  "agents": {
    "defaults": {
      "tools": {
        "enabled": false  // 工具可能被禁用
      }
    }
  }
}
```

### 原因 2：通义千问模型行为异常

**证据**：
- 用户可能发送了简单消息（如"你好"）
- 但模型认为需要调用工具（如 `exec`、`session_status`）
- 这不是正常的对话行为

**可能的原因**：
- 系统提示词包含了工具定义
- 模型"看到"工具列表后倾向于调用工具
- 通义千问对工具调用的理解可能与 OpenAI 不同

### 原因 3：飞书频道特殊处理

**证据**：
- 所有调用都来自飞书频道
- `messageChannel=feishu`
- 可能飞书频道有特殊的工具处理逻辑

## 定位代码位置

### 1. 工具执行逻辑

查找工具执行的代码：
```bash
grep -r "tool.*execute\|execute.*tool" src/agents/ --include="*.ts"
```

### 2. 飞书消息处理

查找飞书频道的消息处理：
```bash
grep -r "feishu deliver\|dispatch complete" src/ --include="*.ts"
```

### 3. queuedFinal 逻辑

查找 `queuedFinal` 的设置逻辑：
```bash
grep -r "queuedFinal" src/ --include="*.ts"
```

## 验证方法

### 方法 1：检查配置

```bash
pnpm clawdbot config get agents.defaults.tools
```

### 方法 2：查看完整日志

查看 Agent 的详细日志，看是否有工具执行相关的错误：
```bash
grep -A 20 "embedded run agent start" /tmp/clawdbot/clawdbot-*.log | grep -i "tool\|error"
```

### 方法 3：测试其他频道

如果有其他频道（如 Telegram），测试是否也有同样的问题。

## 临时解决方案

### 方案 1：禁用工具（如果不需要）

修改配置禁用工具：
```json
{
  "agents": {
    "defaults": {
      "maxToolRoundtrips": 0
    }
  }
}
```

### 方案 2：修改系统提示词

如果系统提示词包含工具定义，可能需要调整。

### 方案 3：切换模型

测试其他模型（如 qwen-turbo）是否有同样的问题。

## 下一步

1. 检查 Agent 配置中的工具设置
2. 查看源代码中的工具执行逻辑
3. 确认是否是通义千问模型的特殊行为
4. 如果需要，修改代码以正确处理工具调用
