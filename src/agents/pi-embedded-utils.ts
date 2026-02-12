import type { AssistantMessage } from "@mariozechner/pi-ai";
import { stripReasoningTagsFromText } from "../shared/text/reasoning-tags.js";
import { sanitizeUserFacingText } from "./pi-embedded-helpers.js";
import { formatToolDetail, resolveToolDisplay } from "./tool-display.js";

/**
 * Strip malformed Minimax tool invocations that leak into text content.
 * Minimax sometimes embeds tool calls as XML in text blocks instead of
 * proper structured tool calls. This removes:
 * - <invoke name="...">...</invoke> blocks
 * - </minimax:tool_call> closing tags
 */
export function stripMinimaxToolCallXml(text: string): string {
  if (!text) {
    return text;
  }
  if (!/minimax:tool_call/i.test(text)) {
    return text;
  }

  // Remove <invoke ...>...</invoke> blocks (non-greedy to handle multiple).
  let cleaned = text.replace(/<invoke\b[^>]*>[\s\S]*?<\/invoke>/gi, "");

  // Remove stray minimax tool tags.
  cleaned = cleaned.replace(/<\/?minimax:tool_call>/gi, "");

  return cleaned;
}

/**
 * Strip downgraded tool call text representations that leak into text content.
 * When replaying history to Gemini, tool calls without `thought_signature` are
 * downgraded to text blocks like `[Tool Call: name (ID: ...)]`. These should
 * not be shown to users.
 */
export function stripDowngradedToolCallText(text: string): string {
  if (!text) {
    return text;
  }
  if (!/\[Tool (?:Call|Result)/i.test(text)) {
    return text;
  }

  const consumeJsonish = (
    input: string,
    start: number,
    options?: { allowLeadingNewlines?: boolean },
  ): number | null => {
    const { allowLeadingNewlines = false } = options ?? {};
    let index = start;
    while (index < input.length) {
      const ch = input[index];
      if (ch === " " || ch === "\t") {
        index += 1;
        continue;
      }
      if (allowLeadingNewlines && (ch === "\n" || ch === "\r")) {
        index += 1;
        continue;
      }
      break;
    }
    if (index >= input.length) {
      return null;
    }

    const startChar = input[index];
    if (startChar === "{" || startChar === "[") {
      let depth = 0;
      let inString = false;
      let escape = false;
      for (let i = index; i < input.length; i += 1) {
        const ch = input[i];
        if (inString) {
          if (escape) {
            escape = false;
          } else if (ch === "\\") {
            escape = true;
          } else if (ch === '"') {
            inString = false;
          }
          continue;
        }
        if (ch === '"') {
          inString = true;
          continue;
        }
        if (ch === "{" || ch === "[") {
          depth += 1;
          continue;
        }
        if (ch === "}" || ch === "]") {
          depth -= 1;
          if (depth === 0) {
            return i + 1;
          }
        }
      }
      return null;
    }

    if (startChar === '"') {
      let escape = false;
      for (let i = index + 1; i < input.length; i += 1) {
        const ch = input[i];
        if (escape) {
          escape = false;
          continue;
        }
        if (ch === "\\") {
          escape = true;
          continue;
        }
        if (ch === '"') {
          return i + 1;
        }
      }
      return null;
    }

    let end = index;
    while (end < input.length && input[end] !== "\n" && input[end] !== "\r") {
      end += 1;
    }
    return end;
  };

  const stripToolCalls = (input: string): string => {
    const markerRe = /\[Tool Call:[^\]]*\]/gi;
    let result = "";
    let cursor = 0;
    for (const match of input.matchAll(markerRe)) {
      const start = match.index ?? 0;
      if (start < cursor) {
        continue;
      }
      result += input.slice(cursor, start);
      let index = start + match[0].length;
      while (index < input.length && (input[index] === " " || input[index] === "\t")) {
        index += 1;
      }
      if (input[index] === "\r") {
        index += 1;
        if (input[index] === "\n") {
          index += 1;
        }
      } else if (input[index] === "\n") {
        index += 1;
      }
      while (index < input.length && (input[index] === " " || input[index] === "\t")) {
        index += 1;
      }
      if (input.slice(index, index + 9).toLowerCase() === "arguments") {
        index += 9;
        if (input[index] === ":") {
          index += 1;
        }
        if (input[index] === " ") {
          index += 1;
        }
        const end = consumeJsonish(input, index, { allowLeadingNewlines: true });
        if (end !== null) {
          index = end;
        }
      }
      if (
        (input[index] === "\n" || input[index] === "\r") &&
        (result.endsWith("\n") || result.endsWith("\r") || result.length === 0)
      ) {
        if (input[index] === "\r") {
          index += 1;
        }
        if (input[index] === "\n") {
          index += 1;
        }
      }
      cursor = index;
    }
    result += input.slice(cursor);
    return result;
  };

  // Remove [Tool Call: name (ID: ...)] blocks and their Arguments.
  let cleaned = stripToolCalls(text);

  // Remove [Tool Result for ID ...] blocks and their content.
  cleaned = cleaned.replace(/\[Tool Result for ID[^\]]*\]\n?[\s\S]*?(?=\n*\[Tool |\n*$)/gi, "");

  return cleaned.trim();
}

