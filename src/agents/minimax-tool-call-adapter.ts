/**
 * MiniMax Tool Call Adapter
 *
 * 将 MiniMax 返回的 XML 格式工具调用转换为 OpenAI 兼容的 JSON 结构
 *
 * 适用场景：
 * - Clawdbot / OpenClaw
 * - 任意使用 OpenAI SDK 的项目
 * - 飞书/微信机器人
 * - Agent 框架
 *
 * @module minimax-tool-call-adapter
 */

import { randomUUID } from "crypto";

/**
 * OpenAI 兼容的工具调用结构
 */
export interface OpenAIToolCall {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
}

/**
 * OpenAI 兼容的消息结构
 */
export interface OpenAIMessage {
  role: string;
  content: string | null;
  tool_calls?: OpenAIToolCall[];
  name?: string;
}

/**
 * OpenAI 兼容的响应结构
 */
export interface OpenAIResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: OpenAIMessage;
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/**
 * MiniMax 原始响应结构
 */
export interface MinimaxResponse {
  id: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
      name?: string;
    };
    finish_reason: string;
  }>;
  created: number;
  model: string;
  object: string;
  usage?: any;
}

/**
 * 解析后的工具调用信息
 */
interface ParsedToolCall {
  name: string;
  arguments: string;
}

/**
 * 检测内容是否包含 MiniMax XML 工具调用
 */
function hasMinimaxToolCall(content: string): boolean {
  if (!content) return false;

  // 检测多种可能的 XML 格式
  return (
    /<tool_call\b/i.test(content) ||
    /<invoke\b/i.test(content) ||
    /<minimax:tool_call\b/i.test(content)
  );
}

/**
 * 从 XML 内容中提取工具调用信息
 *
 * 支持的格式：
 * 1. <tool_call><name>func</name><arguments>{...}</arguments></tool_call>
 * 2. <invoke><exec><cmd>...</cmd></exec></invoke>
 * 3. <minimax:tool_call>...</minimax:tool_call>
 */
function parseMinimaxToolCalls(content: string): ParsedToolCall[] {
  const toolCalls: ParsedToolCall[] = [];

  // 格式 1: 标准 tool_call 格式
  const toolCallRegex = /<tool_call[^>]*>([\s\S]*?)<\/tool_call>/gi;
  let match: RegExpExecArray | null;

  while ((match = toolCallRegex.exec(content)) !== null) {
    const toolCallContent = match[1];

    const nameMatch = toolCallContent.match(/<name>([^<]+)<\/name>/i);
    const argsMatch = toolCallContent.match(/<arguments>([\s\S]*?)<\/arguments>/i);

    if (nameMatch) {
      const name = nameMatch[1].trim();
      const args = argsMatch ? argsMatch[1].trim() : "{}";

      toolCalls.push({ name, arguments: args });
    }
  }

  // 格式 2: invoke/exec 格式（MiniMax 特有）
  if (toolCalls.length === 0) {
    const invokeRegex = /<invoke[^>]*>([\s\S]*?)<\/invoke>/gi;

    while ((match = invokeRegex.exec(content)) !== null) {
      const invokeContent = match[1];

      // 检测 exec 类型
      if (/<exec[^>]*>/i.test(invokeContent)) {
        const cmdMatch = invokeContent.match(/<cmd>([^<]+)<\/cmd>/i);
        const timeoutMatch = invokeContent.match(/<timeout>([^<]*)<\/timeout>/i);
        const envMatch = invokeContent.match(/<env>([^<]*)<\/env>/i);

        if (cmdMatch) {
          const args = JSON.stringify({
            cmd: cmdMatch[1].trim(),
            timeout: timeoutMatch ? timeoutMatch[1].trim() : undefined,
            env: envMatch ? envMatch[1].trim() : undefined,
          });

          toolCalls.push({
            name: "exec",
            arguments: args,
          });
        }
      }

      // 检测 read 类型
      if (/<read[^>]*>/i.test(invokeContent)) {
        const pathMatch = invokeContent.match(/<path>([^<]+)<\/path>/i);

        if (pathMatch) {
          const args = JSON.stringify({
            path: pathMatch[1].trim(),
          });

          toolCalls.push({
            name: "read",
            arguments: args,
          });
        }
      }

      // 检测 write 类型
      if (/<write[^>]*>/i.test(invokeContent)) {
        const pathMatch = invokeContent.match(/<path>([^<]+)<\/path>/i);
        const contentMatch = invokeContent.match(/<content>([\s\S]*?)<\/content>/i);

        if (pathMatch) {
          const args = JSON.stringify({
            path: pathMatch[1].trim(),
            content: contentMatch ? contentMatch[1].trim() : "",
          });

          toolCalls.push({
            name: "write",
            arguments: args,
          });
        }
      }
    }
  }

  return toolCalls;
}

/**
 * 从内容中移除 XML 工具调用标记
 */
