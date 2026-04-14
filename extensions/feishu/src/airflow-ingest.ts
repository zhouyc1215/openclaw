import { createHash } from "node:crypto";
import type { FeishuConfig } from "./types.js";

/** Airflow 2.x REST 触发 DAG Run 后的响应体（仅解析常用字段） */
type AirflowDagRunResponse = {
  dag_run_id?: string;
};

export type AirflowIngestParams = {
  /** 合并后的 channels.feishu 配置 */
  feishuCfg: FeishuConfig;
  /** 解析后的用户正文（不含群聊 speaker 前缀） */
  userText: string;
  feishuMessageId: string;
  senderOpenId: string;
  accountId: string;
  log: (...args: unknown[]) => void;
  error: (...args: unknown[]) => void;
};

const DEFAULT_FILING_KEYWORDS = [
  "年报",
  "财报",
  "年度报告",
  "半年度报告",
  "季报",
  "一季报",
  "三季报",
  "巨潮",
  "cninfo",
  "披露",
  "公告",
];

const DEFAULT_RATE_LIMIT_WINDOW_MS = 60_000;
const DEFAULT_RATE_LIMIT_MAX_PER_SENDER = 5;
const DEFAULT_RATE_LIMIT_MAX_GLOBAL = 30;
const DEFAULT_DEDUPE_TTL_MS = 600_000;
const MIN_RATE_LIMIT_WINDOW_MS = 1_000;
const MAX_RATE_LIMIT_WINDOW_MS = 86_400_000;
const MAX_RATE_LIMIT_MAX_PER_SENDER = 1_000;
const MAX_RATE_LIMIT_MAX_GLOBAL = 10_000;

type RateLimitBucket = {
  windowStartedAt: number;
  count: number;
};

const senderRateBuckets = new Map<string, RateLimitBucket>();
const globalRateBuckets = new Map<string, RateLimitBucket>();
const recentIngestKeys = new Map<string, number>();

function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

function hashIdempotency(parts: string[]): string {
  return createHash("sha256").update(parts.join("|")).digest("hex").slice(0, 48);
}

/** 从正文提取 4 位年份（2000–2099） */
function extractFiscalYear(text: string): number | undefined {
  const m = text.match(/\b(20\d{2})\b/);
  if (!m?.[1]) {
    return undefined;
  }
  const y = Number(m[1]);
  return Number.isFinite(y) ? y : undefined;
}

/** 从正文提取 A 股代码：6 位数字，可选 .SH / .SZ */
function extractTsCodeFromDigits(text: string): string | undefined {
  const m = text.match(/\b(\d{6})(\.(SH|SZ))?\b/i);
  if (!m?.[1]) {
    return undefined;
  }
  const num = m[1];
  const suf = m[2]?.toUpperCase();
  if (suf) {
    return `${num}${suf}`;
  }
  // 无后缀时按首位粗分交易所（与常见习惯一致；不确定时由 DAG 再校验）
  if (num.startsWith("6")) {
    return `${num}.SH`;
  }
  return `${num}.SZ`;
}

/** 按配置的证券简称表在正文中查找（优先较长键） */
function resolveTsCodeFromAliases(
  text: string,
  aliases: Record<string, string> | undefined,
): string | undefined {
  if (!aliases || typeof aliases !== "object") {
    return undefined;
  }
  const keys = Object.keys(aliases).sort((a, b) => b.length - a.length);
  for (const key of keys) {
    if (!key.trim()) {
      continue;
    }
    if (text.includes(key)) {
      const code = aliases[key]?.trim();
      if (code) {
        return code;
      }
    }
  }
  return undefined;
}

function hasFilingIntent(text: string, keywords: string[] | undefined): boolean {
  const list = keywords?.length ? keywords : DEFAULT_FILING_KEYWORDS;
  return list.some((k) => k && text.includes(k));
}

function normalizeAllowFromEntries(
  allowFrom: Array<string | number> | undefined,
): Set<string> | null {
  if (!allowFrom?.length) {
    return null;
  }
  const entries = allowFrom
    .map((entry) => String(entry).trim())
    .filter((entry) => entry.length > 0);
  return entries.length ? new Set(entries) : null;
}

function isSenderAllowed(
  senderOpenId: string,
  allowFrom: Array<string | number> | undefined,
): boolean {
  const allowlist = normalizeAllowFromEntries(allowFrom);
  if (!allowlist) {
    return true;
  }
  return allowlist.has("*") || allowlist.has(senderOpenId.trim());
}