/**
 * Strip thinking tags and their content from text.
 * This is a safety net for cases where the model outputs <think> tags
 * that slip through other filtering mechanisms.
 */
export function stripThinkingTagsFromText(text: string): string {
  return stripReasoningTagsFromText(text, { mode: "strict", trim: "both" });
}

export function extractAssistantText(msg: AssistantMessage): string {
  const isTextBlock = (block: unknown): block is { type: "text"; text: string } => {
    if (!block || typeof block !== "object") {
      return false;
    }
    const rec = block as Record<string, unknown>;
    return rec.type === "text" && typeof rec.text === "string";
  };

  const blocks = Array.isArray(msg.content)
    ? msg.content
        .filter(isTextBlock)
        .map((c) =>
          stripThinkingTagsFromText(
            stripDowngradedToolCallText(stripMinimaxToolCallXml(c.text)),
          ).trim(),
        )
        .filter(Boolean)
    : [];
  const extracted = blocks.join("\n").trim();
  return sanitizeUserFacingText(extracted);
}

export function extractAssistantThinking(msg: AssistantMessage): string {
  if (!Array.isArray(msg.content)) {
    return "";
  }
  const blocks = msg.content
    .map((block) => {
      if (!block || typeof block !== "object") {
        return "";
      }
      const record = block as unknown as Record<string, unknown>;
      if (record.type === "thinking" && typeof record.thinking === "string") {
        return record.thinking.trim();
      }
      return "";
    })
    .filter(Boolean);
  return blocks.join("\n").trim();
}

export function formatReasoningMessage(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return "";
  }
  // Show reasoning in italics (cursive) for markdown-friendly surfaces (Discord, etc.).
  // Keep the plain "Reasoning:" prefix so existing parsing/detection keeps working.
  // Note: Underscore markdown cannot span multiple lines on Telegram, so we wrap
  // each non-empty line separately.
  const italicLines = trimmed
    .split("\n")
    .map((line) => (line ? `_${line}_` : line))
    .join("\n");
  return `Reasoning:\n${italicLines}`;
}

type ThinkTaggedSplitBlock =
  | { type: "thinking"; thinking: string }
  | { type: "text"; text: string };

