import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  sendMessageFeishu,
  sendMarkdownCardFeishu,
  editMessageFeishu,
  updateCardFeishu,
  buildMarkdownCard,
  resolveFeishuAccount,
} = vi.hoisted(() => ({
  sendMessageFeishu: vi.fn(),
  sendMarkdownCardFeishu: vi.fn(),
  editMessageFeishu: vi.fn(),
  updateCardFeishu: vi.fn(),
  buildMarkdownCard: vi.fn((text: string) => ({
    config: { wide_screen_mode: true },
    elements: [{ tag: "markdown", content: text }],
  })),
  resolveFeishuAccount: vi.fn(),
}));

function createFakeReplyDispatcherWithTyping(options: {
  deliver: (
    payload: { text?: string },
    info: { kind: "tool" | "block" | "final" },
  ) => Promise<void>;
}) {
  let queue = Promise.resolve();
  const counts = { tool: 0, block: 0, final: 0 };
  return {
    dispatcher: {
      sendToolResult(payload: { text?: string }) {
        counts.tool += 1;
        queue = queue.then(() => options.deliver(payload, { kind: "tool" }));
        return true;
      },
      sendBlockReply(payload: { text?: string }) {
        counts.block += 1;
        queue = queue.then(() => options.deliver(payload, { kind: "block" }));
        return true;
      },
      sendFinalReply(payload: { text?: string }) {
        counts.final += 1;
        queue = queue.then(() => options.deliver(payload, { kind: "final" }));
        return true;
      },
      waitForIdle() {
        return queue;
      },
      getQueuedCounts() {
        return { ...counts };
      },
    },
    replyOptions: {},
    markDispatchIdle: vi.fn(),
  };
}

vi.mock("openclaw/plugin-sdk", () => ({
  createReplyPrefixContext: () => ({
    responsePrefix: undefined,
    responsePrefixContextProvider: undefined,
    onModelSelected: vi.fn(),
  }),
  createTypingCallbacks: () => ({
    onReplyStart: undefined,
    onIdle: undefined,
  }),
  logTypingFailure: vi.fn(),
}));

vi.mock("./accounts.js", () => ({
  resolveFeishuAccount,
}));

vi.mock("./runtime.js", () => ({
  getFeishuRuntime: () => ({
    channel: {
      text: {
        resolveTextChunkLimit: () => 4000,
        resolveChunkMode: () => "length",
        resolveMarkdownTableMode: () => "native",
        chunkTextWithMode: (text: string) => [text],
        convertMarkdownTables: (text: string) => text,
      },
      reply: {
        createReplyDispatcherWithTyping: createFakeReplyDispatcherWithTyping,
        resolveHumanDelayConfig: () => undefined,
      },
    },
  }),
}));

vi.mock("./send.js", () => ({
  buildMarkdownCard,
  editMessageFeishu,
  sendMessageFeishu,
  sendMarkdownCardFeishu,
  updateCardFeishu,
}));

vi.mock("./typing.js", () => ({
  addTypingIndicator: vi.fn(),
  removeTypingIndicator: vi.fn(),
}));

import { createFeishuReplyDispatcher } from "./reply-dispatcher.js";

describe("createFeishuReplyDispatcher", () => {
  beforeEach(() => {
    sendMessageFeishu.mockReset();
    sendMarkdownCardFeishu.mockReset();
    editMessageFeishu.mockReset();
    updateCardFeishu.mockReset();
    buildMarkdownCard.mockClear();
    resolveFeishuAccount.mockReset();
    resolveFeishuAccount.mockReturnValue({
      accountId: "default",
      configured: true,
      config: {
        renderMode: "raw",
      },
    });
    sendMessageFeishu.mockResolvedValue({
      messageId: "msg-1",
      chatId: "chat-1",
    });
    sendMarkdownCardFeishu.mockResolvedValue({
      messageId: "card-1",
      chatId: "chat-1",
    });
    editMessageFeishu.mockResolvedValue(undefined);
    updateCardFeishu.mockResolvedValue(undefined);
  });

  it("streaming=true 时块回复复用同一条文本消息并持续更新", async () => {
    resolveFeishuAccount.mockReturnValue({
      accountId: "default",
      configured: true,
      config: {
        streaming: true,
        renderMode: "raw",
      },
    });

    const runtime = {
      log: vi.fn(),
      error: vi.fn(),
    };

    const { dispatcher } = createFeishuReplyDispatcher({
      cfg: {} as never,
      agentId: "finance-tools",
      runtime: runtime as never,
      chatId: "chat-1",
      replyToMessageId: "reply-1",
      accountId: "default",
    });

    dispatcher.sendBlockReply({ text: "Hello" });
    dispatcher.sendBlockReply({ text: " world" });
    await dispatcher.waitForIdle();

    expect(sendMessageFeishu).toHaveBeenCalledTimes(1);
    expect(sendMessageFeishu).toHaveBeenCalledWith(
      expect.objectContaining({
        text: "Hello",
      }),
    );
    expect(editMessageFeishu).toHaveBeenCalledTimes(1);
    expect(editMessageFeishu).toHaveBeenCalledWith({
      cfg: {},
      messageId: "msg-1",
      text: "Hello world",
      accountId: "default",
    });
    expect(sendMarkdownCardFeishu).not.toHaveBeenCalled();
    expect(updateCardFeishu).not.toHaveBeenCalled();
  });

  it("streaming=false 时保持原来的分块多消息发送", async () => {
    const runtime = {
      log: vi.fn(),
      error: vi.fn(),
    };

    const { dispatcher } = createFeishuReplyDispatcher({
      cfg: {} as never,
      agentId: "finance-tools",
      runtime: runtime as never,
      chatId: "chat-1",
      replyToMessageId: "reply-1",
      accountId: "default",
    });

    dispatcher.sendBlockReply({ text: "Hello" });
    dispatcher.sendBlockReply({ text: " world" });
    await dispatcher.waitForIdle();

    expect(sendMessageFeishu).toHaveBeenCalledTimes(2);
    expect(editMessageFeishu).not.toHaveBeenCalled();
  });

  it("streaming=true 且 renderMode=auto 时优先走卡片更新链路", async () => {
    resolveFeishuAccount.mockReturnValue({
      accountId: "default",
      configured: true,
      config: {
        streaming: true,
        renderMode: "auto",
      },
    });

    const runtime = {
      log: vi.fn(),
      error: vi.fn(),
    };

    const { dispatcher } = createFeishuReplyDispatcher({
      cfg: {} as never,
      agentId: "finance-tools",
      runtime: runtime as never,
      chatId: "chat-1",
      replyToMessageId: "reply-1",
      accountId: "default",
    });

    dispatcher.sendBlockReply({ text: "```ts\nconst x = 1;\n```" });
    dispatcher.sendBlockReply({ text: "\nconsole.log(x);" });
    await dispatcher.waitForIdle();

    expect(sendMarkdownCardFeishu).toHaveBeenCalledTimes(1);
    expect(updateCardFeishu).toHaveBeenCalledTimes(1);
    expect(buildMarkdownCard).toHaveBeenCalledWith("```ts\nconst x = 1;\n```\nconsole.log(x);");
    expect(sendMessageFeishu).not.toHaveBeenCalled();
  });
});