function consumeRateLimit(
  buckets: Map<string, RateLimitBucket>,
  key: string,
  now: number,
  windowMs: number,
  limit: number,
): boolean {
  const existing = buckets.get(key);
  if (!existing || now - existing.windowStartedAt >= windowMs) {
    buckets.set(key, { windowStartedAt: now, count: 1 });
    return true;
  }
  if (existing.count >= limit) {
    return false;
  }
  existing.count += 1;
  return true;
}

function pruneExpiredRecentIngestKeys(now: number): void {
  for (const [key, expiresAt] of recentIngestKeys.entries()) {
    if (expiresAt <= now) {
      recentIngestKeys.delete(key);
    }
  }
}

function reserveRecentIngestKey(key: string, now: number, ttlMs: number): boolean {
  pruneExpiredRecentIngestKeys(now);
  const expiresAt = recentIngestKeys.get(key);
  if (expiresAt && expiresAt > now) {
    return false;
  }
  recentIngestKeys.set(key, now + ttlMs);
  return true;
}

function releaseRecentIngestKey(key: string): void {
  recentIngestKeys.delete(key);
}

export function resetAirflowIngestRateLimitStateForTests(): void {
  senderRateBuckets.clear();
  globalRateBuckets.clear();
  recentIngestKeys.clear();
}

function resolveAuth(feishuCfg: FeishuConfig): { user: string; pass: string } | null {
  const ingest = feishuCfg.airflowIngest;
  const user =
    (process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME ?? "").trim() || (ingest?.username ?? "").trim();
  const pass = (process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD ?? "").trim();
  if (!user || !pass) {
    return null;
  }
  return { user, pass };
}

/**
 * 若启用 channels.feishu.airflowIngest 且解析到证券与披露意图，则同步 POST Airflow REST 触发 DAG；失败仅打日志，不抛错。
 */
