# Pi Agent Core 架构深度解析

## 核心设计哲学：LLM + Tools + Loop

Pi Agent Core 是一个极简主义的 AI Agent 运行时框架，遵循 "LLM + Tools + Loop" 的核心设计哲学。这个设计将复杂的 AI Agent 系统简化为三个基本组件的协同工作。

## 一、核心组件概览

### 1. LLM（Large Language Model）

- **角色**: 推理引擎和决策中心
- **职责**: 理解用户意图、规划任务、生成响应、决定工具调用
- **实现**: 通过 `@mariozechner/pi-ai` 包提供统一的模型接口

### 2. Tools（工具集）

- **角色**: Agent 的能力扩展
- **职责**: 执行具体操作（文件读写、命令执行、网络请求等）
- **实现**: 通过 `AgentTool` 接口定义，支持动态注册和执行

### 3. Loop（执行循环）

- **角色**: 协调器和控制流
- **职责**: 管理 LLM 和 Tools 的交互，处理流式输出，管理会话状态
- **实现**: 通过 `AgentSession` 和事件订阅机制实现

## 二、代码层面的实现

### 2.1 LLM 层实现

#### 模型抽象

```typescript
// 模型定义（来自配置）
const safeModel = {
  ...params.model,
  input: params.model.input ?? ["text"], // 支持的输入类型
  provider: "anthropic", // 提供商
  api: "openai-completions", // API 类型
  contextWindow: 200000, // 上下文窗口
  maxTokens: 8192, // 最大输出
};
```

#### 流式处理

```typescript
// 使用 streamSimple 进行流式推理
activeSession.agent.streamFn = streamSimple;

// 支持缓存追踪和日志记录
if (cacheTrace) {
  activeSession.agent.streamFn = cacheTrace.wrapStreamFn(activeSession.agent.streamFn);
}
```

### 2.2 Tools 层实现

#### 工具定义接口

```typescript
// AgentTool 接口（来自 @mariozechner/pi-agent-core）
interface AgentTool<TParams, TResult> {
  name: string; // 工具名称
  label?: string; // 显示标签
  description: string; // 工具描述（LLM 可见）
  parameters: TSchema; // 参数 schema（TypeBox）
  execute: (
    // 执行函数
    toolCallId: string,
    params: TParams,
    signal?: AbortSignal,
    onUpdate?: AgentToolUpdateCallback<TResult>,
  ) => Promise<AgentToolResult<TResult>>;
}
```

#### 工具适配器

```typescript
// 将 AgentTool 转换为 ToolDefinition（pi-coding-agent 格式）
export function toToolDefinitions(tools: AnyAgentTool[], guard?: ToolRetryGuard): ToolDefinition[] {
  return tools.map((tool) => {
    const name = tool.name || "tool";
    const normalizedName = normalizeToolName(name);

    return {
      name,
      label: tool.label ?? name,
      description: tool.description,
      parameters: tool.parameters,
      execute: async (toolCallId, params, signal, onUpdate, _ctx) => {
        // 1. 检查重试保护（防止无限循环）
        if (guard) {
          const blockCheck = guard.shouldBlockTool(normalizedName, params);
          if (blockCheck.blocked) {
            return jsonResult({
              status: "error",
              tool: normalizedName,
              error: "Tool blocked by retry guard",
              blocked: true,
            });
          }
        }

        // 2. 执行工具
        try {
          const result = await tool.execute(toolCallId, params, signal, onUpdate);
          return result;
        } catch (err) {
          // 3. 记录失败（用于重试保护）
          if (guard) {
            guard.recordFailure({
              toolName: normalizedName,
              timestamp: Date.now(),
              errorMessage: err.message,
              params,
            });
          }
          return jsonResult({
            status: "error",
            tool: normalizedName,
            error: err.message,
          });
        }
      },
    };
  });
}
```

#### 工具创建示例

```typescript
// 创建 OpenClaw 工具集
const tools = createOpenClawCodingTools({
  exec: { elevated: params.bashElevated },
  sandbox,
  messageProvider: params.messageChannel,
  sessionKey: params.sessionKey,
  agentDir,
  workspaceDir: effectiveWorkspace,
  config: params.config,
  abortSignal: runAbortController.signal,
  modelProvider: safeModel.provider,
  modelId: params.modelId,
  modelHasVision,
  // ... 更多配置
});

// 工具包括：
// - 文件操作：read, write, edit
// - 命令执行：exec, bash
// - 浏览器控制：browser
// - 消息发送：message
// - 会话管理：sessions
// - 定时任务：cron
// - 网络请求：web_search, web_fetch
// - 飞书集成：feishu_doc, feishu_wiki, feishu_drive, feishu_bitable
```

#### 工具重试保护

