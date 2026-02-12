# MiniMax Tool Call Adapter - 集成指南

## 🎯 核心价值

将 MiniMax 返回的 XML 格式工具调用转换为 OpenAI 兼容的 JSON 结构，实现：
- ✅ 无缝集成到现有 OpenAI SDK 代码
- ✅ 保持工具调用功能完整可用
- ✅ 零侵入式适配，不影响其他模型
- ✅ 支持多种 MiniMax XML 格式

---

## 📦 安装

```bash
# 复制文件到项目中
cp minimax-tool-call-adapter.ts src/agents/
cp minimax-tool-call-adapter.test.ts src/agents/

# 运行测试
npm test minimax-tool-call-adapter.test.ts
```

---

## 🚀 快速开始

### 场景 1: Clawdbot / OpenClaw 集成

**位置**: `src/agents/pi-embedded.ts` 或模型响应处理的核心位置

```typescript
import { processMinimaxResponse, isMinimaxResponse } from './minimax-tool-call-adapter.js';

async function callModel(messages: any[], tools: any[]) {
  const response = await fetch('https://api.minimaxi.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${MINIMAX_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'MiniMax-M2.1',
      messages,
      tools, // 正常传递工具定义
    }),
  });

  const data = await response.json();
  
  // 🔥 关键：自动转换 MiniMax 响应
  if (isMinimaxResponse(data)) {
    return processMinimaxResponse(data);
  }
  
  return data; // 其他模型原样返回
}
```

### 场景 2: 飞书机器人集成

**位置**: `~/.clawdbot/extensions/feishu/src/reply-dispatcher.ts`

```typescript
import { processMinimaxResponse } from './minimax-tool-call-adapter.js';

export function createFeishuReplyDispatcher(params: CreateFeishuReplyDispatcherParams) {
  // ... 现有代码 ...

  const { dispatcher, replyOptions, markDispatchIdle } =
    core.channel.reply.createReplyDispatcherWithTyping({
      // ... 现有配置 ...
      deliver: async (payload: ReplyPayload) => {
        let text = payload.text ?? '';
        
        // 🔥 不再需要 stripMinimaxToolCallXml
        // 工具调用已经在模型层转换为标准格式
        
        // 只需清理思考标记
        text = stripThinkingTags(text);
        
        if (!text.trim()) {
          params.runtime.log?.(`feishu deliver: empty text, skipping`);
          return;
        }

        // ... 发送消息的现有逻辑 ...
      },
      // ... 其他配置 ...
    });

  return { dispatcher, replyOptions, markDispatchIdle };
}
```

### 场景 3: 通用 OpenAI SDK 集成

```typescript
import OpenAI from 'openai';
import { smartAdapter } from './minimax-tool-call-adapter.js';

// 创建自定义 HTTP 客户端
const client = new OpenAI({
  baseURL: 'https://api.minimaxi.com/v1',
  apiKey: MINIMAX_API_KEY,
  // 添加响应拦截器
  fetch: async (url, init) => {
    const response = await fetch(url, init);
    const data = await response.json();
    
    // 🔥 自动转换 MiniMax 响应
    const converted = smartAdapter(data);
    
    return new Response(JSON.stringify(converted), {
      status: response.status,
      headers: response.headers,
    });
  },
});

// 正常使用，工具调用自动工作
const completion = await client.chat.completions.create({
  model: 'MiniMax-M2.1',
  messages: [{ role: 'user', content: '北京天气如何？' }],
  tools: [
    {
      type: 'function',
      function: {
        name: 'get_weather',
        description: '获取天气信息',
        parameters: {
          type: 'object',
          properties: {
            city: { type: 'string' },
          },
        },
      },
    },
  ],
});

// tool_calls 已经是标准 OpenAI 格式
if (completion.choices[0].message.tool_calls) {
  console.log('工具调用:', completion.choices[0].message.tool_calls);
}
```

### 场景 4: Agent 框架集成 (LangChain / LlamaIndex)

```typescript
import { ChatOpenAI } from '@langchain/openai';
import { smartAdapter } from './minimax-tool-call-adapter.js';

// 创建自定义 LLM 类
class MinimaxChatModel extends ChatOpenAI {
  constructor(config: any) {
    super({
      ...config,
      configuration: {
        baseURL: 'https://api.minimaxi.com/v1',
        apiKey: MINIMAX_API_KEY,
        // 添加响应转换
        fetch: async (url, init) => {
          const response = await fetch(url, init);
          const data = await response.json();
          return new Response(
            JSON.stringify(smartAdapter(data)),
            { status: response.status, headers: response.headers }
          );
        },
      },
    });
  }
}

// 正常使用 LangChain
const model = new MinimaxChatModel({ model: 'MiniMax-M2.1' });
const result = await model.invoke([
  { role: 'user', content: '帮我查询北京天气' },
]);
```

---

## 🔧 Clawdbot 完整集成方案

### 步骤 1: 添加适配器到核心层

```bash
# 文件位置
src/agents/minimax-tool-call-adapter.ts
```

### 步骤 2: 在模型调用层集成

**文件**: `src/agents/pi-embedded.ts` (或类似的模型调用入口)

```typescript
import { processMinimaxResponse, isMinimaxResponse } from './minimax-tool-call-adapter.js';

// 在模型响应处理函数中
function processModelResponse(provider: string, rawResponse: any) {
  // 检测并转换 MiniMax 响应
  if (provider === 'minimax' || isMinimaxResponse(rawResponse)) {
    return processMinimaxResponse(rawResponse);
  }
  
  // 其他模型原样返回
  return rawResponse;
}
```

### 步骤 3: 移除插件层的临时方案

**文件**: `~/.clawdbot/extensions/feishu/src/reply-dispatcher.ts`

