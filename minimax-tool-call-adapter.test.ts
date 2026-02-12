/**
 * MiniMax Tool Call Adapter - 测试用例
 */

import { describe, it, expect } from 'vitest';
import {
  convertMinimaxResponse,
  smartAdapter,
  isMinimaxResponse,
  stripThinkingTags,
  processMinimaxResponse,
} from './minimax-tool-call-adapter';

describe('MiniMax Tool Call Adapter', () => {
  describe('情况 1: 纯文本响应', () => {
    it('should pass through normal text response', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: '你好，我是 MiniMax AI 助手。',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = convertMinimaxResponse(input);

      expect(output.choices[0].message.content).toBe('你好，我是 MiniMax AI 助手。');
      expect(output.choices[0].message.tool_calls).toBeUndefined();
      expect(output.choices[0].finish_reason).toBe('stop');
    });

    it('should handle empty content', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: '',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = convertMinimaxResponse(input);

      expect(output.choices[0].message.content).toBe('');
      expect(output.choices[0].message.tool_calls).toBeUndefined();
    });
  });

  describe('情况 2: XML 工具调用', () => {
    it('should convert standard tool_call format', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content:
                '<tool_call>\n<name>get_weather</name>\n<arguments>{"city":"Beijing"}</arguments>\n</tool_call>',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = convertMinimaxResponse(input);

      expect(output.choices[0].message.tool_calls).toBeDefined();
      expect(output.choices[0].message.tool_calls?.length).toBe(1);
      expect(output.choices[0].message.tool_calls?.[0].function.name).toBe('get_weather');
      expect(output.choices[0].message.tool_calls?.[0].function.arguments).toBe(
        '{"city":"Beijing"}'
      );
      expect(output.choices[0].message.tool_calls?.[0].type).toBe('function');
      expect(output.choices[0].message.tool_calls?.[0].id).toMatch(/^call_/);
      expect(output.choices[0].finish_reason).toBe('tool_calls');
    });

    it('should convert invoke/exec format', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content:
                '<invoke><exec>\n<cmd>date "+%H:%M:%S"</cmd>\n<timeout></timeout>\n<env></env>\n</exec></invoke>',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = convertMinimaxResponse(input);

      expect(output.choices[0].message.tool_calls).toBeDefined();
      expect(output.choices[0].message.tool_calls?.length).toBe(1);
      expect(output.choices[0].message.tool_calls?.[0].function.name).toBe('exec');

      const args = JSON.parse(output.choices[0].message.tool_calls?.[0].function.arguments || '{}');
      expect(args.cmd).toBe('date "+%H:%M:%S"');
    });

    it('should handle multiple tool calls', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content:
                '<tool_call><name>func1</name><arguments>{"a":1}</arguments></tool_call>\n' +
                '<tool_call><name>func2</name><arguments>{"b":2}</arguments></tool_call>',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = convertMinimaxResponse(input);

      expect(output.choices[0].message.tool_calls?.length).toBe(2);
      expect(output.choices[0].message.tool_calls?.[0].function.name).toBe('func1');
      expect(output.choices[0].message.tool_calls?.[1].function.name).toBe('func2');
    });

    it('should preserve text content alongside tool calls', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content:
                '让我帮你查询天气。\n<tool_call><name>get_weather</name><arguments>{"city":"Beijing"}</arguments></tool_call>',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = convertMinimaxResponse(input);

      expect(output.choices[0].message.content).toContain('让我帮你查询天气');
      expect(output.choices[0].message.content).not.toContain('<tool_call>');
      expect(output.choices[0].message.tool_calls).toBeDefined();
    });
  });

  describe('stripThinkingTags', () => {
    it('should remove <think> tags', () => {
      const input = '<think>思考过程...</think>这是回复内容。';
      const output = stripThinkingTags(input);

      expect(output).toBe('思考过程...这是回复内容。');
      expect(output).not.toContain('<think>');
    });

    it('should handle content without thinking tags', () => {
      const input = '这是普通内容。';
      const output = stripThinkingTags(input);

      expect(output).toBe(input);
    });
  });

  describe('isMinimaxResponse', () => {
    it('should detect MiniMax response', () => {
      const response = {
        id: 'test',
        choices: [],
        base_resp: { status_code: 0 },
      };

      expect(isMinimaxResponse(response)).toBe(true);
    });

    it('should not detect OpenAI response', () => {
      const response = {
        id: 'test',
        choices: [],
        object: 'chat.completion',
      };

      expect(isMinimaxResponse(response)).toBe(false);
    });
  });

  describe('smartAdapter', () => {
    it('should convert MiniMax response', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        base_resp: { status_code: 0 },
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: '你好',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = smartAdapter(input);

      expect(output.choices[0].message.content).toBe('你好');
    });

    it('should pass through non-MiniMax response', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'gpt-4',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: 'Hello',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = smartAdapter(input);

      expect(output).toBe(input);
    });
  });

  describe('processMinimaxResponse', () => {
    it('should convert tool calls and strip thinking tags', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content:
                '<think>我需要查询天气</think><tool_call><name>get_weather</name><arguments>{"city":"Beijing"}</arguments></tool_call>',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = processMinimaxResponse(input);

      expect(output.choices[0].message.content).not.toContain('<think>');
      expect(output.choices[0].message.tool_calls).toBeDefined();
      expect(output.choices[0].message.tool_calls?.[0].function.name).toBe('get_weather');
    });
  });

  describe('边界情况', () => {
    it('should handle malformed XML gracefully', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: '<tool_call><name>func</name>',
            },
            finish_reason: 'stop',
          },
        ],
      };

      const output = convertMinimaxResponse(input);

      // 应该清理掉格式错误的 XML，返回友好消息
      expect(output.choices[0].message.content).toBeTruthy();
      expect(output.choices[0].message.tool_calls).toBeUndefined();
    });

    it('should handle null content', () => {
      const input = {
        id: 'test-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'MiniMax-M2.1',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: null as any,
            },
            finish_reason: 'stop',
          },
        ],
      };

      expect(() => convertMinimaxResponse(input)).not.toThrow();
    });
  });
});
