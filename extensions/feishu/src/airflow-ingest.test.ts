import { afterEach, describe, expect, it, vi } from "vitest";
import type { FeishuConfig } from "./types.js";
import { maybeTriggerAirflowIngest } from "./airflow-ingest.js";

describe("maybeTriggerAirflowIngest", () => {
  const log = vi.fn();
  const error = vi.fn();

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
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
    expect(log.mock.calls.some((c) => String(c[0]).includes("airflow_dag_run_enqueued"))).toBe(
      true,
    );
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
});
