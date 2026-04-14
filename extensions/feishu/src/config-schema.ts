import { z } from "zod";
export { z };

const DmPolicySchema = z.enum(["open", "pairing", "allowlist"]);
const GroupPolicySchema = z.enum(["open", "allowlist", "disabled"]);
const FeishuDomainSchema = z.union([
  z.enum(["feishu", "lark"]),
  z.string().url().startsWith("https://"),
]);
const FeishuConnectionModeSchema = z.enum(["websocket", "webhook"]);

const ToolPolicySchema = z
  .object({
    allow: z.array(z.string()).optional(),
    deny: z.array(z.string()).optional(),
  })
  .strict()
  .optional();

const DmConfigSchema = z
  .object({
    enabled: z.boolean().optional(),
    systemPrompt: z.string().optional(),
  })
  .strict()
  .optional();

const MarkdownConfigSchema = z
  .object({
    mode: z.enum(["native", "escape", "strip"]).optional(),
    tableMode: z.enum(["native", "ascii", "simple"]).optional(),
  })
  .strict()
  .optional();

// Message render mode: auto (default) = detect markdown, raw = plain text, card = always card
const RenderModeSchema = z.enum(["auto", "raw", "card"]).optional();

const BlockStreamingCoalesceSchema = z
  .object({
    enabled: z.boolean().optional(),
    minDelayMs: z.number().int().positive().optional(),
    maxDelayMs: z.number().int().positive().optional(),
  })
  .strict()
  .optional();

const ChannelHeartbeatVisibilitySchema = z
  .object({
    visibility: z.enum(["visible", "hidden"]).optional(),
    intervalMs: z.number().int().positive().optional(),
  })
  .strict()
  .optional();

/**
 * Feishu tools configuration.
 * Controls which tool categories are enabled.
 *
 * Dependencies:
 * - wiki requires doc (wiki content is edited via doc tools)
 * - perm can work independently but is typically used with drive
 */
const FeishuToolsConfigSchema = z
  .object({
    doc: z.boolean().optional(), // Document operations (default: true)
    wiki: z.boolean().optional(), // Knowledge base operations (default: true, requires doc)
    drive: z.boolean().optional(), // Cloud storage operations (default: true)
    perm: z.boolean().optional(), // Permission management (default: false, sensitive)
    scopes: z.boolean().optional(), // App scopes diagnostic (default: true)
  })
  .strict()
  .optional();

/**
 * 阶段 4：飞书进线后同步触发 Airflow REST `POST …/dagRuns`（异步执行由 DAG 负责）。
 * 密码请用环境变量 OPENCLAW_FEISHU_AIRFLOW_PASSWORD，勿写入配置文件。
 */
const FeishuAirflowIngestConfigSchema = z
  .object({
    enabled: z.boolean().optional(),
    /** Airflow Web 根 URL，如 https://airflow.example.com */
    baseUrl: z.string().url().optional(),
    /** 目标 DAG id */
    dagId: z.string().optional(),
    /** HTTP 客户端超时（毫秒），默认 8000，上限 120000 */
    timeoutMs: z.number().int().positive().max(120_000).optional(),
    /**
     * 披露/财报类触发词；未配置时使用内置默认列表（年报、财报、巨潮等）。
     * 正文须包含其中**至少一个**，且能解析出证券代码后才会触发。
     */
    filingKeywords: z.array(z.string()).optional(),
    /** 允许触发 ingest 的 sender_open_id 白名单，支持 "*" */
    allowFrom: z.array(z.union([z.string(), z.number()])).optional(),
    /** 证券简称 → ts_code（如 浪潮信息 → 000977.SZ） */
    stockAliases: z.record(z.string(), z.string()).optional(),
    /** 写入 dag_run.conf.report_type，由 DAG 自行解释 */
    reportType: z.string().optional(),
    /** 限流窗口（毫秒），默认 60000 */
    rateLimitWindowMs: z.number().int().positive().max(86_400_000).optional(),
    /** 单 sender 在窗口内最多触发次数，默认 5 */
    rateLimitMaxPerSender: z.number().int().positive().max(1_000).optional(),
    /** 单账号在窗口内全局最多触发次数，默认 30 */
    rateLimitMaxGlobal: z.number().int().positive().max(10_000).optional(),
    /** 同一消息短期去重窗口（毫秒），默认 600000 */
    dedupeTtlMs: z.number().int().positive().max(86_400_000).optional(),
    /**
     * Basic 用户名（可选）；优先使用环境变量 OPENCLAW_FEISHU_AIRFLOW_USERNAME。
     * 密码仅支持 OPENCLAW_FEISHU_AIRFLOW_PASSWORD，不在此 schema 中声明。
     */
    username: z.string().optional(),
  })
  .strict();

