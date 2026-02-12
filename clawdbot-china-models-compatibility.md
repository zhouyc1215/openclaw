# Clawdbot 国产模型兼容性改进建议

## 问题背景

国产大模型在实现 OpenAI 兼容 API 时，普遍存在"伪 tool calling"问题：

### 受影响的模型
- **MiniMax**: 返回 XML 格式的工具调用 (`<invoke>`, `<minimax:tool_call>`)
- **智谱 (GLM)**: 部分版本返回非标准格式
- **早期 Qwen**: function calling 格式不完全兼容
- 其他国产模型可能存在类似问题

### 问题表现
1. 模型在 `content` 字段中返回工具调用的 XML/文本表示，而不是标准的 `tool_calls` 结构
2. 即使禁用工具，模型仍然尝试生成工具调用格式
3. 导致用户收到空消息或格式错误的消息

## 解决方案设计

### 1. 在模型接入层添加 `sanitizeToolCall` 函数

**位置建议**: `src/agents/model-adapter.ts` 或 `src/agents/response-sanitizer.ts`

```typescript
/**
 * 清理国产模型返回的伪工具调用内容
 * 
 * @param model - 模型标识符 (如 "minimax/MiniMax-M2.1")
 * @param content - 模型返回的原始内容
 * @returns 清理后的内容
 */
export function sanitizeToolCall(model: string, content: string): string {
  if (!content) return content;
  
  const provider = model.split('/')[0].toLowerCase();
  
  // MiniMax 特殊处理
  if (provider === 'minimax') {
    return sanitizeMinimaxToolCall(content);
  }
  
  // 智谱 GLM 特殊处理
  if (provider === 'zhipu' || provider === 'glm') {
    return sanitizeZhipuToolCall(content);
  }
  
  // Qwen 早期版本特殊处理
  if (provider === 'qwen' || provider === 'qwen-portal') {
    return sanitizeQwenToolCall(content);
  }
  
  // 通用 XML 工具调用清理
  return sanitizeGenericToolCall(content);
}

/**
 * 清理 MiniMax 的 XML 工具调用
 */
function sanitizeMinimaxToolCall(content: string): string {
  // 检测是否包含工具调用标记
  if (!/minimax:tool_call/i.test(content) && !/<invoke\b/i.test(content)) {
    return content;
  }
  
  // 尝试提取工具调用意图
  const cmdMatch = content.match(/<cmd>([^<]+)<\/cmd>/);
  if (cmdMatch) {
    const cmd = cmdMatch[1].trim();
    // 根据命令类型返回友好提示
    if (cmd.includes('date') || cmd.includes('time')) {
      return '抱歉，我无法直接获取当前时间。请问我可以用其他方式帮助你吗？';
    }
    return `我理解你想执行"${cmd}"，但我目前无法执行命令。请用文字描述你的需求。`;
  }
  
  // 移除所有 XML 标签
  let cleaned = content.replace(/<invoke\b[^>]*>[\s\S]*?<\/invoke>/gi, '');
  cleaned = cleaned.replace(/<\/?minimax:tool_call>/gi, '');
  
  // 如果清理后为空，返回通用消息
  if (!cleaned.trim()) {
    return '抱歉，我遇到了一些技术问题。请换一种方式提问。';
  }
  
  return cleaned;
}

/**
 * 清理智谱 GLM 的工具调用
 */
function sanitizeZhipuToolCall(content: string): string {
  // TODO: 根据智谱实际格式实现
  // 可能的格式: ```tool_call\n{...}\n```
  if (content.includes('```tool_call')) {
    const cleaned = content.replace(/```tool_call[\s\S]*?```/g, '');
    return cleaned.trim() || '抱歉，我遇到了一些技术问题。请换一种方式提问。';
  }
  return content;
}

/**
 * 清理 Qwen 早期版本的 function calling
 */
function sanitizeQwenToolCall(content: string): string {
  // TODO: 根据 Qwen 实际格式实现
  // 早期版本可能使用特殊标记
  return content;
}

/**
 * 通用工具调用清理（兜底方案）
 */
function sanitizeGenericToolCall(content: string): string {
  // 移除常见的工具调用标记
  let cleaned = content;
  
  // 移除 XML 风格的标记
  cleaned = cleaned.replace(/<\/?tool_call[^>]*>/gi, '');
  cleaned = cleaned.replace(/<\/?function[^>]*>/gi, '');
  cleaned = cleaned.replace(/<invoke\b[^>]*>[\s\S]*?<\/invoke>/gi, '');
  
  // 移除 Markdown 代码块中的工具调用
  cleaned = cleaned.replace(/```(?:tool_call|function)[\s\S]*?```/g, '');
  
  return cleaned;
}

