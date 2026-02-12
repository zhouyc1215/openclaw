import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
<<<<<<< HEAD

import { describe, expect, it } from "vitest";

=======
import { describe, expect, it } from "vitest";
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c
import {
  resetWorkspaceTemplateDirCache,
  resolveWorkspaceTemplateDir,
} from "./workspace-templates.js";

async function makeTempRoot(): Promise<string> {
<<<<<<< HEAD
  return await fs.mkdtemp(path.join(os.tmpdir(), "clawdbot-templates-"));
=======
  return await fs.mkdtemp(path.join(os.tmpdir(), "openclaw-templates-"));
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c
}

describe("resolveWorkspaceTemplateDir", () => {
  it("resolves templates from package root when module url is dist-rooted", async () => {
    resetWorkspaceTemplateDirCache();
    const root = await makeTempRoot();
<<<<<<< HEAD
    await fs.writeFile(path.join(root, "package.json"), JSON.stringify({ name: "clawdbot" }));
=======
    await fs.writeFile(path.join(root, "package.json"), JSON.stringify({ name: "openclaw" }));
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c

    const templatesDir = path.join(root, "docs", "reference", "templates");
    await fs.mkdir(templatesDir, { recursive: true });
    await fs.writeFile(path.join(templatesDir, "AGENTS.md"), "# ok\n");

    const distDir = path.join(root, "dist");
    await fs.mkdir(distDir, { recursive: true });
    const moduleUrl = pathToFileURL(path.join(distDir, "model-selection.mjs")).toString();

    const resolved = await resolveWorkspaceTemplateDir({ cwd: distDir, moduleUrl });
    expect(resolved).toBe(templatesDir);
  });
});