```typescript
// ❌ 删除这个函数（不再需要）
function stripMinimaxToolCallXml(text: string): string {
  // ...
}

// ✅ 只保留思考标记清理
function stripThinkingTags(text: string): string {
  return text.replace(/<\/?think>/gi, '');
}
```

### 步骤 4: 配置选项（可选）

**文件**: `~/.clawdbot/clawdbot.json`

```json
{
  "models": {
    "providers": {
      "minimax": {
        "baseUrl": "https://api.minimaxi.com/v1",
        "apiKey": "sk-api-...",
        "api": "openai-completions",
        "adapter": "minimax-tool-call",  // 启用适配器
        "models": [
          {
            "id": "MiniMax-M2.1",
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "minimax/MiniMax-M2.1"
      }
    }
  },
  "tools": {
    "allow": ["exec", "read", "write"]  // ✅ 现在可以正常启用工具
  }
}
```

---

## 📊 转换示例

### 示例 1: 天气查询

**MiniMax 原始响应**:
```json
{
  "choices": [{
    "message": {
      "content": "<tool_call>\n<name>get_weather</name>\n<arguments>{\"city\":\"Beijing\"}</arguments>\n</tool_call>"
    }
  }]
}
```

**转换后 (OpenAI 格式)**:
```json
{
  "choices": [{
    "message": {
      "content": null,
      "tool_calls": [{
        "id": "call_abc123...",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"city\":\"Beijing\"}"
        }
      }]
    },
    "finish_reason": "tool_calls"
  }]
}
```

### 示例 2: 执行命令

**MiniMax 原始响应**:
```json
{
  "choices": [{
    "message": {
      "content": "<invoke><exec>\n<cmd>date \"+%H:%M:%S\"</cmd>\n<timeout></timeout>\n</exec></invoke>"
    }
  }]
}
```

**转换后**:
```json
{
  "choices": [{
    "message": {
      "content": null,
      "tool_calls": [{
        "id": "call_def456...",
        "type": "function",
        "function": {
          "name": "exec",
          "arguments": "{\"cmd\":\"date \\\"+%H:%M:%S\\\"\"}"
        }
      }]
    },
    "finish_reason": "tool_calls"
  }]
}
```

### 示例 3: 纯文本 + 思考标记

**MiniMax 原始响应**:
```json
{
  "choices": [{
    "message": {
      "content": "<think>用户在问时间...</think>现在是下午3点。"
    }
  }]
}
```

**转换后**:
```json
{
  "choices": [{
    "message": {
      "content": "用户在问时间...现在是下午3点。"
    },
    "finish_reason": "stop"
  }]
}
```

---

## 🧪 测试

```bash
# 运行单元测试
npm test minimax-tool-call-adapter.test.ts

# 测试覆盖率
npm run test:coverage -- minimax-tool-call-adapter.test.ts
```

**测试用例覆盖**:
- ✅ 纯文本响应透传
- ✅ 标准 tool_call 格式转换
- ✅ invoke/exec 格式转换
- ✅ 多个工具调用
- ✅ 混合文本和工具调用
- ✅ 思考标记清理
- ✅ 边界情况处理

---

## 🔍 调试

### 启用调试日志

```typescript
import { convertMinimaxResponse } from './minimax-tool-call-adapter.js';

function debugConvert(response: any) {
  console.log('原始响应:', JSON.stringify(response, null, 2));
  
  const converted = convertMinimaxResponse(response);
  
  console.log('转换后:', JSON.stringify(converted, null, 2));
  
  return converted;
}
```

### 常见问题排查

**问题 1: 工具调用未被识别**
```typescript
// 检查内容格式
const content = response.choices[0].message.content;
console.log('Content:', content);
console.log('Has tool call:', /<tool_call|<invoke/.test(content));
```

**问题 2: 参数解析失败**
```typescript
// 检查 arguments 格式
const args = toolCall.function.arguments;
try {
  JSON.parse(args);
  console.log('Arguments valid JSON');
} catch (e) {
  console.error('Arguments invalid:', args);
}
```

---

## 🎨 扩展其他模型

适配器设计支持扩展到其他国产模型：

```typescript
// 添加智谱 GLM 支持
export function convertZhipuResponse(response: any): OpenAIResponse {
  // 实现智谱特定的转换逻辑
}

// 添加到智能适配器
export function smartAdapter(response: any): OpenAIResponse {
  if (isMinimaxResponse(response)) {
    return convertMinimaxResponse(response);
  }
  if (isZhipuResponse(response)) {
    return convertZhipuResponse(response);
  }
  return response;
}
```

---

## 📝 最佳实践

1. **在模型层转换，不在渠道层** - 保持渠道插件简洁
2. **使用 smartAdapter** - 自动检测和转换，支持多模型
3. **保留原始响应** - 便于调试和问题排查
4. **添加日志** - 记录转换前后的数据
5. **测试边界情况** - 格式错误、空内容等

---

## 🚀 性能优化

- 正则表达式已优化，避免回溯
- 仅在检测到 XML 标记时才解析
- 支持流式响应（未来扩展）

---

## 📚 相关资源

- [MiniMax API 文档](https://api.minimaxi.com/document)
- [OpenAI Tool Calling 规范](https://platform.openai.com/docs/guides/function-calling)
- [Clawdbot 文档](https://docs.clawd.bot)

---

## 🤝 贡献

欢迎提交 PR 添加对其他模型的支持！

**需要支持的模型**:
- [ ] 智谱 GLM
- [ ] 百川 Baichuan
- [ ] 月之暗面 Moonshot
- [ ] 其他国产模型

---

**创建时间**: 2026-02-12  
**版本**: 1.0.0  
**维护者**: Clawdbot Team
