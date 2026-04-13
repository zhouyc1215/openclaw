import { Type } from "@sinclair/typebox";
import type { OpenClawPluginApi } from "../../../src/plugins/types.js";

const LOG_PREFIX = "finance_ask";

/** 去除末尾斜杠，便于拼接 `/ask` */
export function normalizeClawApiBaseUrl(raw: string): string {
  return raw.replace(/\/+$/, "");
}

function readStringConfig(
  envValue: string | undefined,
  pluginValue: unknown,
  fallback: string,
): string {
  const fromEnv = typeof envValue === "string" ? envValue.trim() : "";
  if (fromEnv) {
    return fromEnv;
  }
  if (typeof pluginValue === "string" && pluginValue.trim()) {
    return pluginValue.trim();
  }
  return fallback;
}

function readPositiveInt(
  envValue: string | undefined,
  pluginValue: unknown,
  fallback: number,
  max: number,
): number {
  const fromEnv = typeof envValue === "string" ? Number.parseInt(envValue.trim(), 10) : Number.NaN;
  if (Number.isFinite(fromEnv) && fromEnv > 0) {
    return Math.min(fromEnv, max);
  }
  if (typeof pluginValue === "number" && Number.isFinite(pluginValue) && pluginValue > 0) {
    return Math.min(Math.floor(pluginValue), max);
  }
  return fallback;
}

function resolveBaseUrl(api: OpenClawPluginApi): string {
  const cfg = api.pluginConfig ?? {};
  return normalizeClawApiBaseUrl(
    readStringConfig(
      process.env.CLAW_API_URL ?? process.env.CLAW_FINANCE_API_URL,
      cfg.clawApiUrl,
      "http://127.0.0.1:9000",
    ),
  );
}

/** 与爬取+LLM 对齐的默认超时（毫秒） */
const DEFAULT_TIMEOUT_MS = 180_000;
const MAX_TIMEOUT_MS = 600_000;

function resolveTimeoutMs(api: OpenClawPluginApi): number {
  const cfg = api.pluginConfig ?? {};
  return readPositiveInt(
    process.env.CLAW_FINANCE_ASK_TIMEOUT_MS,
    cfg.askTimeoutMs,
    DEFAULT_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
  );
}

const MAX_RETRIES = 3;

function resolveMaxRetries(api: OpenClawPluginApi): number {
  const cfg = api.pluginConfig ?? {};
  return readPositiveInt(process.env.CLAW_FINANCE_ASK_RETRIES, cfg.askMaxRetries, 0, MAX_RETRIES);
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

function shouldRetryFetch(status: number): boolean {
  return status === 429 || status === 502 || status === 503 || status === 504;
}

type AskJson = Record<string, unknown>;

export function createFinanceAskTool(api: OpenClawPluginApi) {
  return {
    name: "finance_ask",
    description:
      "Query the claw-finance-agent /ask endpoint for financial Q&A (RAG, disclosure schedules, optional crawl fallback). Use for Chinese market filings, annual reports, and metrics when workspace context is insufficient.",
    parameters: Type.Object(
      {
        question: Type.String({
          description: "User question in natural language (Chinese preferred for domain accuracy).",
        }),
        use_llm: Type.Optional(
          Type.Boolean({
            description:
              "Whether to allow LLM generation after retrieval (default true on server).",
          }),
        ),
        top_k: Type.Optional(
          Type.Number({
            description: "Number of retrieved chunks (default 5 on server).",
            minimum: 1,
            maximum: 50,
          }),
        ),
      },
      { additionalProperties: false },
    ),
    async execute(_id: string, params: Record<string, unknown>) {
      const question = typeof params.question === "string" ? params.question.trim() : "";
      if (!question) {
        throw new Error("question required");
      }

      const baseUrl = resolveBaseUrl(api);
      const url = `${baseUrl}/ask`;
      const timeoutMs = resolveTimeoutMs(api);
      const maxRetries = resolveMaxRetries(api);

      let use_llm: boolean | undefined;
      if (typeof params.use_llm === "boolean") {
        use_llm = params.use_llm;
      }

      let top_k: number | undefined;
      if (typeof params.top_k === "number" && Number.isFinite(params.top_k)) {
        top_k = Math.max(1, Math.min(50, Math.floor(params.top_k)));
      }

      const body: Record<string, unknown> = { question };
      if (use_llm !== undefined) {
        body.use_llm = use_llm;
      }
      if (top_k !== undefined) {
        body.top_k = top_k;
      }

      const started = performance.now();
      api.logger?.info?.(
        `${LOG_PREFIX} start url=${url} timeout_ms=${timeoutMs} retries=${maxRetries} question_preview=${JSON.stringify(question.slice(0, 120))}`,
      );

      let lastStatus = 0;
      let attempt = 0;

      while (attempt <= maxRetries) {
        attempt += 1;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        try {
          const res = await fetch(url, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(body),
            signal: controller.signal,
          });
          lastStatus = res.status;

          const text = await res.text();
          if (!res.ok) {
            if (attempt <= maxRetries && shouldRetryFetch(res.status)) {
              api.logger?.warn?.(
                `${LOG_PREFIX} http_retry status=${res.status} attempt=${attempt}/${maxRetries + 1}`,
              );
              await sleep(400 * attempt);
              continue;
            }
            throw new Error(`${LOG_PREFIX} HTTP ${res.status}: ${text.slice(0, 2000)}`);
          }

          let parsed: AskJson;
          try {
            parsed = JSON.parse(text) as AskJson;
          } catch {
            throw new Error(`${LOG_PREFIX} invalid JSON from /ask`);
          }

          const elapsed = Math.round(performance.now() - started);
          api.logger?.info?.(
            `${LOG_PREFIX} ok status=${res.status} elapsed_ms=${elapsed} used_llm=${String(parsed.used_llm)} retrieval_status=${String(parsed.retrieval_status ?? "")}`,
          );

          return {
            content: [{ type: "text", text: JSON.stringify(parsed, null, 2) }],
            details: parsed,
          };
        } catch (err) {
          const isAbort = err instanceof Error && err.name === "AbortError";
          if (isAbort && attempt <= maxRetries) {
            api.logger?.warn?.(
              `${LOG_PREFIX} timeout_retry attempt=${attempt}/${maxRetries + 1} timeout_ms=${timeoutMs}`,
            );
            continue;
          }
          const elapsed = Math.round(performance.now() - started);
          api.logger?.error?.(
            `${LOG_PREFIX} fail elapsed_ms=${elapsed} last_http_status=${lastStatus} err=${String(err)}`,
          );
          throw err;
        } finally {
          clearTimeout(timer);
        }
      }

      throw new Error(`${LOG_PREFIX} exhausted retries (last HTTP ${lastStatus})`);
    },
  };
}