export async function maybeTriggerAirflowIngest(params: AirflowIngestParams): Promise<void> {
  const { feishuCfg, userText, feishuMessageId, senderOpenId, accountId, log, error } = params;
  const ingest = feishuCfg.airflowIngest;
  if (!ingest?.enabled) {
    return;
  }
  const preview = userText.trim().replace(/\s+/g, " ").slice(0, 120);
  const baseUrl = ingest.baseUrl?.trim();
  const dagId = ingest.dagId?.trim();
  if (!baseUrl || !dagId) {
    log(
      `feishu[${accountId}]: airflow ingest skipped (missing baseUrl or dagId message_id=${feishuMessageId} preview=${preview})`,
    );
    return;
  }

  const text = userText.trim();
  if (!text) {
    return;
  }

  if (!hasFilingIntent(text, ingest.filingKeywords)) {
    return;
  }

  const tsCode =
    resolveTsCodeFromAliases(text, ingest.stockAliases) ?? extractTsCodeFromDigits(text);
  if (!tsCode) {
    log(
      `feishu[${accountId}]: airflow ingest skipped (no ts_code from text message_id=${feishuMessageId} preview=${preview})`,
    );
    return;
  }

  if (!isSenderAllowed(senderOpenId, ingest.allowFrom)) {
    log(
      `feishu[${accountId}]: airflow ingest skipped (sender not allowed message_id=${feishuMessageId} sender_open_id=${senderOpenId} preview=${preview})`,
    );
    return;
  }

  const fiscalYear = extractFiscalYear(text);
  const idempotencyKey = hashIdempotency([
    feishuMessageId,
    dagId,
    tsCode,
    fiscalYear !== undefined ? String(fiscalYear) : "",
  ]);

  const auth = resolveAuth(feishuCfg);
  if (!auth) {
    log(
      `feishu[${accountId}]: airflow ingest skipped (set OPENCLAW_FEISHU_AIRFLOW_USERNAME / OPENCLAW_FEISHU_AIRFLOW_PASSWORD, or username in config + password in env message_id=${feishuMessageId} preview=${preview})`,
    );
    return;
  }

  const windowMs = Math.min(
    Math.max(ingest.rateLimitWindowMs ?? DEFAULT_RATE_LIMIT_WINDOW_MS, MIN_RATE_LIMIT_WINDOW_MS),
    MAX_RATE_LIMIT_WINDOW_MS,
  );
  const senderLimit = Math.min(
    Math.max(ingest.rateLimitMaxPerSender ?? DEFAULT_RATE_LIMIT_MAX_PER_SENDER, 1),
    MAX_RATE_LIMIT_MAX_PER_SENDER,
  );
  const globalLimit = Math.min(
    Math.max(ingest.rateLimitMaxGlobal ?? DEFAULT_RATE_LIMIT_MAX_GLOBAL, 1),
    MAX_RATE_LIMIT_MAX_GLOBAL,
  );
  const dedupeTtlMs = Math.min(
    Math.max(ingest.dedupeTtlMs ?? DEFAULT_DEDUPE_TTL_MS, MIN_RATE_LIMIT_WINDOW_MS),
    MAX_RATE_LIMIT_WINDOW_MS,
  );
  const now = Date.now();
  const recentIngestKey = `${accountId}:${dagId}:${idempotencyKey}`;

  if (!reserveRecentIngestKey(recentIngestKey, now, dedupeTtlMs)) {
    log(
      `feishu[${accountId}]: airflow ingest skipped (duplicate message_id=${feishuMessageId} dag_id=${dagId} idempotency_key=${idempotencyKey} dedupe_ttl_ms=${dedupeTtlMs})`,
    );
    return;
  }

  if (
    !consumeRateLimit(senderRateBuckets, `${accountId}:${senderOpenId}`, now, windowMs, senderLimit)
  ) {
    log(
      `feishu[${accountId}]: airflow ingest skipped (sender rate limited message_id=${feishuMessageId} sender_open_id=${senderOpenId} window_ms=${windowMs} limit=${senderLimit})`,
    );
    return;
  }

  if (!consumeRateLimit(globalRateBuckets, accountId, now, windowMs, globalLimit)) {
    log(
      `feishu[${accountId}]: airflow ingest skipped (global rate limited message_id=${feishuMessageId} window_ms=${windowMs} limit=${globalLimit})`,
    );
    return;
  }

  const timeoutMs = Math.min(Math.max(ingest.timeoutMs ?? 8000, 1000), 120_000);
  const url = `${normalizeBaseUrl(baseUrl)}/api/v1/dags/${encodeURIComponent(dagId)}/dagRuns`;
  const started = Date.now();

  const conf: Record<string, unknown> = {
    idempotency_key: idempotencyKey,
    trigger_source: "openclaw_gateway_feishu",
    ts_code: tsCode,
    feishu_message_id: feishuMessageId,
    sender_open_id: senderOpenId,
  };
  if (fiscalYear !== undefined) {
    conf.fiscal_year = fiscalYear;
  }
  if (ingest.reportType) {
    conf.report_type = ingest.reportType;
  }
  conf.raw_question_preview = preview;

  const body = JSON.stringify({ conf });

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Basic ${Buffer.from(`${auth.user}:${auth.pass}`).toString("base64")}`,
      },
      body,
      signal: AbortSignal.timeout(timeoutMs),
    });

    const latencyMs = Date.now() - started;
    if (!res.ok) {
      releaseRecentIngestKey(recentIngestKey);
      const errText = await res.text().catch(() => "");
      error(
        `feishu[${accountId}]: airflow ingest failed http=${res.status} latency_ms=${latencyMs} dag_id=${dagId} message_id=${feishuMessageId} idempotency_key=${idempotencyKey} body=${errText.slice(0, 500)}`,
      );
      return;
    }

    let dagRunId = "";
    try {
      const json = (await res.json()) as AirflowDagRunResponse;
      dagRunId = json.dag_run_id ?? "";
    } catch {
      // 无 JSON 时仍视为已接受
    }
    log(
      `feishu[${accountId}]: airflow_dag_run_enqueued dag_id=${dagId} dag_run_id=${dagRunId || "(server)"} message_id=${feishuMessageId} idempotency_key=${idempotencyKey} latency_ms=${latencyMs} ts_code=${tsCode}`,
    );
  } catch (e) {
    releaseRecentIngestKey(recentIngestKey);
    const latencyMs = Date.now() - started;
    error(
      `feishu[${accountId}]: airflow ingest error latency_ms=${latencyMs} dag_id=${dagId} message_id=${feishuMessageId} idempotency_key=${idempotencyKey} err=${String(e)}`,
    );
  }
}
