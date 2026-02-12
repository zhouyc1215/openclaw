# Clawdbot 死循环问题分析

## 问题描述

Clawdbot 在处理飞书文档操作时陷入死循环，不断重复调用 `feishu_doc` 和 `feishu_drive` 工具但都失败。

## 用户请求

用户在飞书中发送消息：
1. "删除此文档"
2. "可以将其名字修改为'临时文档'吗？"
3. 提供了文档链接：`https://kcnj4dk8vebw.feishu.cn/docx/TDYVdwd1hokMbLxYThFcPkG1nmg`

## 循环模式

从会话日志中发现重复的错误模式：

### 错误 1: feishu_doc - 无效的 action
```
Validation failed for tool "feishu_doc":
  - action: must be equal to one of the allowed values

Received arguments:
{
  "action": "update",
  "doc_token": "TDYVdwd1hokMbLxYThFcPkG1nmg",
  "content": "# 临时文档\n\n这里是临时文档的内容。"
}
```

**问题**: Agent 尝试使用 `action: "update"` 但这不是有效的 action 值。

### 错误 2: feishu_drive - 400 错误
```
{
  "error": "Request failed with status code 400"
}
```

**问题**: feishu_drive 调用返回 400 错误，可能是参数不正确。

### 错误 3: feishu_doc - 缺少参数
```
{
  "error": "request miss document_id path argument"
}
```

**问题**: 缺少必需的 `document_id` 参数。

## 循环时间线

从日志时间戳分析：
- 开始时间：约 11:05:29
- 持续时间：至少 4 分钟（到 11:09:02）
- 调用频率：约每 10-15 秒一次
- 总调用次数：约 20+ 次

## 根本原因分析

### 1. 工具 Schema 不匹配
Agent 尝试使用的 `action: "update"` 不在 `feishu_doc` 工具的允许值列表中。

可能的有效 actions（需要确认）：
- `read`
- `write`
- `append`
- `create`
- ~~`update`~~ (无效)

### 2. 缺少错误恢复机制
Agent 在遇到工具调用失败后，没有：
- 停止重试
- 尝试其他方法
- 向用户报告失败

而是继续使用相同的错误参数重复调用。

### 3. 上下文理解问题
Agent 可能误解了用户的需求：
- 用户想"修改文档名字"
- Agent 尝试"更新文档内容"

这是两个不同的操作。

## 影响

1. **资源浪费**: 持续的 API 调用消耗资源
2. **用户体验差**: 用户没有收到任何响应
3. **会话阻塞**: 其他消息可能无法处理

## 建议的解决方案

### 短期修复

1. **添加重试限制**
   - 同一工具调用失败 N 次后停止
   - 向用户报告失败原因

2. **改进错误处理**
   - 工具验证失败时，检查 schema 并使用正确的参数
   - 提供更清晰的错误消息给 agent

3. **添加超时机制**
   - 单个任务执行时间超过阈值时中止

### 长期改进

1. **工具 Schema 文档化**
   - 在 prompt 中明确列出每个工具的有效 actions
   - 提供示例用法

2. **智能重试策略**
   - 分析错误类型
   - 自动调整参数重试
   - 或切换到替代方案

3. **任务监控**
   - 检测循环模式
   - 自动中断并报告

4. **改进 feishu_doc 工具**
   - 支持文档重命名操作
   - 或者明确说明不支持，让 agent 使用其他方法

## 需要检查的代码位置

1. **工具定义**: 查找 `feishu_doc` 工具的 schema 定义
2. **错误处理**: Agent 的工具调用错误处理逻辑
3. **重试机制**: 是否有重试限制？
4. **超时设置**: 任务执行超时配置

## 临时解决方案

如果 agent 仍在循环中：
1. 重启 gateway: `pnpm clawdbot gateway restart`
2. 或者清理会话: 删除或重命名会话文件
3. 在飞书中发送新消息打断循环

## 相关文件

- 会话日志: `~/.clawdbot/agents/main/sessions/b13d8019-6b88-446d-a7d0-7e0553af473a.jsonl`
- Gateway 日志: `/tmp/clawdbot/clawdbot-2026-02-11.log`
- 配置文件: `~/.clawdbot/clawdbot.json`
