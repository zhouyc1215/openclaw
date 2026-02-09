# 飞书工具调用问题修复总结

## 问题现象
飞书消息返回工具调用 JSON 而不是文本回复,例如:
```json
{"name": "exec", "arguments": {"command": "date '+%Y-%m-%d %H:%M:%S %Z'"}}
```

## 根本原因分析

### 1. 配置层面
- 用户设置了 `tools.deny: ["*"]` 试图禁用所有工具
- 该配置确实过滤了核心 Clawdbot 工具
- 但**飞书插件工具**仍然被注册(feishu_wiki, feishu_drive, feishu_bitable等)

### 2. 代码层面 - 关键Bug
在 `src/agents/system-prompt.ts` 中发现了一个严重的bug:

**问题代码**:
```typescript
"## Tooling",
"Tool availability (filtered by policy):",
"Tool names are case-sensitive. Call tools exactly as listed.",
toolLines.length > 0
  ? toolLines.join("\n")
  : [
      "Pi lists the standard tools above. This runtime enables:",
      "- grep: search file contents for patterns",
      "- find: find files by glob pattern",
      // ... 硬编码的工具列表
    ].join("\n"),
```

**Bug说明**:
- 当 `toolLines.length === 0` (所有工具被deny)时
- 系统提示仍然显示一个**硬编码的工具列表**
- 模型看到这个列表后,认为可以使用工具
- 模型生成工具调用JSON
- 但工具被deny,无法执行
- 原始JSON直接发送给用户

### 3. 执行流程
```
用户消息 → Agent启动
  ↓
创建工具列表(被tools.deny过滤为空)
  ↓
构建系统提示(Bug:显示硬编码工具列表)
  ↓
模型看到工具列表 → 生成工具调用JSON
  ↓
工具执行被阻止(因为tools.deny)
  ↓
工具调用JSON直接发送给用户 ❌
```

## 修复方案

### 修改文件: `src/agents/system-prompt.ts`

**修复后的代码**:
```typescript
"## Tooling",
toolLines.length > 0
  ? [
      "Tool availability (filtered by policy):",
      "Tool names are case-sensitive. Call tools exactly as listed.",
      toolLines.join("\n"),
      "TOOLS.md does not control tool availability; it is user guidance for how to use external tools.",
      "If a task is more complex or takes longer, spawn a sub-agent. It will do the work for you and ping you when it's done. You can always check up on it.",
    ].join("\n")
  : [
      "Tools are disabled in this session. Do not call tools.",
      "Respond directly to user queries with text only.",
    ].join("\n"),
"",
```

**修复说明**:
- 当工具列表为空时,明确告诉模型"工具已被禁用"
- 指示模型"仅使用文本直接回复"
- 不再显示硬编码的工具列表

## 配置文件

### `~/.clawdbot/clawdbot.json`
```json
{
  "tools": {
    "deny": ["*", "feishu_*", "group:feishu"]
  }
}
```

**说明**:
- `"*"`: 禁用所有核心工具
- `"feishu_*"`: 禁用所有飞书插件工具(通配符)
- `"group:feishu"`: 禁用飞书工具组

## 执行步骤

1. **修改代码**: 已修改 `src/agents/system-prompt.ts`
2. **重新构建**: `pnpm build` ✅
3. **重启服务**: `systemctl --user restart clawdbot-gateway.service` ✅
4. **测试验证**: 在飞书发送测试消息

## 预期结果

修复后的行为:
```
用户消息 → Agent启动
  ↓
创建工具列表(被tools.deny过滤为空)
  ↓
构建系统提示(显示"工具已禁用")
  ↓
模型看到禁用提示 → 生成文本回复
  ↓
文本回复发送给用户 ✅
```

## 技术细节

### 工具过滤机制
- 工具过滤发生在 `createClawdbotCodingTools()` 函数中
- 通过 `filterToolsByPolicy()` 应用 `tools.deny` 规则
- 过滤后的工具列表传递给 `buildEmbeddedSystemPrompt()`

### 系统提示构建
- `buildEmbeddedSystemPrompt()` 调用 `buildAgentSystemPrompt()`
- 传入 `toolNames` 数组(从过滤后的工具列表提取)
- 如果 `toolNames` 为空,现在会显示"工具已禁用"

### 模型行为
- 模型根据系统提示决定是否生成工具调用
- 如果系统提示说"工具已禁用",模型应该只生成文本
- 如果系统提示列出工具,模型可能生成工具调用

## 相关文件

- `src/agents/system-prompt.ts` - 系统提示构建(已修复)
- `src/agents/pi-tools.ts` - 工具创建和过滤
- `src/agents/pi-tools.policy.ts` - 工具策略过滤逻辑
- `src/agents/pi-embedded-runner/run/attempt.ts` - Agent运行入口
- `~/.clawdbot/clawdbot.json` - 配置文件

## 测试建议

1. 在飞书发送简单问候:"你好"
2. 在飞书发送需要计算的问题:"1+1等于几?"
3. 在飞书发送需要信息的问题:"今天天气怎么样?"

预期所有回复都是纯文本,不包含工具调用JSON。

## 时间线

- **11:29** - 发现问题:返回工具调用JSON
- **11:34** - 尝试配置 `tools.deny: ["*"]`
- **11:42** - 发现配置错误(maxToolRoundtrips)
- **11:44** - 修正配置,重启服务
- **19:49** - 深入代码分析,发现系统提示bug
- **19:53** - 修复代码,重新构建,重启服务

## 状态
✅ 代码已修复
✅ 服务已重启
⏳ 等待测试验证