```typescript
// 防止工具无限循环调用
const toolRetryGuard = new ToolRetryGuard({
  maxConsecutiveFailures: 3, // 最大连续失败次数
  failureWindowMs: 5 * 60 * 1000, // 5分钟窗口
  checkParamSimilarity: true, // 检查参数相似度
});

// 工具执行前检查
const blockCheck = guard.shouldBlockTool(toolName, params);
if (blockCheck.blocked) {
  // 阻止执行，返回错误
  return {
    status: "error",
    error: `Tool blocked: ${blockCheck.reason}`,
    blocked: true,
  };
}
```

### 2.3 Loop 层实现

#### Agent Session 创建

```typescript
// 创建 Agent Session（核心运行时）
const { session } = await createAgentSession({
  cwd: resolvedWorkspace, // 工作目录
  agentDir, // Agent 配置目录
  authStorage: params.authStorage, // 认证存储
  modelRegistry: params.modelRegistry, // 模型注册表
  model: safeModel, // 模型配置
  thinkingLevel: mapThinkingLevel(params.thinkLevel), // 思考级别
  tools: builtInTools, // 内置工具
  customTools: allCustomTools, // 自定义工具
  sessionManager, // 会话管理器
  settingsManager, // 设置管理器
});
```

#### 主执行循环

```typescript
// 1. 准备阶段
// - 加载会话历史
// - 验证消息格式
// - 限制历史长度
const validated = validateAnthropicTurns(prior);
const limited = limitHistoryTurns(validated, historyLimit);
activeSession.agent.replaceMessages(limited);

// 2. 图像处理（Vision 模型）
const imageResult = await detectAndLoadPromptImages({
  prompt: effectivePrompt,
  workspaceDir: effectiveWorkspace,
  model: params.model,
  existingImages: params.images,
  historyMessages: activeSession.messages,
  maxBytes: MAX_IMAGE_BYTES,
  sandboxRoot: sandbox?.enabled ? sandbox.workspaceDir : undefined,
});

// 3. 执行 Prompt（核心循环入口）
if (imageResult.images.length > 0) {
  await abortable(
    activeSession.prompt(effectivePrompt, {
      images: imageResult.images,
    }),
  );
} else {
  await abortable(activeSession.prompt(effectivePrompt));
}

// 4. 等待压缩重试（如果需要）
await waitForCompactionRetry();

// 5. 获取结果
messagesSnapshot = activeSession.messages.slice();
sessionIdUsed = activeSession.sessionId;
```

#### 事件订阅机制

```typescript
// 订阅 Agent 事件（实现流式输出和工具调用监控）
const subscription = subscribeEmbeddedPiSession({
  session: activeSession,
  runId: params.runId,
  verboseLevel: params.verboseLevel,
  reasoningMode: params.reasoningLevel ?? "off",
  toolResultFormat: params.toolResultFormat,
  shouldEmitToolResult: params.shouldEmitToolResult,
  shouldEmitToolOutput: params.shouldEmitToolOutput,
  onToolResult: params.onToolResult, // 工具结果回调
  onReasoningStream: params.onReasoningStream, // 推理流回调
  onBlockReply: params.onBlockReply, // 块回复回调
  onBlockReplyFlush: params.onBlockReplyFlush, // 块刷新回调
  blockReplyBreak: params.blockReplyBreak, // 块分隔符
  blockReplyChunking: params.blockReplyChunking, // 块分块策略
  onPartialReply: params.onPartialReply, // 部分回复回调
  onAssistantMessageStart: params.onAssistantMessageStart, // 消息开始回调
  onAgentEvent: params.onAgentEvent, // Agent 事件回调
  enforceFinalTag: params.enforceFinalTag, // 强制最终标签
});

// 订阅返回的控制接口
const {
  assistantTexts, // 助手文本累积
  toolMetas, // 工具元数据
  unsubscribe, // 取消订阅
  waitForCompactionRetry, // 等待压缩重试
  getMessagingToolSentTexts, // 获取消息工具发送的文本
  getMessagingToolSentTargets, // 获取消息工具发送的目标
  didSendViaMessagingTool, // 是否通过消息工具发送
  getLastToolError, // 获取最后的工具错误
  getUsageTotals, // 获取使用统计
  getCompactionCount, // 获取压缩次数
} = subscription;
```

#### 中止控制

```typescript
// 超时控制
const abortTimer = setTimeout(
  () => {
    log.warn(`embedded run timeout: runId=${params.runId}`);
    abortRun(true); // 中止运行
  },
  Math.max(1, params.timeoutMs),
);

// 手动中止
const queueHandle: EmbeddedPiQueueHandle = {
  queueMessage: async (text: string) => {
    await activeSession.steer(text); // 注入新消息
  },
  isStreaming: () => activeSession.isStreaming,
  isCompacting: () => subscription.isCompacting(),
  abort: abortRun, // 中止函数
};

// 外部信号中止
if (params.abortSignal) {
  params.abortSignal.addEventListener("abort", onAbort, { once: true });
}
```

