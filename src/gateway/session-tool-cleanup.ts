import fs from "node:fs/promises";
import path from "node:path";
import { resolveStateDir } from "../config/paths.js";

/**
 * Clean tool calls from session transcripts when tools are disabled.
 * This prevents models from learning tool call patterns from history.
 */

type SessionMessage = {
  type: string;
  message?: {
    role?: string;
    content?: Array<{ type: string; [key: string]: unknown }>;
  };
  [key: string]: unknown;
};

/**
 * Check if a message contains tool calls or tool results
 */
function isToolRelatedMessage(msg: SessionMessage): boolean {
  if (msg.type === "toolResult") return true;

  if (msg.type === "message" && msg.message?.role === "assistant") {
    const content = msg.message.content;
    if (Array.isArray(content)) {
      return content.some((item) => item.type === "toolCall");
    }
  }

  return false;
}

/**
 * Clean tool calls from a single session transcript file
 */
async function cleanSessionTranscript(filePath: string): Promise<{
  cleaned: boolean;
  removedCount: number;
}> {
  try {
    const content = await fs.readFile(filePath, "utf8");
    const lines = content.split("\n").filter((line) => line.trim());

    const messages: SessionMessage[] = [];
    let removedCount = 0;

    for (const line of lines) {
      try {
        const msg = JSON.parse(line) as SessionMessage;

        // Keep non-tool-related messages
        if (!isToolRelatedMessage(msg)) {
          messages.push(msg);
        } else {
          removedCount++;
        }
      } catch {
        // Keep malformed lines as-is
        messages.push({ type: "unknown", raw: line });
      }
    }

    if (removedCount === 0) {
      return { cleaned: false, removedCount: 0 };
    }

    // Write back the cleaned transcript
    const newContent = messages.map((msg) => JSON.stringify(msg)).join("\n") + "\n";
    await fs.writeFile(filePath, newContent, "utf8");

    return { cleaned: true, removedCount };
  } catch (err) {
    // If file doesn't exist or can't be read, skip it
    return { cleaned: false, removedCount: 0 };
  }
}

/**
 * Clean tool calls from all session transcripts in the state directory
 */
export async function cleanAllSessionTranscripts(opts?: {
  stateDir?: string;
  log?: (msg: string) => void;
}): Promise<{
  processedFiles: number;
  cleanedFiles: number;
  totalRemoved: number;
}> {
  const stateDir = opts?.stateDir ?? resolveStateDir();
  const log = opts?.log ?? (() => {});

  let processedFiles = 0;
  let cleanedFiles = 0;
  let totalRemoved = 0;

  try {
    const agentsDir = path.join(stateDir, "agents");

    // Check if agents directory exists
    try {
      await fs.access(agentsDir);
    } catch {
      log("No agents directory found, skipping session cleanup");
      return { processedFiles: 0, cleanedFiles: 0, totalRemoved: 0 };
    }

    // Iterate through all agent directories
    const agentDirs = await fs.readdir(agentsDir);

    for (const agentId of agentDirs) {
      const sessionsDir = path.join(agentsDir, agentId, "sessions");

      try {
        await fs.access(sessionsDir);
      } catch {
        continue; // Skip if sessions directory doesn't exist
      }

      // Find all .jsonl files (session transcripts)
      const files = await fs.readdir(sessionsDir);
      const transcriptFiles = files.filter((f) => f.endsWith(".jsonl") && !f.endsWith(".lock"));

      for (const file of transcriptFiles) {
        const filePath = path.join(sessionsDir, file);
        processedFiles++;

        const result = await cleanSessionTranscript(filePath);

        if (result.cleaned) {
          cleanedFiles++;
          totalRemoved += result.removedCount;
          log(
            `Cleaned ${result.removedCount} tool-related messages from ${agentId}/sessions/${file}`,
          );
        }
      }
    }

    if (cleanedFiles > 0) {
      log(
        `Session cleanup complete: processed ${processedFiles} files, cleaned ${cleanedFiles} files, removed ${totalRemoved} tool-related messages`,
      );
    } else {
      log(`Session cleanup complete: processed ${processedFiles} files, no tool calls found`);
    }
  } catch (err) {
    log(`Session cleanup error: ${String(err)}`);
  }

  return { processedFiles, cleanedFiles, totalRemoved };
}

/**
 * Check if tools.deny configuration disables all tools
 */
export function areAllToolsDisabled(toolsDeny: unknown): boolean {
  if (!Array.isArray(toolsDeny)) return false;
  return toolsDeny.includes("*");
}
