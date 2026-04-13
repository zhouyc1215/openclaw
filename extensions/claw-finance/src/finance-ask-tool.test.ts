import { afterEach, describe, expect, it, vi } from "vitest";
import type { OpenClawPluginApi } from "../../../src/plugins/types.js";
import { createFinanceAskTool, normalizeClawApiBaseUrl } from "./finance-ask-tool.js";

describe("normalizeClawApiBaseUrl", () => {
  it("strips trailing slashes", () => {
    expect(normalizeClawApiBaseUrl("http://api:9000/")).toBe("http://api:9000");
    expect(normalizeClawApiBaseUrl("http://api:9000///")).toBe("http://api:9000");
  });
});

describe("createFinanceAskTool", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("POSTs JSON to /ask and returns content + details", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          answer: "ok",
          used_llm: false,
          retrieval_status: "success",
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const logger = { info: vi.fn(), warn: vi.fn(), error: vi.fn() };
    const api = { logger, pluginConfig: {} } as unknown as OpenClawPluginApi;
    const tool = createFinanceAskTool(api);

    const result = await tool.execute("call-1", { question: "测试问题" });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(calledUrl).toMatch(/\/ask$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toMatchObject({ question: "测试问题" });

    expect(result.content[0]?.type).toBe("text");
    expect(JSON.parse(String(result.content[0]?.text))).toMatchObject({
      answer: "ok",
      used_llm: false,
    });
    expect(result.details).toMatchObject({ answer: "ok" });
  });

  it("throws when question missing", async () => {
    const api = {
      logger: { info: vi.fn(), warn: vi.fn(), error: vi.fn() },
    } as unknown as OpenClawPluginApi;
    const tool = createFinanceAskTool(api);
    await expect(tool.execute("x", {})).rejects.toThrow("question required");
  });
});