## 三、执行流程详解

### 3.1 完整的执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                    1. 初始化阶段                              │
├─────────────────────────────────────────────────────────────┤
│ • 解析配置和参数                                              │
│ • 创建工作目录和沙箱环境                                       │
│ • 加载技能和引导文件                                          │
│ • 创建工具集（内置 + 自定义 + 插件）                           │
│ • 初始化模型和认证                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    2. Session 创建                           │
├─────────────────────────────────────────────────────────────┤
│ • 获取会话锁（防止并发写入）                                   │
│ • 修复会话文件（如果损坏）                                     │
│ • 打开 SessionManager                                        │
│ • 创建 SettingsManager                                       │
│ • 创建 AgentSession（核心运行时）                             │
│ • 应用系统提示词覆盖                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    3. 历史处理                               │
├─────────────────────────────────────────────────────────────┤
│ • 加载会话历史消息                                            │
│ • 清理和验证消息格式                                          │
│   - sanitizeSessionHistory()                                │
│   - validateGeminiTurns()                                   │
│   - validateAnthropicTurns()                                │
│ • 限制历史长度（DM 策略）                                      │
│ • 注入历史图像（Vision 模型）                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    4. Prompt 执行（核心循环）                 │
├─────────────────────────────────────────────────────────────┤
│ • 运行 before_agent_start 钩子                               │
│ • 检测和加载图像（Vision 模型）                                │
│ • 调用 activeSession.prompt()                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │         LLM 推理和工具调用循环                        │   │
│   ├─────────────────────────────────────────────────────┤   │
│   │ 1. LLM 生成响应（流式输出）                           │   │
│   │    ↓                                                 │   │
│   │ 2. 检测工具调用请求                                   │   │
│   │    ↓                                                 │   │
│   │ 3. 执行工具（并行或串行）                             │   │
│   │    ↓                                                 │   │
│   │ 4. 将工具结果注入上下文                               │   │
│   │    ↓                                                 │   │
│   │ 5. LLM 继续生成（基于工具结果）                        │   │
│   │    ↓                                                 │   │
│   │ 6. 重复 2-5 直到：                                    │   │
│   │    • LLM 生成最终响应（无工具调用）                    │   │
│   │    • 达到最大迭代次数                                 │   │
│   │    • 超时或中止                                       │   │
│   └─────────────────────────────────────────────────────┘   │
│ • 等待压缩重试（如果触发）                                     │
│ • 运行 agent_end 钩子                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    5. 结果收集                               │
├─────────────────────────────────────────────────────────────┤
│ • 获取消息快照                                                │
│ • 收集助手文本                                                │
│ • 收集工具元数据                                              │
│ • 收集使用统计                                                │
│ • 检测客户端工具调用                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    6. 清理阶段                               │
├─────────────────────────────────────────────────────────────┤
│ • 刷新待处理的工具结果                                         │
│ • 释放 Session                                               │
│ • 释放会话锁                                                  │
│ • 恢复工作目录                                                │
│ • 恢复环境变量                                                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 LLM + Tools 交互细节

#### 工具调用流程

```typescript
// LLM 生成工具调用请求（JSON 格式）
{
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lq9",
      "name": "read_file",
      "input": {
        "path": "src/main.ts"
      }
    }
  ]
}

// Agent 执行工具
const result = await tool.execute(
  "toolu_01A09q90qw90lq917835lq9",  // toolCallId
  { path: "src/main.ts" },           // params
  abortSignal,                       // signal
  onUpdate                           // 流式更新回调
);

// 工具结果注入上下文
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
      "content": "export function main() { ... }"
    }
  ]
}

// LLM 基于工具结果继续生成
{
  "role": "assistant",
  "content": "I can see the main function exports..."
}
```

#### 并行工具调用

```typescript
// LLM 可以同时请求多个工具
{
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01",
      "name": "read_file",
      "input": { "path": "package.json" }
    },
    {
      "type": "tool_use",
      "id": "toolu_02",
      "name": "read_file",
      "input": { "path": "tsconfig.json" }
    }
  ]
}

// Agent 并行执行所有工具
const results = await Promise.all([
  tool1.execute("toolu_01", params1, signal),
  tool2.execute("toolu_02", params2, signal),
]);

// 所有结果一起注入上下文
{
  "role": "user",
  "content": [
    { "type": "tool_result", "tool_use_id": "toolu_01", "content": "..." },
    { "type": "tool_result", "tool_use_id": "toolu_02", "content": "..." }
  ]
}
```

## 四、关键特性实现

### 4.1 流式输出（Streaming）