export function splitThinkingTaggedText(text: string): ThinkTaggedSplitBlock[] | null {
  const trimmedStart = text.trimStart();
  // Avoid false positives: only treat it as structured thinking when it begins
  // with a think tag (common for local/OpenAI-compat providers that emulate
  // reasoning blocks via tags).
  if (!trimmedStart.startsWith("<")) {
    return null;
  }
  const openRe = /<\s*(?:think(?:ing)?|thought|antthinking)\s*>/i;
  const closeRe = /<\s*\/\s*(?:think(?:ing)?|thought|antthinking)\s*>/i;
  if (!openRe.test(trimmedStart)) {
    return null;
  }
  if (!closeRe.test(text)) {
    return null;
  }

  const scanRe = /<\s*(\/?)\s*(?:think(?:ing)?|thought|antthinking)\s*>/gi;
  let inThinking = false;
  let cursor = 0;
  let thinkingStart = 0;
  const blocks: ThinkTaggedSplitBlock[] = [];

  const pushText = (value: string) => {
    if (!value) {
      return;
    }
    blocks.push({ type: "text", text: value });
  };
  const pushThinking = (value: string) => {
    const cleaned = value.trim();
    if (!cleaned) {
      return;
    }
    blocks.push({ type: "thinking", thinking: cleaned });
  };

  for (const match of text.matchAll(scanRe)) {
    const index = match.index ?? 0;
    const isClose = Boolean(match[1]?.includes("/"));

    if (!inThinking && !isClose) {
      pushText(text.slice(cursor, index));
      thinkingStart = index + match[0].length;
      inThinking = true;
      continue;
    }

    if (inThinking && isClose) {
      pushThinking(text.slice(thinkingStart, index));
      cursor = index + match[0].length;
      inThinking = false;
    }
  }

  if (inThinking) {
    return null;
  }
  pushText(text.slice(cursor));

  const hasThinking = blocks.some((b) => b.type === "thinking");
  if (!hasThinking) {
    return null;
  }
  return blocks;
}

export function promoteThinkingTagsToBlocks(message: AssistantMessage): void {
  if (!Array.isArray(message.content)) {
    return;
  }
  const hasThinkingBlock = message.content.some((block) => block.type === "thinking");
  if (hasThinkingBlock) {
    return;
  }

  const next: AssistantMessage["content"] = [];
  let changed = false;

  for (const block of message.content) {
    if (block.type !== "text") {
      next.push(block);
      continue;
    }
    const split = splitThinkingTaggedText(block.text);
    if (!split) {
      next.push(block);
      continue;
    }
    changed = true;
    for (const part of split) {
      if (part.type === "thinking") {
        next.push({ type: "thinking", thinking: part.thinking });
      } else if (part.type === "text") {
        const cleaned = part.text.trimStart();
        if (cleaned) {
          next.push({ type: "text", text: cleaned });
        }
      }
    }
  }

  if (!changed) {
    return;
  }
  message.content = next;
}

export function extractThinkingFromTaggedText(text: string): string {
  if (!text) {
    return "";
  }
  const scanRe = /<\s*(\/?)\s*(?:think(?:ing)?|thought|antthinking)\s*>/gi;
  let result = "";
  let lastIndex = 0;
  let inThinking = false;
  for (const match of text.matchAll(scanRe)) {
    const idx = match.index ?? 0;
    if (inThinking) {
      result += text.slice(lastIndex, idx);
    }
    const isClose = match[1] === "/";
    inThinking = !isClose;
    lastIndex = idx + match[0].length;
  }
  return result.trim();
}

export function extractThinkingFromTaggedStream(text: string): string {
  if (!text) {
    return "";
  }
  const closed = extractThinkingFromTaggedText(text);
  if (closed) {
    return closed;
  }

  const openRe = /<\s*(?:think(?:ing)?|thought|antthinking)\s*>/gi;
  const closeRe = /<\s*\/\s*(?:think(?:ing)?|thought|antthinking)\s*>/gi;
  const openMatches = [...text.matchAll(openRe)];
  if (openMatches.length === 0) {
    return "";
  }
  const closeMatches = [...text.matchAll(closeRe)];
  const lastOpen = openMatches[openMatches.length - 1];
  const lastClose = closeMatches[closeMatches.length - 1];
  if (lastClose && (lastClose.index ?? -1) > (lastOpen.index ?? -1)) {
    return closed;
  }
  const start = (lastOpen.index ?? 0) + lastOpen[0].length;
  return text.slice(start).trim();
}

export function inferToolMetaFromArgs(toolName: string, args: unknown): string | undefined {
  const display = resolveToolDisplay({ name: toolName, args });
  return formatToolDetail(display);
}

/**
 * 解析后的工具调用信息
 */
interface ParsedToolCall {
  name: string;
  arguments: Record<string, any>;
}

/**
 * 检测内容是否包含 MiniMax XML 工具调用
 */
function hasMinimaxXmlToolCall(text: string): boolean {
  if (!text) {
    return false;
  }

  // 检测多种可能的 XML 格式
  return (
    /<tool_call\b/i.test(text) || /<invoke\b/i.test(text) || /<minimax:tool_call\b/i.test(text)
  );
}