function stripToolCallXML(content: string): string {
  let cleaned = content;

  // 移除 tool_call 标签
  cleaned = cleaned.replace(/<tool_call[^>]*>[\s\S]*?<\/tool_call>/gi, "");

  // 移除 invoke 标签
  cleaned = cleaned.replace(/<invoke[^>]*>[\s\S]*?<\/invoke>/gi, "");

  // 移除 minimax:tool_call 标签
  cleaned = cleaned.replace(/<\/?minimax:tool_call[^>]*>/gi, "");

  // 移除多余的空白
  cleaned = cleaned.trim();

  return cleaned;
}

/**
 * 转换 MiniMax 响应为 OpenAI 兼容格式
 *
 * @param response - MiniMax 原始响应
 * @returns OpenAI 兼容的响应
 *
 * @example
 * // 情况 1: 纯文本响应
 * const response = {
 *   choices: [{ message: { content: "你好" } }]
 * };
 * const converted = convertMinimaxResponse(response);
 * // ➡ 原样透传
 *
 * @example
 * // 情况 2: XML 工具调用
 * const response = {
 *   choices: [{
 *     message: {
 *       content: '<tool_call><name>get_weather</name><arguments>{"city":"Beijing"}</arguments></tool_call>'
 *     }
 *   }]
 * };
 * const converted = convertMinimaxResponse(response);
 * // ➡ 转换为 OpenAI tool_calls 格式
 */
export function convertMinimaxResponse(response: MinimaxResponse): OpenAIResponse {
  const converted: OpenAIResponse = {
    id: response.id,
    object: response.object || "chat.completion",
    created: response.created,
    model: response.model,
    choices: [],
    usage: response.usage,
  };

  for (const choice of response.choices) {
    const content = choice.message.content || "";

    // 检测是否包含工具调用
    if (hasMinimaxToolCall(content)) {
      // 解析工具调用
      const parsedToolCalls = parseMinimaxToolCalls(content);

      if (parsedToolCalls.length > 0) {
        // 转换为 OpenAI 格式
        const toolCalls: OpenAIToolCall[] = parsedToolCalls.map((tc) => ({
          id: `call_${randomUUID().replace(/-/g, "").substring(0, 24)}`,
          type: "function" as const,
          function: {
            name: tc.name,
            arguments: tc.arguments,
          },
        }));

        // 移除 XML 标记后的剩余文本
        const cleanedContent = stripToolCallXML(content);

        converted.choices.push({
          index: choice.index,
          message: {
            role: choice.message.role,
            content: cleanedContent || null,
            tool_calls: toolCalls,
            name: choice.message.name,
          },
          finish_reason: "tool_calls",
        });
      } else {
        // 解析失败，返回清理后的文本
        converted.choices.push({
          index: choice.index,
          message: {
            role: choice.message.role,
            content: stripToolCallXML(content) || "抱歉，我遇到了一些技术问题。",
            name: choice.message.name,
          },
          finish_reason: choice.finish_reason,
        });
      }
    } else {
      // 纯文本响应，原样透传
      converted.choices.push({
        index: choice.index,
        message: {
          role: choice.message.role,
          content: content,
          name: choice.message.name,
        },
        finish_reason: choice.finish_reason,
      });
    }
  }

  return converted;
}

/**
 * 创建 MiniMax 适配器中间件
 *
 * 用于拦截和转换 MiniMax API 响应
 *
 * @example
 * // 在 HTTP 客户端中使用
 * const adapter = createMinimaxAdapter();
 * const response = await fetch('https://api.minimaxi.com/v1/chat/completions', options);
 * const data = await response.json();
 * const converted = adapter(data);
 */
export function createMinimaxAdapter() {
  return (response: MinimaxResponse): OpenAIResponse => {
    return convertMinimaxResponse(response);
  };
}

/**
 * 检测响应是否来自 MiniMax
 */
export function isMinimaxResponse(response: any): boolean {
  // 检测特征字段
  return (
    response && typeof response === "object" && "base_resp" in response // MiniMax 特有字段
  );
}

/**
 * 智能适配器：自动检测并转换 MiniMax 响应
 *
 * @example
 * const response = await fetch(apiUrl, options).then(r => r.json());
 * const normalized = smartAdapter(response);
 * // 如果是 MiniMax 响应，自动转换；否则原样返回
 */
export function smartAdapter(response: any): OpenAIResponse {
  if (isMinimaxResponse(response)) {
    return convertMinimaxResponse(response as MinimaxResponse);
  }
  return response;
}

/**
 * 清理 MiniMax 的思考标记
 *
 * MiniMax 有时会返回 <think>...</think> 标记
 */
export function stripThinkingTags(content: string): string {
  if (!content) return content;
  return content.replace(/<\/?think>/gi, "");
}

/**
 * 完整的 MiniMax 响应处理管道
 *
 * @example
 * const response = await fetch(apiUrl, options).then(r => r.json());
 * const processed = processMinimaxResponse(response);
 */
export function processMinimaxResponse(response: MinimaxResponse): OpenAIResponse {
  // 1. 转换工具调用格式
  const converted = convertMinimaxResponse(response);

  // 2. 清理思考标记
  for (const choice of converted.choices) {
    if (choice.message.content) {
      choice.message.content = stripThinkingTags(choice.message.content);
    }
  }

  return converted;
}
