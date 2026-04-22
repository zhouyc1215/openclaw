import {
  createReplyPrefixContext,
  createTypingCallbacks,
  logTypingFailure,
  type ClawdbotConfig,
  type RuntimeEnv,
  type ReplyPayload,
} from "openclaw/plugin-sdk";
import type { MentionTarget } from "./mention.js";
import { resolveFeishuAccount } from "./accounts.js";
import { getFeishuRuntime } from "./runtime.js";
import {
  buildMarkdownCard,
  editMessageFeishu,
  sendMessageFeishu,
  sendMarkdownCardFeishu,
  updateCardFeishu,
} from "./send.js";
import { addTypingIndicator, removeTypingIndicator, type TypingIndicatorState } from "./typing.js";

/**
 * Detect if text contains markdown elements that benefit from card rendering.
 * Used by auto render mode.
 */
function shouldUseCard(text: string): boolean {
  // Code blocks (fenced)
  if (/```[\s\S]*?```/.test(text)) {
    return true;
  }
  // Tables (at least header + separator row with |)
  if (/\|.+\|[\r\n]+\|[-:| ]+\|/.test(text)) {
    return true;
  }
  return false;
}

type FeishuReplyRenderMode = "text" | "card";

type FeishuStreamingState = {
  accumulatedText: string;
  messageId?: string;
  mode?: FeishuReplyRenderMode;
  sentMentions: boolean;
};

function resolveReplyRenderMode(params: {
  renderMode: "auto" | "raw" | "card";
  text: string;
  streaming: boolean;
}): FeishuReplyRenderMode {
  if (params.renderMode === "raw") {
    return "text";
  }
  if (params.renderMode === "card") {
    return "card";
  }
  // 伪流式优先使用卡片更新，避免后续内容出现 Markdown 时需要切换消息类型。
  return params.streaming || shouldUseCard(params.text) ? "card" : "text";
}

export type CreateFeishuReplyDispatcherParams = {
  cfg: ClawdbotConfig;
  agentId: string;
  runtime: RuntimeEnv;
  chatId: string;
  replyToMessageId?: string;
  /** Mention targets, will be auto-included in replies */
  mentionTargets?: MentionTarget[];
  /** Account ID for multi-account support */
  accountId?: string;
};

