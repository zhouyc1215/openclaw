import { describe, expect, it } from "vitest";
import { ToolRetryGuard } from "./tool-retry-guard.js";

describe("ToolRetryGuard", () => {
  it("allows tool calls initially", () => {
    const guard = new ToolRetryGuard();
    const result = guard.shouldBlockTool("test_tool");
    expect(result.blocked).toBe(false);
  });

  it("blocks tool after max consecutive failures", () => {
    const guard = new ToolRetryGuard({ maxConsecutiveFailures: 3 });

    // Record 3 failures
    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now() });
    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now() });
    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now() });

    const result = guard.shouldBlockTool("test_tool");
    expect(result.blocked).toBe(true);
    expect(result.failureCount).toBe(3);
  });

  it("does not block different tools", () => {
    const guard = new ToolRetryGuard({ maxConsecutiveFailures: 2 });

    guard.recordFailure({ toolName: "tool_a", timestamp: Date.now() });
    guard.recordFailure({ toolName: "tool_a", timestamp: Date.now() });

    const resultA = guard.shouldBlockTool("tool_a");
    const resultB = guard.shouldBlockTool("tool_b");

    expect(resultA.blocked).toBe(true);
    expect(resultB.blocked).toBe(false);
  });

  it("cleans up old failures outside time window", () => {
    const guard = new ToolRetryGuard({
      maxConsecutiveFailures: 2,
      failureWindowMs: 1000, // 1 second
    });

    // Record old failure
    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now() - 2000 });

    // Record recent failure
    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now() });

    const result = guard.shouldBlockTool("test_tool");
    expect(result.blocked).toBe(false); // Only 1 recent failure
  });

  it("checks parameter similarity when enabled", () => {
    const guard = new ToolRetryGuard({
      maxConsecutiveFailures: 2,
      checkParamSimilarity: true,
    });

    const params1 = { action: "update", doc_token: "abc123" };
    const params2 = { action: "update", doc_token: "abc123" };
    const params3 = { action: "delete", doc_token: "xyz789" };

    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now(), params: params1 });
    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now(), params: params2 });

    // Should block with similar params
    const result1 = guard.shouldBlockTool("test_tool", params1);
    expect(result1.blocked).toBe(true);

    // Should not block with different params
    const result2 = guard.shouldBlockTool("test_tool", params3);
    expect(result2.blocked).toBe(false);
  });

  it("provides failure statistics", () => {
    const guard = new ToolRetryGuard();

    guard.recordFailure({ toolName: "tool_a", timestamp: Date.now() });
    guard.recordFailure({ toolName: "tool_a", timestamp: Date.now() });
    guard.recordFailure({ toolName: "tool_b", timestamp: Date.now() });

    const stats = guard.getStats();
    expect(stats.totalFailures).toBe(3);
    expect(stats.failuresByTool["tool_a"]).toBe(2);
    expect(stats.failuresByTool["tool_b"]).toBe(1);
  });

  it("resets all failures", () => {
    const guard = new ToolRetryGuard();

    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now() });
    guard.recordFailure({ toolName: "test_tool", timestamp: Date.now() });

    guard.reset();

    const result = guard.shouldBlockTool("test_tool");
    expect(result.blocked).toBe(false);

    const stats = guard.getStats();
    expect(stats.totalFailures).toBe(0);
  });
});