```typescript
// 流式处理架构
activeSession.agent.streamFn = streamSimple;

// 事件订阅处理流式输出
const subscription = subscribeEmbeddedPiSession({
  session: activeSession,
  onBlockReply: (block) => {
    // 处理文本块
    console.log(block.text);
  },
  onToolResult: (result) => {
    // 处理工具结果
    console.log(result.toolName, result.output);
  },
  onReasoningStream: (chunk) => {
    // 处理推理流（思考过程）
    console.log(chunk);
  },
});

// 流式输出的优势：
// 1. 实时反馈：用户立即看到响应
// 2. 降低延迟：不需要等待完整响应
// 3. 更好的体验：显示"正在思考"状态
// 4. 支持中断：可以随时停止生成
```

### 4.2 上下文管理

#### 消息历史管理

```typescript
// SessionManager 管理消息树
class SessionManager {
  // 添加消息
  addMessage(message: AgentMessage): void;

  // 分支管理（支持多个对话分支）
  branch(parentId: string): void;

  // 获取当前分支的消息
  buildSessionContext(): { messages: AgentMessage[] };

  // 重置到特定点
  resetLeaf(): void;
}

// 消息验证和清理
const sanitized = await sanitizeSessionHistory({
  messages: activeSession.messages,
  modelApi: safeModel.api,
  modelId: params.modelId,
  provider: params.provider,
  sessionManager,
  policy: transcriptPolicy,
});

// 历史长度限制
const limited = limitHistoryTurns(
  validated,
  getDmHistoryLimitFromSessionKey(params.sessionKey, params.config),
);
```

#### 上下文压缩（Compaction）

```typescript
// 当上下文接近限制时自动触发压缩
const compactionMode = params.config?.agents?.defaults?.compaction?.mode;

// 压缩策略：
// 1. "safeguard": 保护模式，保留重要消息
// 2. "aggressive": 激进模式，最大化压缩
// 3. "off": 禁用压缩

// 压缩实现
await generateSummary(
  messages,              // 要压缩的消息
  contextWindow,         // 上下文窗口大小
  reserveTokens,         // 保留的 token 数
  model                  // 用于生成摘要的模型
);

// 压缩后的消息结构
{
  "role": "user",
  "content": "[Summary] Previous conversation covered: ..."
}
```

### 4.3 沙箱隔离

```typescript
// 沙箱配置
const sandbox = await resolveSandboxContext({
  config: params.config,
  sessionKey: sandboxSessionKey,
  workspaceDir: resolvedWorkspace,
});

// 沙箱特性：
// 1. 文件系统隔离
const effectiveWorkspace = sandbox?.enabled
  ? sandbox.workspaceAccess === "rw"
    ? resolvedWorkspace // 读写访问
    : sandbox.workspaceDir // 只读访问
  : resolvedWorkspace;

// 2. 命令执行限制
const execTool = createExecTool({
  sandbox, // 沙箱配置
  elevated: params.bashElevated, // 是否允许提权
  abortSignal, // 中止信号
});

// 3. 网络访问控制
// 4. 资源限制（CPU、内存、时间）
```

### 4.4 错误处理和重试

```typescript
// 工具重试保护
class ToolRetryGuard {
  shouldBlockTool(toolName: string, params: Record<string, unknown>) {
    const failures = this.getRecentFailures(toolName);

    // 检查连续失败次数
    if (failures.length >= this.maxConsecutiveFailures) {
      // 检查参数相似度
      if (this.checkParamSimilarity) {
        const similar = this.areSimilarParams(params, failures);
        if (similar) {
          return { blocked: true, reason: "similar-params" };
        }
      }
      return { blocked: true, reason: "max-failures" };
    }

    return { blocked: false };
  }

  recordFailure(failure: ToolFailure) {
    this.failures.push(failure);
    this.cleanupOldFailures();
  }
}

// 超时处理
const abortTimer = setTimeout(() => {
  abortRun(true); // 超时中止
}, params.timeoutMs);

// 中止信号传播
const abortable = <T>(promise: Promise<T>): Promise<T> => {
  return new Promise<T>((resolve, reject) => {
    const onAbort = () => reject(makeAbortError(signal));
    signal.addEventListener("abort", onAbort, { once: true });
    promise.then(resolve, reject).finally(() => {
      signal.removeEventListener("abort", onAbort);
    });
  });
};
```

## 五、扩展机制

### 5.1 插件系统

```typescript
// 插件工具注册
const pluginTools = resolvePluginTools({
  context: {
    config: options?.config,
    workspaceDir: options?.workspaceDir,
    agentDir: options?.agentDir,
    agentId: resolveSessionAgentId({
      sessionKey: options?.agentSessionKey,
      config: options?.config,
    }),
  },
  allowlist: options?.pluginToolAllowlist,
});

// 插件工具示例（飞书插件）
const feishuTools = [
  feishu_doc, // 文档操作
  feishu_wiki, // 知识库
  feishu_drive, // 云文档
  feishu_bitable, // 多维表格
];
```

### 5.2 钩子系统

