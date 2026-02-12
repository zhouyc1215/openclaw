import { describe, expect, it } from "vitest";
import type { AgentTool } from "@mariozechner/pi-agent-core";
import { toToolDefinitions } from "./pi-tool-definition-adapter.js";
import { ToolRetryGuard } from "./tool-retry-guard.js";

describe("toToolDefinitions with ToolRetryGuard", () => {
  it("blocks tool execution after max failures", async () => {
    const guard = new ToolRetryGuard({ maxConsecutiveFailures: 2, checkParamSimilarity: false });
    
    const failingTool: AgentTool<unknown, unknown> = {
      name: "test_tool",
      description: "A test tool that always fails",
      parameters: {},
      execute: async () => {
        throw new Error("Tool execution failed");
      },
    };

    const defs = toToolDefinitions([failingTool], guard);
    const toolDef = defs[0];

    // First failure
    const result1 = await toolDef.execute("call1", { test: "param" }, undefined, undefined, undefined);
    const content1 = JSON.stringify(result1.content);
    expect(content1).toContain("error");
    expect(content1).toContain("Tool execution failed");

    // Second failure
    const result2 = await toolDef.execute("call2", { test: "param" }, undefined, undefined, undefined);
    const content2 = JSON.stringify(result2.content);
    expect(content2).toContain("error");
    expect(content2).toContain("Tool execution failed");

    // Third attempt should be blocked
    const result3 = await toolDef.execute("call3", { test: "param" }, undefined, undefined, undefined);
    const content3 = JSON.stringify(result3.content);
    expect(content3).toContain("blocked");
    expect(content3).toContain("failed 2 consecutive times");
    expect(content3).toContain("prevent infinite loop");
  });

  it("resets failure count on success", async () => {
    const guard = new ToolRetryGuard({ maxConsecutiveFailures: 2, checkParamSimilarity: false });
    
    let shouldFail = true;
    const intermittentTool: AgentTool<unknown, unknown> = {
      name: "intermittent_tool",
      description: "A tool that fails then succeeds",
      parameters: {},
      execute: async () => {
        if (shouldFail) {
          throw new Error("Temporary failure");
        }
        return { content: JSON.stringify({ status: "ok" }) };
      },
    };

    const defs = toToolDefinitions([intermittentTool], guard);
    const toolDef = defs[0];

    // First failure
    const result1 = await toolDef.execute("call1", { test: "param" }, undefined, undefined, undefined);
    const content1 = JSON.stringify(result1.content);
    expect(content1).toContain("error");

    // Success - failures are still recorded but we can continue
    shouldFail = false;
    const result2 = await toolDef.execute("call2", { test: "param" }, undefined, undefined, undefined);
    const content2 = JSON.stringify(result2.content);
    expect(content2).toContain("ok");

    // Fail again - should not be blocked yet (only 2 total failures, not consecutive)
    shouldFail = true;
    const result3 = await toolDef.execute("call3", { test: "param" }, undefined, undefined, undefined);
    const content3 = JSON.stringify(result3.content);
    expect(content3).toContain("error");
    expect(content3).not.toContain("blocked");
    
    // Another failure - now should be blocked (2 consecutive failures)
    const result4 = await toolDef.execute("call4", { test: "param" }, undefined, undefined, undefined);
    const content4 = JSON.stringify(result4.content);
    expect(content4).toContain("blocked");
  });

  it("works without guard (backward compatibility)", async () => {
    const tool: AgentTool<unknown, unknown> = {
      name: "normal_tool",
      description: "A normal tool",
      parameters: {},
      execute: async () => {
        return { content: JSON.stringify({ status: "ok" }) };
      },
    };

    // No guard provided
    const defs = toToolDefinitions([tool]);
    const toolDef = defs[0];

    const result = await toolDef.execute("call1", {}, undefined, undefined, undefined);
    expect(result.content).toContain("ok");
  });

  it("detects similar parameters", async () => {
    const guard = new ToolRetryGuard({
      maxConsecutiveFailures: 2,
      checkParamSimilarity: true,
    });
    
    const failingTool: AgentTool<unknown, unknown> = {
      name: "param_tool",
      description: "A tool that checks params",
      parameters: {},
      execute: async () => {
        throw new Error("Invalid params");
      },
    };

    const defs = toToolDefinitions([failingTool], guard);
    const toolDef = defs[0];

    // Fail with same params twice
    await toolDef.execute("call1", { action: "add", name: "test" }, undefined, undefined, undefined);
    await toolDef.execute("call2", { action: "add", name: "test" }, undefined, undefined, undefined);

    // Third attempt with same params should be blocked
    const result3 = await toolDef.execute(
      "call3",
      { action: "add", name: "test" },
      undefined,
      undefined,
      undefined,
    );
    const content3 = JSON.stringify(result3.content);
    expect(content3).toContain("blocked");
  });
});