export function createFeishuReplyDispatcher(params: CreateFeishuReplyDispatcherParams) {
  const core = getFeishuRuntime();
  const { cfg, agentId, chatId, replyToMessageId, mentionTargets, accountId } = params;

  // Resolve account for config access
  const account = resolveFeishuAccount({ cfg, accountId });

  const prefixContext = createReplyPrefixContext({
    cfg,
    agentId,
  });

  // Feishu doesn't have a native typing indicator API.
  // We use message reactions as a typing indicator substitute.
  let typingState: TypingIndicatorState | null = null;

  const typingCallbacks = createTypingCallbacks({
    start: async () => {
      if (!replyToMessageId) {
        return;
      }
      typingState = await addTypingIndicator({ cfg, messageId: replyToMessageId, accountId });
      params.runtime.log?.(`feishu[${account.accountId}]: added typing indicator reaction`);
    },
    stop: async () => {
      if (!typingState) {
        return;
      }
      await removeTypingIndicator({ cfg, state: typingState, accountId });
      typingState = null;
      params.runtime.log?.(`feishu[${account.accountId}]: removed typing indicator reaction`);
    },
    onStartError: (err) => {
      logTypingFailure({
        log: (message) => params.runtime.log?.(message),
        channel: "feishu",
        action: "start",
        error: err,
      });
    },
    onStopError: (err) => {
      logTypingFailure({
        log: (message) => params.runtime.log?.(message),
        channel: "feishu",
        action: "stop",
        error: err,
      });
    },
  });

  const textChunkLimit = core.channel.text.resolveTextChunkLimit({
    cfg,
    channel: "feishu",
    defaultLimit: 4000,
  });
  const chunkMode = core.channel.text.resolveChunkMode(cfg, "feishu");
  const tableMode = core.channel.text.resolveMarkdownTableMode({
    cfg,
    channel: "feishu",
  });
  const streamingState: FeishuStreamingState = {
    accumulatedText: "",
    sentMentions: false,
  };

  const sendChunkedReply = async (delivery: {
    text: string;
    renderMode: FeishuReplyRenderMode;
  }) => {
    let isFirstChunk = true;
    if (delivery.renderMode === "card") {
      const chunks = core.channel.text.chunkTextWithMode(delivery.text, textChunkLimit, chunkMode);
      params.runtime.log?.(
        `feishu[${account.accountId}] deliver: sending ${chunks.length} card chunks to ${chatId}`,
      );
      for (const chunk of chunks) {
        await sendMarkdownCardFeishu({
          cfg,
          to: chatId,
          text: chunk,
          replyToMessageId,
          mentions: isFirstChunk ? mentionTargets : undefined,
          accountId,
        });
        isFirstChunk = false;
      }
      return;
    }

    const converted = core.channel.text.convertMarkdownTables(delivery.text, tableMode);
    const chunks = core.channel.text.chunkTextWithMode(converted, textChunkLimit, chunkMode);
    params.runtime.log?.(
      `feishu[${account.accountId}] deliver: sending ${chunks.length} text chunks to ${chatId}`,
    );
    for (const chunk of chunks) {
      await sendMessageFeishu({
        cfg,
        to: chatId,
        text: chunk,
        replyToMessageId,
        mentions: isFirstChunk ? mentionTargets : undefined,
        accountId,
      });
      isFirstChunk = false;
    }
  };

  const sendStreamingReply = async (delivery: {
    text: string;
    renderMode: FeishuReplyRenderMode;
  }) => {
    const nextAccumulatedText = `${streamingState.accumulatedText}${delivery.text}`;
    if (streamingState.messageId && nextAccumulatedText.length > textChunkLimit) {
      // 单条飞书消息超过上限时，新开一条流，避免后续更新失败。
      streamingState.accumulatedText = "";
      streamingState.messageId = undefined;
      streamingState.mode = undefined;
    }

    const nextText = `${streamingState.accumulatedText}${delivery.text}`;
    const nextMode = streamingState.mode ?? delivery.renderMode;

    if (!streamingState.messageId) {
      const result =
        nextMode === "card"
          ? await sendMarkdownCardFeishu({
              cfg,
              to: chatId,
              text: nextText,
              replyToMessageId,
              mentions: streamingState.sentMentions ? undefined : mentionTargets,
              accountId,
            })
          : await sendMessageFeishu({
              cfg,
              to: chatId,
              text: nextText,
              replyToMessageId,
              mentions: streamingState.sentMentions ? undefined : mentionTargets,
              accountId,
            });
      streamingState.accumulatedText = nextText;
      streamingState.messageId = result.messageId;
      streamingState.mode = nextMode;
      streamingState.sentMentions = true;
      params.runtime.log?.(
        `feishu[${account.accountId}] deliver: started streaming ${nextMode} message ${result.messageId}`,
      );
      return;
    }

    try {
      if (nextMode === "card") {
        await updateCardFeishu({
          cfg,
          messageId: streamingState.messageId,
          card: buildMarkdownCard(nextText),
          accountId,
        });
      } else {
        await editMessageFeishu({
          cfg,
          messageId: streamingState.messageId,
          text: nextText,
          accountId,
        });
      }
      streamingState.accumulatedText = nextText;
      streamingState.mode = nextMode;
      params.runtime.log?.(
        `feishu[${account.accountId}] deliver: updated streaming ${nextMode} message ${streamingState.messageId}`,
      );
    } catch (err) {
      params.runtime.error?.(
        `feishu[${account.accountId}] deliver: streaming update failed, falling back to new message: ${String(err)}`,
      );
      streamingState.accumulatedText = "";
      streamingState.messageId = undefined;
      streamingState.mode = undefined;
      await sendStreamingReply(delivery);
    }
  };

  const { dispatcher, replyOptions, markDispatchIdle } =
    core.channel.reply.createReplyDispatcherWithTyping({
      responsePrefix: prefixContext.responsePrefix,
      responsePrefixContextProvider: prefixContext.responsePrefixContextProvider,
      humanDelay: core.channel.reply.resolveHumanDelayConfig(cfg, agentId),
      onReplyStart: typingCallbacks.onReplyStart,
      deliver: async (payload: ReplyPayload, info) => {
        params.runtime.log?.(
          `feishu[${account.accountId}] deliver called: text=${payload.text?.slice(0, 100)}`,
        );
        const text = payload.text ?? "";
        if (!text.trim()) {
          params.runtime.log?.(`feishu[${account.accountId}] deliver: empty text, skipping`);
          return;
        }

        // Check render mode: auto (default), raw, or card
        const feishuCfg = account.config;
        const renderMode = feishuCfg?.renderMode ?? "auto";
        const streamingEnabled = feishuCfg?.streaming === true && info.kind === "block";
        const replyRenderMode = resolveReplyRenderMode({
          renderMode,
          text,
          streaming: streamingEnabled,
        });

        if (streamingEnabled) {
          await sendStreamingReply({
            text,
            renderMode: replyRenderMode,
          });
          return;
        }

        await sendChunkedReply({
          text,
          renderMode: replyRenderMode,
        });
      },
      onError: (err, info) => {
        params.runtime.error?.(
          `feishu[${account.accountId}] ${info.kind} reply failed: ${String(err)}`,
        );
        typingCallbacks.onIdle?.();
      },
      onIdle: typingCallbacks.onIdle,
    });

  return {
    dispatcher,
    replyOptions: {
      ...replyOptions,
      onModelSelected: prefixContext.onModelSelected,
    },
    markDispatchIdle,
  };
}