```typescript
// 钩子类型
type HookType =
  | "before_agent_start" // Agent 启动前
  | "agent_end" // Agent 结束后
  | "before_tool_call" // 工具调用前
  | "after_tool_call" // 工具调用后
  | "message_received" // 消息接收时
  | "message_sent"; // 消息发送时

// 注册钩子
hookRunner.register("before_agent_start", async (data, context) => {
  // 可以修改 prompt
  return {
    prependContext: "Additional context...",
  };
});

// 运行钩子
const hookResult = await hookRunner.runBeforeAgentStart(
  { prompt: params.prompt, messages: activeSession.messages },
  { agentId, sessionKey, workspaceDir },
);

if (hookResult?.prependContext) {
  effectivePrompt = `${hookResult.prependContext}\n\n${params.prompt}`;
}
```

### 5.3 自定义工具

```typescript
// 创建自定义工具
const customTool: AgentTool<MyParams, MyResult> = {
  name: "my_custom_tool",
  label: "My Custom Tool",
  description: "Does something custom",
  parameters: Type.Object({
    input: Type.String({ description: "Input parameter" }),
  }),
  execute: async (toolCallId, params, signal, onUpdate) => {
    // 1. 验证参数
    if (!params.input) {
      return jsonResult({
        status: "error",
        error: "Missing input parameter",
      });
    }

    // 2. 执行操作
    const result = await doSomething(params.input);

    // 3. 流式更新（可选）
    if (onUpdate) {
      onUpdate({
        status: "progress",
        message: "Processing...",
      });
    }

    // 4. 返回结果
    return jsonResult({
      status: "success",
      result: result,
    });
  },
};

// 注册到工具集
const tools = [...builtInTools, customTool];
```

## 六、性能优化

### 6.1 缓存机制

```typescript
// 提示词缓存追踪
const cacheTrace = createCacheTrace({
  cfg: params.config,
  runId: params.runId,
  sessionId: activeSession.sessionId,
  provider: params.provider,
  modelId: params.modelId,
});

// 记录缓存阶段
cacheTrace?.recordStage("session:loaded", {
  messages: activeSession.messages,
  system: systemPromptText,
});

// 包装流函数以追踪缓存
activeSession.agent.streamFn = cacheTrace.wrapStreamFn(activeSession.agent.streamFn);

// 缓存 TTL 追踪
if (shouldTrackCacheTtl) {
  appendCacheTtlTimestamp(sessionManager, {
    timestamp: Date.now(),
    provider: params.provider,
    modelId: params.modelId,
  });
}
```

### 6.2 并发控制

```typescript
// Agent 并发限制
const maxConcurrent = params.config?.agents?.defaults?.maxConcurrent ?? 4;

// Subagent 并发限制
const subagentMaxConcurrent = params.config?.agents?.defaults?.subagents?.maxConcurrent ?? 8;

// 会话锁（防止并发写入）
const sessionLock = await acquireSessionWriteLock({
  sessionFile: params.sessionFile,
});

try {
  // 执行操作
  await runAgent();
} finally {
  // 释放锁
  await sessionLock.release();
}
```

### 6.3 资源管理

```typescript
// 会话文件预热
await prewarmSessionFile(params.sessionFile);

// 跟踪会话访问
trackSessionManagerAccess(params.sessionFile);

// 清理资源
try {
  // 执行
} finally {
  // 刷新待处理结果
  sessionManager?.flushPendingToolResults?.();

  // 释放 session
  session?.dispose();

  // 释放锁
  await sessionLock.release();

  // 恢复环境
  restoreSkillEnv?.();
  process.chdir(prevCwd);
}
```

## 七、设计优势总结

### 7.1 极简主义的价值

Pi Agent Core 的 "LLM + Tools + Loop" 设计哲学带来了以下优势：

1. **概念清晰**
   - 只有三个核心概念，易于理解和学习
   - 每个组件职责明确，边界清晰
   - 降低了系统的认知负担

2. **易于扩展**
   - 添加新工具只需实现 `AgentTool` 接口
   - 插件系统支持动态加载
   - 钩子系统允许在关键点注入自定义逻辑

3. **高度可组合**
   - 工具可以自由组合
   - 支持工具链（一个工具调用另一个工具）
   - 支持并行工具调用

4. **可测试性强**
   - 每个组件可以独立测试
   - 工具执行可以 mock
   - 流式输出可以验证

### 7.2 与传统架构的对比

| 特性       | Pi Agent Core              | 传统 Agent 框架                               |
| ---------- | -------------------------- | --------------------------------------------- |
| 核心概念   | 3 个（LLM + Tools + Loop） | 10+ 个（Agent、Memory、Planner、Executor...） |
| 学习曲线   | 平缓                       | 陡峭                                          |
| 代码复杂度 | 低                         | 高                                            |
| 扩展性     | 高（插件系统）             | 中（需要理解框架内部）                        |
| 性能       | 高（流式处理）             | 中（批处理为主）                              |
| 调试难度   | 低（事件订阅）             | 高（黑盒执行）                                |