/**
 * 从 XML 内容中提取工具调用信息
 *
 * 支持的格式:
 * 1. <tool_call><name>func</name><arguments>{...}</arguments></tool_call>
 * 2. <invoke><exec><cmd>...</cmd></exec></invoke>
 * 3. <minimax:tool_call>...</minimax:tool_call>
 */
function parseMinimaxXmlToolCalls(content: string): ParsedToolCall[] {
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
      let args: Record<string, any> = {};

      if (argsMatch) {
        const argsStr = argsMatch[1].trim();
        try {
          args = JSON.parse(argsStr);
        } catch {
          // 如果不是 JSON,尝试作为单个参数
          args = { value: argsStr };
        }
      }

      toolCalls.push({ name, arguments: args });
    }
  }

  // 格式 2: invoke/exec 格式 (MiniMax 特有)
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
          const args: Record<string, any> = {
            cmd: cmdMatch[1].trim(),
          };

          if (timeoutMatch && timeoutMatch[1].trim()) {
            args.timeout = timeoutMatch[1].trim();
          }
          if (envMatch && envMatch[1].trim()) {
            args.env = envMatch[1].trim();
          }

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
          toolCalls.push({
            name: "read",
            arguments: {
              path: pathMatch[1].trim(),
            },
          });
        }
      }

      // 检测 write 类型
      if (/<write[^>]*>/i.test(invokeContent)) {
        const pathMatch = invokeContent.match(/<path>([^<]+)<\/path>/i);
        const contentMatch = invokeContent.match(/<content>([\s\S]*?)<\/content>/i);

        if (pathMatch) {
          toolCalls.push({
            name: "write",
            arguments: {
              path: pathMatch[1].trim(),
              content: contentMatch ? contentMatch[1].trim() : "",
            },
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
function stripXmlToolCallTags(content: string): string {
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
 * 转换 MiniMax XML 工具调用为标准 ToolCall 对象
 *
 * 在 handleMessageEnd 中调用此函数,在 AssistantMessage 被处理之前拦截并转换
 *
 * @param message - AssistantMessage 对象
 * @returns 是否进行了转换
 */
export function convertMinimaxXmlToolCalls(message: AssistantMessage): boolean {
  if (!Array.isArray(message.content)) {
    return false;
  }

  let converted = false;
  const newContent: (typeof message.content)[number][] = [];

  for (const block of message.content) {
    if (!block || typeof block !== "object") {
      newContent.push(block);
      continue;
    }

    const record = block as unknown as Record<string, unknown>;

    // 只处理 TextContent
    if (record.type === "text" && typeof record.text === "string") {
      const text = record.text;

      // 检测是否包含 XML 工具调用
      if (hasMinimaxXmlToolCall(text)) {
        // 解析工具调用
        const parsedToolCalls = parseMinimaxXmlToolCalls(text);

        if (parsedToolCalls.length > 0) {
          // 转换为 ToolCall 对象
          for (const tc of parsedToolCalls) {
            const toolCall = {
              type: "toolCall" as const,
              id: `call_${Math.random().toString(36).substring(2, 26)}`,
              name: tc.name,
              arguments: tc.arguments,
            };
            newContent.push(toolCall as any);
          }

          // 移除 XML 标记后的剩余文本
          const cleanedText = stripXmlToolCallTags(text);
          if (cleanedText) {
            newContent.push({
              type: "text",
              text: cleanedText,
            } as any);
          }

          converted = true;
        } else {
          // 解析失败,保留原文本但移除 XML
          const cleanedText = stripXmlToolCallTags(text);
          newContent.push({
            type: "text",
            text: cleanedText || "抱歉,我遇到了一些技术问题。",
          } as any);
          converted = true;
        }
      } else {
        // 不包含 XML 工具调用,原样保留
        newContent.push(block);
      }
    } else {
      // 非 TextContent,原样保留
      newContent.push(block);
    }
  }

  if (converted) {
    message.content = newContent as any;
    // 更新 stopReason 为 toolUse
    if (newContent.some((c: any) => c.type === "toolCall")) {
      message.stopReason = "toolUse";
    }
  }

  return converted;
}
