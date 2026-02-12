/**
 * Tool Retry Guard - Prevents infinite loops from repeated tool call failures
 *
 * Tracks tool call failures and stops execution when the same tool fails too many times
 * with the same or similar parameters.
 */

export type ToolCallFailure = {
  toolName: string;
  timestamp: number;
  errorMessage?: string;
  params?: Record<string, unknown>;
};

export type ToolRetryGuardConfig = {
  /** Maximum consecutive failures for the same tool before stopping */
  maxConsecutiveFailures?: number;
  /** Time window in ms to consider failures as consecutive (default: 5 minutes) */
  failureWindowMs?: number;
  /** Whether to check parameter similarity (default: true) */
  checkParamSimilarity?: boolean;
};

const DEFAULT_MAX_CONSECUTIVE_FAILURES = 3;
const DEFAULT_FAILURE_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Guard to prevent tool call retry loops
 */
export class ToolRetryGuard {
  private failures: ToolCallFailure[] = [];
  private config: Required<ToolRetryGuardConfig>;

  constructor(config?: ToolRetryGuardConfig) {
    this.config = {
      maxConsecutiveFailures: config?.maxConsecutiveFailures ?? DEFAULT_MAX_CONSECUTIVE_FAILURES,
      failureWindowMs: config?.failureWindowMs ?? DEFAULT_FAILURE_WINDOW_MS,
      checkParamSimilarity: config?.checkParamSimilarity ?? true,
    };
  }

  /**
   * Record a tool call failure
   */
  recordFailure(failure: ToolCallFailure): void {
    this.failures.push({
      ...failure,
      timestamp: failure.timestamp || Date.now(),
    });

    // Clean up old failures outside the window
    this.cleanupOldFailures();
  }

  /**
   * Check if a tool should be blocked due to too many failures
   */
  shouldBlockTool(toolName: string, params?: Record<string, unknown>): {
    blocked: boolean;
    reason?: string;
    failureCount?: number;
  } {
    this.cleanupOldFailures();

    const recentFailures = this.getRecentFailures(toolName);

    if (recentFailures.length === 0) {
      return { blocked: false };
    }

    // Check consecutive failures
    if (recentFailures.length >= this.config.maxConsecutiveFailures) {
      // If checking param similarity, verify they're similar
      if (this.config.checkParamSimilarity && params) {
        const similarFailures = recentFailures.filter((f) =>
          this.areParamsSimilar(f.params, params),
        );

        if (similarFailures.length >= this.config.maxConsecutiveFailures) {
          return {
            blocked: true,
            reason: `Tool "${toolName}" failed ${similarFailures.length} times with similar parameters`,
            failureCount: similarFailures.length,
          };
        }
      } else {
        return {
          blocked: true,
          reason: `Tool "${toolName}" failed ${recentFailures.length} consecutive times`,
          failureCount: recentFailures.length,
        };
      }
    }

    return { blocked: false };
  }

  /**
   * Get recent failures for a specific tool
   */
  private getRecentFailures(toolName: string): ToolCallFailure[] {
    const now = Date.now();
    return this.failures.filter(
      (f) =>
        f.toolName === toolName && now - f.timestamp <= this.config.failureWindowMs,
    );
  }

  /**
   * Clean up failures outside the time window
   */
  private cleanupOldFailures(): void {
    const now = Date.now();
    this.failures = this.failures.filter(
      (f) => now - f.timestamp <= this.config.failureWindowMs,
    );
  }

  /**
   * Check if two parameter sets are similar
   * (same keys and similar values)
   */
  private areParamsSimilar(
    params1?: Record<string, unknown>,
    params2?: Record<string, unknown>,
  ): boolean {
    if (!params1 || !params2) return false;

    const keys1 = Object.keys(params1).sort();
    const keys2 = Object.keys(params2).sort();

    // Check if keys are the same
    if (keys1.length !== keys2.length) return false;
    if (!keys1.every((k, i) => k === keys2[i])) return false;

    // Check if values are similar (simple string comparison)
    let similarCount = 0;
    for (const key of keys1) {
      const val1 = String(params1[key]);
      const val2 = String(params2[key]);

      if (val1 === val2) {
        similarCount++;
      }
    }

    // Consider similar if >70% of values match
    return similarCount / keys1.length > 0.7;
  }

  /**
   * Reset the guard (clear all failures)
   */
  reset(): void {
    this.failures = [];
  }

  /**
   * Get current failure statistics
   */
  getStats(): {
    totalFailures: number;
    failuresByTool: Record<string, number>;
    recentFailures: number;
  } {
    this.cleanupOldFailures();

    const failuresByTool: Record<string, number> = {};
    for (const failure of this.failures) {
      failuresByTool[failure.toolName] = (failuresByTool[failure.toolName] || 0) + 1;
    }

    return {
      totalFailures: this.failures.length,
      failuresByTool,
      recentFailures: this.failures.length,
    };
  }
}

/**
 * Create a tool retry guard with default configuration
 */
export function createToolRetryGuard(config?: ToolRetryGuardConfig): ToolRetryGuard {
  return new ToolRetryGuard(config);
}