### 7.3 适用场景

Pi Agent Core 特别适合以下场景：

1. **编码助手**
   - 代码生成、重构、调试
   - 文件操作、命令执行
   - Git 操作、测试运行

2. **自动化任务**
   - 批量文件处理
   - 数据转换和清洗
   - 定时任务执行

3. **知识管理**
   - 文档搜索和总结
   - 知识库构建
   - 问答系统

4. **集成平台**
   - 飞书、钉钉等企业应用集成
   - API 调用和数据同步
   - 多系统协同

## 八、最佳实践

### 8.1 工具设计原则

1. **单一职责**

   ```typescript
   // ✅ 好的设计：每个工具只做一件事
   const readFileTool = { name: "read_file", ... };
   const writeFileTool = { name: "write_file", ... };

   // ❌ 不好的设计：一个工具做多件事
   const fileOperationTool = {
     name: "file_operation",
     parameters: {
       operation: Type.Union([
         Type.Literal("read"),
         Type.Literal("write"),
         Type.Literal("delete"),
       ]),
     },
   };
   ```

2. **清晰的描述**

   ```typescript
   // ✅ 好的描述：明确说明工具的功能、参数和返回值
   {
     name: "search_files",
     description: "Search for files matching a pattern in the workspace. " +
                  "Returns a list of file paths. Use glob patterns like " +
                  "'**/*.ts' for recursive search.",
     parameters: Type.Object({
       pattern: Type.String({
         description: "Glob pattern to match files (e.g., '**/*.ts')"
       }),
     }),
   }

   // ❌ 不好的描述：模糊不清
   {
     name: "search",
     description: "Search for something",
     parameters: Type.Object({
       query: Type.String(),
     }),
   }
   ```

3. **错误处理**

   ```typescript
   // ✅ 好的错误处理：提供详细的错误信息
   execute: async (toolCallId, params, signal) => {
     try {
       const result = await fs.readFile(params.path, "utf-8");
       return jsonResult({ status: "success", content: result });
     } catch (err) {
       return jsonResult({
         status: "error",
         error: `Failed to read file: ${err.message}`,
         path: params.path,
         suggestion: "Check if the file exists and you have read permissions",
       });
     }
   };
   ```

4. **流式更新**
   ```typescript
   // ✅ 对于长时间运行的工具，提供进度更新
   execute: async (toolCallId, params, signal, onUpdate) => {
     const files = await listFiles(params.directory);

     for (let i = 0; i < files.length; i++) {
       await processFile(files[i]);

       // 报告进度
       if (onUpdate) {
         onUpdate({
           status: "progress",
           message: `Processing ${i + 1}/${files.length} files`,
           progress: (i + 1) / files.length,
         });
       }
     }

     return jsonResult({ status: "success", processed: files.length });
   };
   ```

### 8.2 Prompt 工程

1. **系统提示词结构**

   ```typescript
   // 推荐的系统提示词结构
   const systemPrompt = `
   # Role
   You are a coding assistant specialized in TypeScript development.
   
   # Capabilities
   - Read and write files
   - Execute shell commands
   - Search code
   - Run tests
   
   # Guidelines
   - Always verify file paths before operations
   - Use relative paths from workspace root
   - Run tests after making changes
   - Provide clear explanations
   
   # Constraints
   - Do not modify files outside the workspace
   - Do not execute dangerous commands
   - Ask for confirmation before destructive operations
   `;
   ```

2. **用户提示词优化**

   ```typescript
   // ✅ 好的用户提示词：具体、可执行
   const goodPrompt =
     "Read the file src/utils/helper.ts and add a new function " +
     "called 'formatDate' that takes a Date object and returns " +
     "a string in ISO format. Add JSDoc comments and unit tests.";

   // ❌ 不好的用户提示词：模糊、难以执行
   const badPrompt = "Make the code better";
   ```

3. **上下文注入**

   ```typescript
   // 在关键时刻注入额外上下文
   const hookResult = await hookRunner.runBeforeAgentStart({
     prompt: userPrompt,
     messages: session.messages,
   });

   if (hookResult?.prependContext) {
     // 注入项目特定的上下文
     effectivePrompt = `
     ${hookResult.prependContext}
     
     Current workspace: ${workspaceDir}
     Current branch: ${currentBranch}
     Recent changes: ${recentChanges}
     
     User request: ${userPrompt}
     `;
   }
   ```

### 8.3 性能优化技巧

1. **批量操作**

   ```typescript
   // ✅ 批量读取文件
   const files = await Promise.all(filePaths.map((path) => readFile(path)));

   // ❌ 逐个读取文件
   const files = [];
   for (const path of filePaths) {
     files.push(await readFile(path));
   }
   ```

