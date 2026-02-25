# OpenClaw (Clawdbot) 详细架构文档

> 基于 OpenClaw v2026.2.6-3 代码库分析
>
> 本文档为二次开发提供完整的架构指南

## 📋 目录

1. [项目概述](#项目概述)
2. [核心架构](#核心架构)
3. [目录结构](#目录结构)
4. [核心模块详解](#核心模块详解)
5. [数据流与通信](#数据流与通信)
6. [扩展开发指南](#扩展开发指南)
7. [关键技术栈](#关键技术栈)

---

## 项目概述

### 什么是 OpenClaw?

OpenClaw 是一个**个人 AI 助手平台**,核心特点:

- **多渠道接入**: WhatsApp, Telegram, Slack, Discord, Signal, iMessage, 飞书等
- **本地优先**: Gateway 作为控制平面,运行在用户自己的设备上
- **多 Agent 路由**: 支持多个独立 Agent,每个有自己的工作空间和会话
- **工具生态**: 浏览器控制、Canvas、定时任务、Webhook 等
- **跨平台**: macOS/Linux/Windows(WSL2) + iOS/Android 节点

### 技术栈

- **运行时**: Node.js ≥22 (支持 Bun)
- **语言**: TypeScript (ESM)
- **构建**: tsdown + rolldown
- **测试**: Vitest
- **格式化/Lint**: Oxfmt + Oxlint
- **包管理**: pnpm (推荐) / npm / bun

---

## 核心架构

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      消息渠道层 (Channels)                        │
│  WhatsApp │ Telegram │ Slack │ Discord │ Signal │ 飞书 │ ...    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Gateway 控制平面                               │
│                  ws://127.0.0.1:18789                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ WebSocket    │  │ HTTP Server  │  │ Control UI   │          │
│  │ 服务器       │  │ (OpenAI API) │  │ (Web界面)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 路由管理     │  │ 会话管理     │  │ 插件系统     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent 执行层                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Pi Agent Runtime (基于 @mariozechner/pi-*)             │   │
│  │  - 工具调用                                              │   │
│  │  - 流式输出                                              │   │
│  │  - 会话管理                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      工具层 (Tools)                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Bash/Exec│ │ Browser  │ │ Canvas   │ │ Nodes    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Cron     │ │ Sessions │ │ Memory   │ │ Plugins  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 三层架构

1. **渠道层 (Channels)**: 处理各种消息平台的接入
2. **Gateway 层**: 核心控制平面,负责路由、会话、插件管理
3. **Agent 层**: AI 执行引擎,处理用户请求并调用工具
4. **工具层**: 提供各种能力(命令执行、浏览器、定时任务等)

---

## 目录结构

### 顶层目录

```
openclaw/
├── src/                    # 核心源代码
│   ├── agents/            # Agent 运行时和工具
│   ├── gateway/           # Gateway 服务器
│   ├── channels/          # 渠道抽象层
│   ├── cli/               # CLI 命令
│   ├── config/            # 配置管理
│   ├── auto-reply/        # 自动回复逻辑
│   ├── browser/           # 浏览器控制
│   ├── cron/              # 定时任务
│   ├── hooks/             # 钩子系统
│   ├── infra/             # 基础设施
│   ├── memory/            # 记忆/向量存储
│   ├── plugins/           # 插件系统
│   └── ...
├── extensions/            # 扩展插件
│   ├── feishu/           # 飞书集成
│   ├── discord/          # Discord 集成
│   ├── telegram/         # Telegram 集成
│   └── ...
├── apps/                  # 客户端应用
│   ├── macos/            # macOS 菜单栏应用
│   ├── ios/              # iOS 节点应用
│   └── android/          # Android 节点应用
├── docs/                  # 文档
├── scripts/               # 构建和工具脚本
└── ui/                    # Control UI (Web界面)
```

---

## 核心模块详解

### 1. Gateway 服务器 (`src/gateway/`)

**职责**: 核心控制平面,管理所有连接、会话和事件

#### 关键文件

- `server.impl.ts`: Gateway 主入口,启动所有服务
- `server-runtime-state.ts`: 运行时状态管理
- `server-methods.ts`: WebSocket RPC 方法处理
- `server-chat.ts`: 聊天会话管理
- `server-channels.ts`: 渠道管理器
- `server-cron.ts`: 定时任务服务
- `server-plugins.ts`: 插件加载

#### 核心功能

```typescript
// Gateway 启动流程
export async function startGatewayServer(
  port = 18789,
  opts: GatewayServerOptions = {},
): Promise<GatewayServer> {
  // 1. 加载配置
  const cfgAtStart = loadConfig();

  // 2. 加载插件
  const { pluginRegistry, gatewayMethods } = loadGatewayPlugins({...});

  // 3. 创建运行时状态
  const runtimeState = await createGatewayRuntimeState({...});

  // 4. 启动渠道
  const channelManager = createChannelManager({...});

  // 5. 启动定时任务
  const cronState = buildGatewayCronService({...});

  // 6. 附加 WebSocket 处理器
  attachGatewayWsHandlers({...});

  // 7. 启动发现服务 (Bonjour/mDNS)
  const discovery = await startGatewayDiscovery({...});

  return { close };
}
```

#### WebSocket 协议

Gateway 使用 WebSocket 作为主要通信协议:

- **方法调用**: `{ method: "agent.run", params: {...} }`
- **事件广播**: `{ event: "heartbeat", payload: {...} }`
- **认证**: Token 或密码认证

---

### 2. Agent 运行时 (`src/agents/`)

**职责**: AI Agent 的执行引擎,基于 Pi Agent Core

#### 关键组件

**Pi Embedded Runner** (`pi-embedded-runner.ts`)

- 运行 AI 模型推理
- 管理工具调用
- 处理流式输出
- 会话历史管理

**工具系统** (`pi-tools.ts`)

- 工具定义和注册
- 工具调用前/后钩子
- 工具权限策略

**会话管理** (`session-*.ts`)

- 会话存储 (JSONL 格式)
- 会话修复和迁移
- 会话锁机制

#### Agent 执行流程

```typescript
// 简化的 Agent 执行流程
async function runEmbeddedPiAgent(opts: {
  sessionKey: string;
  message: string;
  tools: Tool[];
  systemPrompt: string;
  model: string;
}) {
  // 1. 加载会话历史
  const session = await loadSession(opts.sessionKey);

  // 2. 添加用户消息
  session.messages.push({
    role: "user",
    content: opts.message,
  });

  // 3. 调用 AI 模型
  const stream = await piAgent.run({
    messages: session.messages,
    tools: opts.tools,
    model: opts.model,
    systemPrompt: opts.systemPrompt,
  });

  // 4. 处理流式响应
  for await (const chunk of stream) {
    if (chunk.type === "text") {
      // 发送文本块
      await sendTextChunk(chunk.text);
    } else if (chunk.type === "toolCall") {
      // 执行工具
      const result = await executeTool(chunk.toolName, chunk.args);
      // 继续推理
    }
  }

  // 5. 保存会话
  await saveSession(session);
}
```

---

### 3. 渠道系统 (`src/channels/` + `extensions/`)

**职责**: 统一的消息渠道抽象层

#### 渠道插件结构

每个渠道插件需要实现:

```typescript
interface ChannelPlugin {
  id: ChannelId;
  name: string;

  // 启动监听
  monitor: (opts: MonitorOpts) => Promise<void>;

  // 发送消息
  send: (opts: SendOpts) => Promise<void>;

  // 探测状态
  probe: () => Promise<ProbeResult>;

  // 可选: Gateway 方法扩展
  gatewayMethods?: string[];
}
```

#### 内置渠道

- **WhatsApp** (`src/web/`): 基于 Baileys
- **Telegram** (`src/telegram/`): 基于 grammY
- **Slack** (`src/slack/`): 基于 Bolt
- **Discord** (`src/discord/`): 基于 discord.js
- **Signal** (`src/signal/`): 基于 signal-cli
- **iMessage** (`src/imessage/`): macOS 原生

#### 扩展渠道 (extensions/)

- **飞书** (`extensions/feishu/`)
- **Microsoft Teams** (`extensions/msteams/`)
- **Matrix** (`extensions/matrix/`)
- **Zalo** (`extensions/zalo/`)

#### 飞书集成示例

```typescript
// extensions/feishu/index.ts
export const feishuPlugin: ChannelPlugin = {
  id: "feishu",
  name: "Feishu",

  async monitor(opts) {
    // 1. 启动 HTTP 服务器接收 Webhook
    const server = createServer((req, res) => {
      // 验证签名
      // 解析事件
      // 调用 opts.onMessage
    });

    // 2. 订阅事件
    await subscribeToEvents();
  },

  async send(opts) {
    // 调用飞书 API 发送消息
    await feishuClient.sendMessage({
      receive_id: opts.to,
      content: opts.message,
    });
  },

  async probe() {
    // 检查连接状态
    return { connected: true };
  },
};
```

---

### 4. 自动回复系统 (`src/auto-reply/`)

**职责**: 处理入站消息并触发 Agent

#### 核心流程

```typescript
// src/auto-reply/reply.ts
export async function getReplyFromConfig(opts: {
  message: string;
  from: string;
  channel: ChannelId;
  sessionKey: string;
}) {
  // 1. 检查权限 (allowlist)
  if (!isAllowed(opts.from, opts.channel)) {
    return { blocked: true };
  }

  // 2. 检测命令
  const command = detectCommand(opts.message);
  if (command) {
    return await handleCommand(command);
  }

  // 3. 路由到 Agent
  const sessionKey = resolveSessionKey(opts);

  // 4. 运行 Agent
  const reply = await runAgent({
    sessionKey,
    message: opts.message,
  });

  // 5. 分块发送
  await sendChunkedReply(reply, opts.channel);
}
```

#### 指令系统

- `/status`: 会话状态
- `/reset`: 重置会话
- `/compact`: 压缩上下文
- `/think <level>`: 设置思考级别
- `/model <name>`: 切换模型

---

### 5. 工具系统 (`src/agents/tools/`)

**职责**: 为 Agent 提供各种能力

#### 核心工具

**Bash/Exec** (`bash-tools.exec.ts`)

```typescript
{
  name: "exec",
  description: "Execute a shell command",
  inputSchema: {
    command: { type: "string" },
    timeout: { type: "number", optional: true },
  },
  async execute(args) {
    const result = await runCommand(args.command, {
      timeout: args.timeout,
    });
    return {
      stdout: result.stdout,
      stderr: result.stderr,
      exitCode: result.exitCode,
    };
  },
}
```

**Browser** (`src/browser/`)

- 启动 Chrome/Chromium
- CDP 控制
- 截图、点击、输入
- 下载管理

**Canvas** (`src/canvas-host/`)

- A2UI 渲染
- 实时更新
- 跨平台 (macOS/iOS/Android)

**Nodes** (设备节点)

- 相机拍照/录像
- 屏幕录制
- 位置获取
- 通知推送

**Sessions** (会话工具)

- `sessions_list`: 列出会话
- `sessions_history`: 获取历史
- `sessions_send`: 跨会话通信
- `sessions_spawn`: 创建子 Agent

---

### 6. 配置系统 (`src/config/`)

**职责**: 统一的配置管理

#### 配置文件

- **主配置**: `~/.openclaw/openclaw.json`
- **会话配置**: `~/.openclaw/sessions/`
- **凭证**: `~/.openclaw/credentials/`

#### 配置结构

```typescript
interface OpenClawConfig {
  // Agent 配置
  agents?: {
    defaults?: {
      model?: string;
      workspace?: string;
      tools?: {
        deny?: string[];
        alsoAllow?: string[];
      };
      sandbox?: {
        mode?: "off" | "non-main" | "all";
      };
    };
  };

  // 渠道配置
  channels?: {
    whatsapp?: WhatsAppConfig;
    telegram?: TelegramConfig;
    feishu?: FeishuConfig;
    // ...
  };

  // Gateway 配置
  gateway?: {
    bind?: "loopback" | "lan" | "tailnet";
    port?: number;
    auth?: {
      mode?: "none" | "token" | "password";
    };
  };

  // 插件配置
  plugins?: {
    entries?: Record<string, PluginConfig>;
  };
}
```

#### 配置加载

```typescript
// src/config/config.ts
export function loadConfig(): OpenClawConfig {
  // 1. 读取配置文件
  const raw = readConfigFile();

  // 2. 验证 schema
  const validated = validateConfig(raw);

  // 3. 应用默认值
  const withDefaults = applyDefaults(validated);

  // 4. 环境变量覆盖
  const final = applyEnvOverrides(withDefaults);

  return final;
}
```

---

### 7. 插件系统 (`src/plugins/`)

**职责**: 扩展 Gateway 和 Agent 功能

#### 插件类型

1. **渠道插件**: 添加新的消息平台
2. **工具插件**: 添加新的 Agent 工具
3. **Provider 插件**: 添加新的 AI 模型提供商
4. **Hook 插件**: 添加事件钩子

#### 插件结构

```typescript
// extensions/my-plugin/index.ts
import type { Plugin } from "openclaw/plugin-sdk";

export const myPlugin: Plugin = {
  id: "my-plugin",
  name: "My Plugin",
  version: "1.0.0",

  // 初始化
  async init(context) {
    // 注册工具
    context.registerTool({
      name: "my_tool",
      description: "My custom tool",
      execute: async (args) => {
        // 实现
      },
    });

    // 注册 Gateway 方法
    context.registerGatewayMethod({
      name: "myPlugin.doSomething",
      handler: async (params) => {
        // 实现
      },
    });
  },

  // 清理
  async cleanup() {
    // 清理资源
  },
};
```

---

### 8. 定时任务 (`src/cron/`)

**职责**: 定时触发 Agent 执行

#### Cron 配置

```typescript
interface CronJob {
  id: string;
  name: string;
  enabled: boolean;
  schedule: {
    kind: "cron" | "interval";
    expr: string; // "0 8 * * *" 或 "1h"
  };
  payload: {
    kind: "agentTurn";
    message: string;
    deliver: boolean; // 是否发送回复
  };
  sessionTarget: "main" | "isolated";
}
```

#### 使用示例

```bash
# 添加定时任务
openclaw cron add \
  --name "morning-report" \
  --schedule "0 8 * * *" \
  --message "生成今日工作报告" \
  --deliver true

# 列出任务
openclaw cron list

# 删除任务
openclaw cron delete morning-report
```

---

## 数据流与通信

### 消息流

```
用户消息 (WhatsApp/Telegram/...)
  │
  ▼
渠道插件 (monitor)
  │
  ▼
auto-reply (getReplyFromConfig)
  │
  ├─ 权限检查
  ├─ 命令检测
  └─ 路由到 Agent
      │
      ▼
    Agent 运行时 (runEmbeddedPiAgent)
      │
      ├─ 加载会话
      ├─ 调用 AI 模型
      ├─ 执行工具
      └─ 生成回复
          │
          ▼
        分块发送 (sendChunkedReply)
          │
          ▼
        渠道插件 (send)
          │
          ▼
        用户收到回复
```

### WebSocket 通信

```
客户端 (macOS app / CLI / Web UI)
  │
  │ ws://127.0.0.1:18789
  │
  ▼
Gateway WebSocket 服务器
  │
  ├─ 认证
  ├─ 方法调用
  │   ├─ agent.run
  │   ├─ sessions.list
  │   ├─ config.get
  │   └─ ...
  │
  └─ 事件广播
      ├─ heartbeat
      ├─ agent.progress
      ├─ channel.status
      └─ ...
```

---

## 扩展开发指南

### 1. 添加新渠道

#### 步骤

1. 创建插件目录: `extensions/my-channel/`
2. 实现 `ChannelPlugin` 接口
3. 添加配置 schema
4. 注册插件

#### 示例: 添加钉钉集成

```typescript
// extensions/dingtalk/index.ts
import type { Plugin } from "openclaw/plugin-sdk";

export const dingtalkPlugin: Plugin = {
  id: "dingtalk",
  name: "DingTalk",
  version: "1.0.0",

  async init(context) {
    // 注册渠道
    context.registerChannel({
      id: "dingtalk",
      name: "DingTalk",

      async monitor(opts) {
        // 启动 Webhook 服务器
        const server = createWebhookServer({
          port: opts.config.webhookPort,
          secret: opts.config.webhookSecret,

          onMessage: async (msg) => {
            // 调用统一的消息处理
            await opts.onMessage({
              from: msg.senderId,
              text: msg.text,
              media: msg.attachments,
            });
          },
        });

        await server.start();
      },

      async send(opts) {
        // 调用钉钉 API
        await dingtalkClient.sendMessage({
          chatId: opts.to,
          msgtype: "text",
          text: { content: opts.message },
        });
      },

      async probe() {
        // 检查连接
        const ok = await dingtalkClient.ping();
        return { connected: ok };
      },
    });
  },
};

// extensions/dingtalk/package.json
{
  "name": "@openclaw/dingtalk",
  "version": "1.0.0",
  "main": "index.ts",
  "dependencies": {
    "dingtalk-sdk": "^1.0.0"
  }
}
```

### 2. 添加新工具

```typescript
// extensions/my-tools/index.ts
export const myToolsPlugin: Plugin = {
  id: "my-tools",
  name: "My Tools",

  async init(context) {
    // 注册工具
    context.registerTool({
      name: "weather_get",
      description: "Get current weather for a location",
      inputSchema: {
        type: "object",
        properties: {
          location: {
            type: "string",
            description: "City name or coordinates",
          },
        },
        required: ["location"],
      },

      async execute(args, ctx) {
        // 调用天气 API
        const weather = await fetchWeather(args.location);

        return {
          temperature: weather.temp,
          condition: weather.condition,
          humidity: weather.humidity,
        };
      },
    });
  },
};
```

### 3. 添加 Gateway 方法

```typescript
export const myPlugin: Plugin = {
  id: "my-plugin",

  async init(context) {
    // 注册 WebSocket 方法
    context.registerGatewayMethod({
      name: "myPlugin.getData",

      async handler(params, ctx) {
        // 处理请求
        const data = await fetchData(params.id);

        return {
          success: true,
          data,
        };
      },
    });
  },
};
```

### 4. 添加事件钩子

```typescript
export const myPlugin: Plugin = {
  id: "my-plugin",

  async init(context) {
    // 监听 Agent 事件
    context.onAgentEvent("tool.start", async (event) => {
      console.log(`Tool ${event.toolName} started`);
    });

    context.onAgentEvent("tool.end", async (event) => {
      console.log(`Tool ${event.toolName} completed`);
    });

    // 监听渠道事件
    context.onChannelEvent("message.received", async (event) => {
      console.log(`Message from ${event.from}: ${event.text}`);
    });
  },
};
```

---

## 关键技术栈

### 核心依赖

```json
{
  "dependencies": {
    // Agent 运行时
    "@mariozechner/pi-agent-core": "0.52.9",
    "@mariozechner/pi-ai": "0.52.9",
    "@mariozechner/pi-coding-agent": "0.52.9",

    // 渠道集成
    "@whiskeysockets/baileys": "7.0.0-rc.9", // WhatsApp
    "grammy": "^1.39.3", // Telegram
    "@slack/bolt": "^4.6.0", // Slack
    "discord-api-types": "^0.38.38", // Discord
    "@larksuiteoapi/node-sdk": "^1.58.0", // 飞书

    // 浏览器控制
    "playwright-core": "1.58.2",

    // 工具
    "croner": "^10.0.1", // Cron
    "ws": "^8.19.0", // WebSocket
    "express": "^5.2.1", // HTTP
    "hono": "4.11.9", // 轻量 HTTP

    // 数据处理
    "zod": "^4.3.6", // Schema 验证
    "@sinclair/typebox": "0.34.48", // TypeBox
    "yaml": "^2.8.2", // YAML
    "json5": "^2.2.3", // JSON5

    // 其他
    "chalk": "^5.6.2", // 终端颜色
    "commander": "^14.0.3", // CLI
    "tslog": "^4.10.2" // 日志
  }
}
```

### 构建工具

- **tsdown**: TypeScript 编译
- **rolldown**: 打包
- **vitest**: 测试
- **oxlint/oxfmt**: Lint 和格式化

---

## 二次开发最佳实践

### 1. 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# 安装依赖
pnpm install

# 构建
pnpm build

# 开发模式 (自动重载)
pnpm gateway:watch
```

### 2. 调试技巧

```bash
# 启用详细日志
OPENCLAW_LOG_LEVEL=debug pnpm openclaw gateway

# 原始流日志
OPENCLAW_RAW_STREAM=1 pnpm openclaw gateway

# 跳过渠道启动 (快速测试)
OPENCLAW_SKIP_CHANNELS=1 pnpm openclaw gateway
```

### 3. 测试

```bash
# 运行所有测试
pnpm test

# 运行特定测试
pnpm test src/agents/pi-tools.test.ts

# 覆盖率
pnpm test:coverage

# E2E 测试
pnpm test:e2e
```

### 4. 代码规范

- 使用 TypeScript strict 模式
- 遵循 ESM 模块规范
- 文件命名: kebab-case
- 测试文件: `*.test.ts`
- 保持文件 <500 行 (建议)

### 5. 提交 PR

1. Fork 仓库
2. 创建功能分支
3. 编写测试
4. 运行 `pnpm check` (lint + format + typecheck)
5. 提交 PR

---

## 常见问题

### Q: 如何添加新的 AI 模型提供商?

A: 实现 Provider 插件:

```typescript
context.registerProvider({
  id: "my-provider",
  name: "My Provider",

  async createClient(config) {
    return {
      async chat(messages, opts) {
        // 调用 API
        const response = await fetch(config.endpoint, {
          method: "POST",
          body: JSON.stringify({ messages }),
        });

        return response.json();
      },
    };
  },
});
```

### Q: 如何自定义 Agent 系统提示?

A: 编辑工作空间文件:

```bash
# 编辑 AGENTS.md
vim ~/.openclaw/workspace/AGENTS.md

# 或使用配置
openclaw config set agents.defaults.systemPrompt "你的提示"
```

### Q: 如何限制工具权限?

A: 使用工具策略:

```json
{
  "agents": {
    "defaults": {
      "tools": {
        "deny": ["exec", "browser"],
        "alsoAllow": ["read", "write"]
      }
    }
  }
}
```

### Q: 如何实现跨会话通信?

A: 使用 `sessions_send` 工具:

```typescript
await context.invokeTool("sessions_send", {
  sessionKey: "other-session",
  message: "Hello from another session",
  replyBack: true,
});
```

---

## 参考资源

- **官方文档**: https://docs.openclaw.ai
- **GitHub**: https://github.com/openclaw/openclaw
- **Discord**: https://discord.gg/clawd
- **DeepWiki**: https://deepwiki.com/openclaw/openclaw

---

## 更新日志

- **2026-02-25**: 初始版本,基于 v2026.2.6-3

---

**祝你开发顺利! 🦞**