/**
 * 清理模型返回的思考过程标记
 * 某些模型（如 MiniMax）会返回 <think> 标签
 */
export function sanitizeThinkingTags(content: string): string {
  return content.replace(/<\/?think>/gi, '');
}
```

### 2. 集成到响应处理流程

**在 `src/agents/pi-embedded.ts` 或响应处理的核心位置：**

```typescript
import { sanitizeToolCall, sanitizeThinkingTags } from './response-sanitizer.js';

// 在处理模型响应时
function processModelResponse(model: string, response: any): string {
  let content = response.choices[0]?.message?.content || '';
  
  // 清理伪工具调用
  content = sanitizeToolCall(model, content);
  
  // 清理思考标记
  content = sanitizeThinkingTags(content);
  
  return content;
}
```

### 3. 配置选项

在 `clawdbot.json` 中添加配置选项：

```json
{
  "models": {
    "sanitization": {
      "enabled": true,
      "providers": {
        "minimax": {
          "stripToolCalls": true,
          "stripThinkingTags": true
        },
        "zhipu": {
          "stripToolCalls": true
        },
        "qwen": {
          "stripToolCalls": false  // 新版本已修复
        }
      }
    }
  }
}
```

## 实施优先级

### P0 (立即实施)
- [ ] 实现 `sanitizeMinimaxToolCall` - MiniMax 是当前最紧迫的问题
- [ ] 集成到 Feishu 插件的 `reply-dispatcher.ts`

### P1 (短期)
- [ ] 将清理逻辑从插件层移到核心模型适配层
- [ ] 实现通用的 `sanitizeToolCall` 框架
- [ ] 添加配置选项

### P2 (中期)
- [ ] 实现智谱、Qwen 等其他模型的清理逻辑
- [ ] 添加单元测试
- [ ] 文档化各模型的已知问题

### P3 (长期)
- [ ] 建立模型兼容性测试套件
- [ ] 自动检测和报告模型兼容性问题
- [ ] 与模型提供商沟通改进

## 测试用例

```typescript
describe('sanitizeToolCall', () => {
  it('should clean MiniMax XML tool calls', () => {
    const input = '<invoke><exec><cmd>date "+%H:%M:%S"</cmd></exec></invoke>';
    const output = sanitizeToolCall('minimax/MiniMax-M2.1', input);
    expect(output).not.toContain('<invoke>');
    expect(output.length).toBeGreaterThan(0);
  });
  
  it('should preserve normal text content', () => {
    const input = '你好，现在是下午3点。';
    const output = sanitizeToolCall('minimax/MiniMax-M2.1', input);
    expect(output).toBe(input);
  });
  
  it('should handle mixed content', () => {
    const input = '让我帮你查询。<invoke><exec>...</exec></invoke>';
    const output = sanitizeToolCall('minimax/MiniMax-M2.1', input);
    expect(output).toContain('让我帮你查询');
    expect(output).not.toContain('<invoke>');
  });
});
```

## 相关文件

- `src/agents/response-sanitizer.ts` (新建)
- `src/agents/pi-embedded.ts` (修改)
- `src/agents/model-adapter.ts` (修改)
- `extensions/feishu/src/reply-dispatcher.ts` (临时方案，后续移除)

## 参考资料

- MiniMax API 文档: https://api.minimaxi.com/document/guides/chat-model/V2
- OpenAI Tool Calling 标准: https://platform.openai.com/docs/guides/function-calling
- 相关 Issue: [待创建]

## 备注

这个问题反映了国产模型生态的一个普遍挑战：虽然声称兼容 OpenAI API，但在工具调用等高级特性上存在实现差异。建立统一的清理层可以：

1. 提升用户体验 - 避免收到格式错误的消息
2. 降低维护成本 - 集中处理而不是在各个插件中重复实现
3. 便于扩展 - 新增模型支持时只需添加对应的清理逻辑
4. 提供降级方案 - 当工具调用不可用时，至少保证基本对话功能

---

**创建时间**: 2026-02-12  
**作者**: AI Assistant  
**状态**: 提案 (Proposal)