2. **缓存利用**

   ```typescript
   // 利用提示词缓存减少重复计算
   const cacheTrace = createCacheTrace({
     cfg: config,
     runId,
     sessionId,
     provider,
     modelId,
   });

   // 记录缓存阶段
   cacheTrace.recordStage("system:loaded", {
     system: systemPrompt,
   });

   cacheTrace.recordStage("tools:loaded", {
     tools: toolDefinitions,
   });
   ```

3. **上下文压缩**

   ```typescript
   // 配置合理的压缩策略
   const config = {
     agents: {
       defaults: {
         compaction: {
           mode: "safeguard", // 保护重要消息
           reserveTokens: 4000, // 保留足够的空间
           summaryModel: "fast", // 使用快速模型生成摘要
         },
       },
     },
   };
   ```

4. **并发控制**
   ```typescript
   // 限制并发数避免资源耗尽
   const config = {
     agents: {
       defaults: {
         maxConcurrent: 4, // 主 Agent 并发数
         subagents: {
           maxConcurrent: 8, // Subagent 并发数
         },
       },
     },
   };
   ```

### 8.4 安全实践

1. **沙箱隔离**

   ```typescript
   // 启用沙箱保护文件系统
   const sandbox = {
     enabled: true,
     workspaceAccess: "ro", // 只读访问
     allowedCommands: [
       // 白名单命令
       "ls",
       "cat",
       "grep",
       "find",
     ],
   };
   ```

2. **命令验证**

   ```typescript
   // 验证命令安全性
   const dangerousPatterns = [
     /rm\s+-rf\s+\//, // 删除根目录
     /:\(\)\{.*\}/, // Fork 炸弹
     />\s*\/dev\/sda/, // 写入磁盘
   ];

   function isCommandSafe(command: string): boolean {
     return !dangerousPatterns.some((pattern) => pattern.test(command));
   }
   ```

3. **权限控制**

   ```typescript
   // 工具权限分级
   const toolPermissions = {
     read_file: "read",
     write_file: "write",
     exec_command: "execute",
     delete_file: "admin",
   };

   // 检查权限
   function checkPermission(toolName: string, userRole: string): boolean {
     const required = toolPermissions[toolName];
     return hasPermission(userRole, required);
   }
   ```

## 九、常见问题和故障排查

### 9.1 工具调用失败

**问题**: 工具被重复调用但总是失败

**原因**:

- 参数格式错误
- 工具实现有 bug
- 缺少必要的权限或依赖

**解决方案**:

```typescript
// 1. 检查工具重试保护日志
const guard = new ToolRetryGuard({
  maxConsecutiveFailures: 3,
  failureWindowMs: 5 * 60 * 1000,
  checkParamSimilarity: true,
});

// 2. 查看失败记录
const failures = guard.getRecentFailures(toolName);
console.log("Recent failures:", failures);

// 3. 验证参数 schema
const validated = Value.Check(tool.parameters, params);
if (!validated) {
  const errors = [...Value.Errors(tool.parameters, params)];
  console.log("Validation errors:", errors);
}

// 4. 添加详细的错误日志
execute: async (toolCallId, params, signal) => {
  try {
    console.log(`[${toolName}] Executing with params:`, params);
    const result = await doWork(params);
    console.log(`[${toolName}] Success:`, result);
    return jsonResult({ status: "success", result });
  } catch (err) {
    console.error(`[${toolName}] Error:`, err);
    return jsonResult({
      status: "error",
      error: err.message,
      stack: err.stack,
      params,
    });
  }
};
```

### 9.2 上下文溢出

**问题**: 提示 "context window exceeded" 或 "token limit reached"

**原因**:

- 历史消息过多
- 工具输出过大
- 系统提示词过长

**解决方案**:

```typescript
// 1. 启用上下文压缩
const config = {
  agents: {
    defaults: {
      compaction: {
        mode: "safeguard",
        reserveTokens: 4000,
      },
    },
  },
};

// 2. 限制历史长度
const historyLimit = getDmHistoryLimitFromSessionKey(sessionKey, config);
const limited = limitHistoryTurns(messages, historyLimit);

// 3. 截断工具输出
const MAX_TOOL_OUTPUT = 10000; // 字符数
if (output.length > MAX_TOOL_OUTPUT) {
  output = output.slice(0, MAX_TOOL_OUTPUT) + "\n\n[Output truncated due to length]";
}

// 4. 优化系统提示词
// 移除不必要的示例和说明
// 使用更简洁的语言
// 考虑使用提示词缓存
```

### 9.3 流式输出中断

**问题**: 流式输出突然停止，没有完整响应

**原因**:

- 网络连接中断
- 超时设置过短
- 模型生成被中止

**解决方案**:

