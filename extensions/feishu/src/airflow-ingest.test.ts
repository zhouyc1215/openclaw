import { afterEach, describe, expect, it, vi } from "vitest";
import type { FeishuConfig } from "./types.js";
import {
  maybeTriggerAirflowIngest,
  resetAirflowIngestRateLimitStateForTests,
} from "./airflow-ingest.js";

describe("maybeTriggerAirflowIngest", () => {
  const log = vi.fn();
  const error = vi.fn();

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    resetAirflowIngestRateLimitStateForTests();
    delete process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME;
    delete process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD;
    log.mockReset();
    error.mockReset();
  });

  it("未启用时不请求 Airflow", async () => {
    const feishuCfg = { airflowIngest: { enabled: false } } as FeishuConfig;
    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "浪潮信息 2025 年报",
      feishuMessageId: "om_x1",
      senderOpenId: "ou_1",
      accountId: "default",
      log,
      error,
    });
    expect(log).not.toHaveBeenCalledWith(expect.stringMatching(/airflow_dag_run_enqueued/));
  });

  it("缺少鉴权环境变量时跳过并打日志", async () => {
    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
      },
    } as FeishuConfig;
    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "000977 2025 年报下载",
      feishuMessageId: "om_x2",
      senderOpenId: "ou_1",
      accountId: "default",
      log,
      error,
    });
    expect(log.mock.calls.some((c) => String(c[0]).includes("skipped"))).toBe(true);
  });

  it("无法解析证券代码时日志包含 message_id 和正文预览", async () => {
    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
      },
    } as FeishuConfig;

    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "请拉取工业互联网龙头公司今年财报",
      feishuMessageId: "om_no_code_1",
      senderOpenId: "ou_no_code_1",
      accountId: "default",
      log,
      error,
    });

    expect(
      log.mock.calls.some(
        (c) =>
          String(c[0]).includes("no ts_code from text") &&
          String(c[0]).includes("message_id=om_no_code_1") &&
          String(c[0]).includes("preview=请拉取工业互联网龙头公司今年财报"),
      ),
    ).toBe(true);
  });

  it("命中关键词与 6 位代码时 POST dagRuns", async () => {
    process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME = "u";
    process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD = "p";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ dag_run_id: "dr_manual_1" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test/",
        dagId: "ingest_pdf",
        timeoutMs: 5000,
      },
    } as FeishuConfig;

    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "请拉取 000977.SZ 的 2025 年度报告 PDF",
      feishuMessageId: "om_x3",
      senderOpenId: "ou_2",
      accountId: "default",
      log,
      error,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("https://airflow.test/api/v1/dags/ingest_pdf/dagRuns");
    expect(init.method).toBe("POST");
    const body = JSON.parse(String(init.body)) as { conf: Record<string, unknown> };
    expect(body.conf.ts_code).toBe("000977.SZ");
    expect(body.conf.fiscal_year).toBe(2025);
    expect(body.conf.trigger_source).toBe("openclaw_gateway_feishu");
    expect(String(body.conf.idempotency_key)).toHaveLength(48);
    expect(
      log.mock.calls.some(
        (c) =>
          String(c[0]).includes("airflow_dag_run_enqueued") &&
          String(c[0]).includes("message_id=om_x3") &&
          String(c[0]).includes("idempotency_key="),
      ),
    ).toBe(true);
  });

  it("stockAliases 优先于数字解析", async () => {
    process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME = "u";
    process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD = "p";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ dag_run_id: "dr_2" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
        stockAliases: { 浪潮信息: "000977.SZ" },
      },
    } as FeishuConfig;

    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "获取浪潮信息2025年财报并分析",
      feishuMessageId: "om_x4",
      senderOpenId: "ou_3",
      accountId: "default",
      log,
      error,
    });

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const body = JSON.parse(String(init.body)) as { conf: Record<string, unknown> };
    expect(body.conf.ts_code).toBe("000977.SZ");
  });

  it("配置 allowFrom 时仅白名单 sender 可触发", async () => {
    process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME = "u";
    process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD = "p";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
        allowFrom: ["ou_allowed"],
      },
    } as FeishuConfig;

    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "请拉取 000977.SZ 的 2025 年报",
      feishuMessageId: "om_x5",
      senderOpenId: "ou_blocked",
      accountId: "default",
      log,
      error,
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(log.mock.calls.some((c) => String(c[0]).includes("sender not allowed"))).toBe(true);
  });

  it("同一 sender 超过窗口限额后跳过", async () => {
    process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME = "u";
    process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD = "p";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ dag_run_id: "dr_sender_limit" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
        rateLimitWindowMs: 60_000,
        rateLimitMaxPerSender: 1,
        rateLimitMaxGlobal: 10,
      },
    } as FeishuConfig;

    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "请拉取 000977.SZ 的 2025 年报",
      feishuMessageId: "om_x6",
      senderOpenId: "ou_limit_1",
      accountId: "default",
      log,
      error,
    });
    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "请拉取 000977.SZ 的 2025 年报",
      feishuMessageId: "om_x7",
      senderOpenId: "ou_limit_1",
      accountId: "default",
      log,
      error,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(log.mock.calls.some((c) => String(c[0]).includes("sender rate limited"))).toBe(true);
  });

  it("账号全局超过窗口限额后跳过", async () => {
    process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME = "u";
    process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD = "p";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ dag_run_id: "dr_global_limit" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
        rateLimitWindowMs: 60_000,
        rateLimitMaxPerSender: 5,
        rateLimitMaxGlobal: 1,
      },
    } as FeishuConfig;

    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "请拉取 000977.SZ 的 2025 年报",
      feishuMessageId: "om_x8",
      senderOpenId: "ou_global_1",
      accountId: "default",
      log,
      error,
    });
    await maybeTriggerAirflowIngest({
      feishuCfg,
      userText: "请拉取 000001.SZ 的 2025 年报",
      feishuMessageId: "om_x9",
      senderOpenId: "ou_global_2",
      accountId: "default",
      log,
      error,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(log.mock.calls.some((c) => String(c[0]).includes("global rate limited"))).toBe(true);
  });

  it("同一飞书消息重复投递时只触发一次 Airflow", async () => {
    process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME = "u";
    process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD = "p";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ dag_run_id: "dr_dedupe" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
        dedupeTtlMs: 600_000,
        stockAliases: { 浪潮信息: "000977.SZ" },
      },
    } as FeishuConfig;

    const params = {
      feishuCfg,
      userText: "请拉取浪潮信息2025年财报",
      feishuMessageId: "om_dup_1",
      senderOpenId: "ou_dup_1",
      accountId: "default",
      log,
      error,
    };

    await maybeTriggerAirflowIngest(params);
    await maybeTriggerAirflowIngest(params);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(log.mock.calls.some((c) => String(c[0]).includes("duplicate message_id=om_dup_1"))).toBe(
      true,
    );
  });

  it("首次触发失败时释放去重键以允许重试", async () => {
    process.env.OPENCLAW_FEISHU_AIRFLOW_USERNAME = "u";
    process.env.OPENCLAW_FEISHU_AIRFLOW_PASSWORD = "p";
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => "boom",
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ dag_run_id: "dr_retry" }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const feishuCfg = {
      airflowIngest: {
        enabled: true,
        baseUrl: "https://airflow.test",
        dagId: "ingest_pdf",
        dedupeTtlMs: 600_000,
        stockAliases: { 浪潮信息: "000977.SZ" },
      },
    } as FeishuConfig;

    const params = {
      feishuCfg,
      userText: "请拉取浪潮信息2025年财报",
      feishuMessageId: "om_dup_retry",
      senderOpenId: "ou_dup_retry",
      accountId: "default",
      log,
      error,
    };

    await maybeTriggerAirflowIngest(params);
    await maybeTriggerAirflowIngest(params);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(error.mock.calls.some((c) => String(c[0]).includes("http=500"))).toBe(true);
  });
});
