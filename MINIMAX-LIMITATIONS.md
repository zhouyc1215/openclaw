# MiniMax 模型已知限制

## 问题描述

MiniMax 的 OpenAI 兼容 API 存在工具调用格式不兼容的问题：

- **预期行为**: 返回标准的 OpenAI `tool_calls` JSON 结构
- **实际行为**: 返回 XML 格式的工具调用嵌入在文本内容中

### 示例

**MiniMax 实际返回**:
```xml
<invoke><exec>
  <cmd>date "+%H:%M:%S"</cmd>
</exec></invoke>
```

**OpenAI 标准格式**:
```json
{
  "tool_calls": [{
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "exec",
      "arguments": "{\"cmd\":\"date \\\"+%H:%M:%S\\\"\"}"
    }
  }]
}
```

## 影响

当使用 MiniMax 模型并启用工具时：
- 工具调用无法正常执行
- 用户收到空消息或格式错误的消息
- 功能降级为纯文本对话

## 解决方案

### 方案 1: 使用千问模型（推荐）

千问（Qwen）模型完全兼容 OpenAI API，支持正常的工具调用：

```bash
# 切换到千问模型
clawdbot config set agents.defaults.model.primary "qwen-portal/qwen-plus"
clawdbot gateway restart
```

**优势**:
- ✅ 完整的工具调用支持
- ✅ 更好的中文理解能力
- ✅ 更稳定的 API
- ✅ 更快的响应速度

### 方案 2: 禁用工具使用 MiniMax

如果必须使用 MiniMax，可以禁用工具调用：

```bash
# 禁用所有工具
clawdbot config set tools.allow "[]"
clawdbot config set tools.deny '["*"]'
clawdbot gateway restart
```

**限制**:
- ❌ 无法执行命令
- ❌ 无法读写文件
- ❌ 功能受限，仅支持纯文本对话

### 方案 3: 等待 MiniMax 修复

MiniMax 团队可能会在未来版本中修复 OpenAI API 兼容性问题。

## 技术细节

### 为什么不能在 Clawdbot 中修复？

Clawdbot 使用 `@mariozechner/pi-ai` SDK 来调用模型 API。这个 SDK 已经处理了 HTTP 请求和响应，并生成了标准化的事件流。

要支持 MiniMax 的非标准格式，需要：

1. **在 SDK 层面拦截** - 需要 fork 和维护 `@mariozechner/pi-ai`
2. **在应用层转换** - 需要深度修改消息流处理逻辑
3. **在渠道层处理** - 只能提供降级体验（当前方案）

所有方案都有较高的维护成本，且只是为了兼容一个非标准的 API。

### 适配器代码

我们已经开发了完整的 MiniMax 适配器代码（`minimax-tool-call-adapter.ts`），可以将 XML 格式转换为 OpenAI 格式。但由于 SDK 架构限制，无法直接集成。

如果 MiniMax 团队或 Clawdbot 团队未来提供响应拦截钩子，可以快速集成这个适配器。

## 相关文件

- `minimax-tool-call-adapter.ts` - 完整的转换适配器
- `minimax-tool-call-adapter.test.ts` - 测试套件
- `minimax-adapter-integration-guide.md` - 集成指南
- `test-results.md` - 测试结果

## 建议

**对于生产环境，强烈建议使用千问（Qwen）模型**，它提供：
- 完整的 OpenAI API 兼容性
- 优秀的中文能力
- 稳定的工具调用支持
- 更好的性价比

---

**最后更新**: 2026-02-12  
**状态**: MiniMax API 问题待修复  
**推荐模型**: qwen-portal/qwen-plus