```typescript
// 1. 增加超时时间
const timeoutMs = 5 * 60 * 1000; // 5 分钟

// 2. 添加重连逻辑
let retries = 3;
while (retries > 0) {
  try {
    await session.prompt(prompt);
    break;
  } catch (err) {
    if (err.name === "AbortError" && retries > 0) {
      console.log(`Retrying... (${retries} attempts left)`);
      retries--;
      await sleep(1000);
    } else {
      throw err;
    }
  }
}

// 3. 监控流式事件
const subscription = subscribeEmbeddedPiSession({
  session,
  onBlockReply: (block) => {
    lastActivityTime = Date.now();
  },
  onAgentEvent: (event) => {
    if (event.type === "error") {
      console.error("Stream error:", event.error);
    }
  },
});

// 4. 检测超时
const activityTimeout = setInterval(() => {
  if (Date.now() - lastActivityTime > 30000) {
    console.warn("No activity for 30s, stream may be stuck");
  }
}, 5000);
```

### 9.4 会话状态不一致

**问题**: 会话历史丢失或损坏

**原因**:

- 并发写入冲突
- 会话文件损坏
- 序列化错误

**解决方案**:

```typescript
// 1. 使用会话锁
const sessionLock = await acquireSessionWriteLock({
  sessionFile: params.sessionFile,
});

try {
  // 执行操作
} finally {
  await sessionLock.release();
}

// 2. 修复损坏的会话文件
await repairSessionFile(params.sessionFile);

// 3. 验证会话数据
const validated = validateAnthropicTurns(messages);
if (validated.length !== messages.length) {
  console.warn("Some messages were invalid and removed");
}

// 4. 定期备份
const backupFile = `${sessionFile}.backup.${Date.now()}`;
await fs.copyFile(sessionFile, backupFile);
```

### 9.5 性能问题

**问题**: Agent 响应缓慢

**原因**:

- 工具执行耗时
- 模型推理慢
- 上下文过大

**解决方案**:

```typescript
// 1. 分析性能瓶颈
const startTime = Date.now();

const toolTimes = new Map<string, number>();
const originalExecute = tool.execute;
tool.execute = async (...args) => {
  const toolStart = Date.now();
  const result = await originalExecute(...args);
  const toolTime = Date.now() - toolStart;
  toolTimes.set(tool.name, (toolTimes.get(tool.name) || 0) + toolTime);
  return result;
};

// 2. 优化慢工具
// - 添加缓存
// - 并行执行
// - 减少不必要的操作

// 3. 使用更快的模型
const fastModel = {
  provider: "anthropic",
  modelId: "claude-3-haiku-20240307", // 更快的模型
};

// 4. 减少上下文
const config = {
  agents: {
    defaults: {
      historyLimit: 20, // 限制历史消息数
    },
  },
};
```

## 十、参考资料

### 10.1 核心依赖

- **@mariozechner/pi-ai**: LLM 抽象层，提供统一的模型接口
- **@mariozechner/pi-agent-core**: Agent 核心运行时
- **@mariozechner/pi-coding-agent**: 编码 Agent 实现
- **@sinclair/typebox**: TypeScript schema 验证

### 10.2 相关文档

- `src/agents/README.md`: Agent 系统概述
- `src/agents/pi-embedded-runner/README.md`: 嵌入式运行器文档
- `docs/agents/`: Agent 配置和使用指南
- `docs/tools/`: 工具开发指南

### 10.3 代码示例

- `src/agents/openclaw-tools.ts`: 内置工具实现
- `src/agents/pi-tool-definition-adapter.ts`: 工具适配器
- `src/agents/pi-embedded-runner/run/attempt.ts`: 核心执行逻辑
- `src/agents/pi-embedded-subscribe.handlers.messages.ts`: 事件处理

### 10.4 扩展阅读

1. **LLM 工具调用**
   - Anthropic Tool Use: https://docs.anthropic.com/claude/docs/tool-use
   - OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling

2. **Agent 设计模式**
   - ReAct: Reasoning and Acting
   - Chain-of-Thought Prompting
   - Tree of Thoughts

3. **性能优化**
   - Prompt Caching: https://docs.anthropic.com/claude/docs/prompt-caching
   - Streaming Responses
   - Context Window Management

4. **安全实践**
   - Sandboxing Techniques
   - Input Validation
   - Rate Limiting

---

## 总结

Pi Agent Core 通过 "LLM + Tools + Loop" 的极简设计哲学，构建了一个强大而灵活的 AI Agent 运行时框架。这个设计的核心优势在于：

1. **简单**: 只有三个核心概念，易于理解和使用
2. **强大**: 支持复杂的工具调用、流式输出、上下文管理
3. **灵活**: 插件系统、钩子系统、自定义工具
4. **高效**: 并行执行、缓存机制、资源管理
5. **安全**: 沙箱隔离、权限控制、错误处理

通过深入理解这个架构，开发者可以：

- 快速构建自己的 AI Agent 应用
- 扩展和定制 Agent 能力
- 优化性能和用户体验
- 解决常见问题和故障

Pi Agent Core 证明了"少即是多"的设计理念：通过精心设计的核心抽象，可以用最少的概念实现最强大的功能。