export const FeishuGroupSchema = z
  .object({
    requireMention: z.boolean().optional(),
    tools: ToolPolicySchema,
    skills: z.array(z.string()).optional(),
    enabled: z.boolean().optional(),
    allowFrom: z.array(z.union([z.string(), z.number()])).optional(),
    systemPrompt: z.string().optional(),
  })
  .strict();

/**
 * Per-account configuration.
 * All fields are optional - missing fields inherit from top-level config.
 */
export const FeishuAccountConfigSchema = z
  .object({
    enabled: z.boolean().optional(),
    name: z.string().optional(), // Display name for this account
    appId: z.string().optional(),
    appSecret: z.string().optional(),
    encryptKey: z.string().optional(),
    verificationToken: z.string().optional(),
    domain: FeishuDomainSchema.optional(),
    connectionMode: FeishuConnectionModeSchema.optional(),
    webhookPath: z.string().optional(),
    webhookPort: z.number().int().positive().optional(),
    capabilities: z.array(z.string()).optional(),
    markdown: MarkdownConfigSchema,
    configWrites: z.boolean().optional(),
    dmPolicy: DmPolicySchema.optional(),
    allowFrom: z.array(z.union([z.string(), z.number()])).optional(),
    groupPolicy: GroupPolicySchema.optional(),
    groupAllowFrom: z.array(z.union([z.string(), z.number()])).optional(),
    requireMention: z.boolean().optional(),
    groups: z.record(z.string(), FeishuGroupSchema.optional()).optional(),
    historyLimit: z.number().int().min(0).optional(),
    dmHistoryLimit: z.number().int().min(0).optional(),
    dms: z.record(z.string(), DmConfigSchema).optional(),
    textChunkLimit: z.number().int().positive().optional(),
    chunkMode: z.enum(["length", "newline"]).optional(),
    blockStreamingCoalesce: BlockStreamingCoalesceSchema,
    mediaMaxMb: z.number().positive().optional(),
    heartbeat: ChannelHeartbeatVisibilitySchema,
    renderMode: RenderModeSchema,
    tools: FeishuToolsConfigSchema,
    airflowIngest: FeishuAirflowIngestConfigSchema.optional(),
  })
  .strict();

export const FeishuConfigSchema = z
  .object({
    enabled: z.boolean().optional(),
    // Top-level credentials (backward compatible for single-account mode)
    appId: z.string().optional(),
    appSecret: z.string().optional(),
    encryptKey: z.string().optional(),
    verificationToken: z.string().optional(),
    domain: FeishuDomainSchema.optional().default("feishu"),
    connectionMode: FeishuConnectionModeSchema.optional().default("websocket"),
    webhookPath: z.string().optional().default("/feishu/events"),
    webhookPort: z.number().int().positive().optional(),
    capabilities: z.array(z.string()).optional(),
    markdown: MarkdownConfigSchema,
    configWrites: z.boolean().optional(),
    dmPolicy: DmPolicySchema.optional().default("pairing"),
    allowFrom: z.array(z.union([z.string(), z.number()])).optional(),
    groupPolicy: GroupPolicySchema.optional().default("allowlist"),
    groupAllowFrom: z.array(z.union([z.string(), z.number()])).optional(),
    requireMention: z.boolean().optional().default(true),
    groups: z.record(z.string(), FeishuGroupSchema.optional()).optional(),
    historyLimit: z.number().int().min(0).optional(),
    dmHistoryLimit: z.number().int().min(0).optional(),
    dms: z.record(z.string(), DmConfigSchema).optional(),
    textChunkLimit: z.number().int().positive().optional(),
    chunkMode: z.enum(["length", "newline"]).optional(),
    blockStreamingCoalesce: BlockStreamingCoalesceSchema,
    mediaMaxMb: z.number().positive().optional(),
    heartbeat: ChannelHeartbeatVisibilitySchema,
    renderMode: RenderModeSchema, // raw = plain text (default), card = interactive card with markdown
    tools: FeishuToolsConfigSchema,
    airflowIngest: FeishuAirflowIngestConfigSchema.optional(),
    // Multi-account configuration
    accounts: z.record(z.string(), FeishuAccountConfigSchema.optional()).optional(),
  })
  .strict()
  .superRefine((value, ctx) => {
    if (value.dmPolicy === "open") {
      const allowFrom = value.allowFrom ?? [];
      const hasWildcard = allowFrom.some((entry) => String(entry).trim() === "*");
      if (!hasWildcard) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["allowFrom"],
          message:
            'channels.feishu.dmPolicy="open" requires channels.feishu.allowFrom to include "*"',
        });
      }
    }
  });
