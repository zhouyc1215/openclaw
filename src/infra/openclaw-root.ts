<<<<<<< HEAD
=======
import fsSync from "node:fs";
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

<<<<<<< HEAD
// 简化版：只支持 clawdbot (适配 v2026.1.24-1)
const CORE_PACKAGE_NAMES = new Set(["clawdbot"]);
=======
const CORE_PACKAGE_NAMES = new Set(["openclaw"]);
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c

async function readPackageName(dir: string): Promise<string | null> {
  try {
    const raw = await fs.readFile(path.join(dir, "package.json"), "utf-8");
    const parsed = JSON.parse(raw) as { name?: unknown };
    return typeof parsed.name === "string" ? parsed.name : null;
  } catch {
    return null;
  }
}

<<<<<<< HEAD
=======
function readPackageNameSync(dir: string): string | null {
  try {
    const raw = fsSync.readFileSync(path.join(dir, "package.json"), "utf-8");
    const parsed = JSON.parse(raw) as { name?: unknown };
    return typeof parsed.name === "string" ? parsed.name : null;
  } catch {
    return null;
  }
}

>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c
async function findPackageRoot(startDir: string, maxDepth = 12): Promise<string | null> {
  let current = path.resolve(startDir);
  for (let i = 0; i < maxDepth; i += 1) {
    const name = await readPackageName(current);
<<<<<<< HEAD
    if (name && CORE_PACKAGE_NAMES.has(name)) return current;
    const parent = path.dirname(current);
    if (parent === current) break;
=======
    if (name && CORE_PACKAGE_NAMES.has(name)) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }
  return null;
}

function findPackageRootSync(startDir: string, maxDepth = 12): string | null {
  let current = path.resolve(startDir);
  for (let i = 0; i < maxDepth; i += 1) {
    const name = readPackageNameSync(current);
    if (name && CORE_PACKAGE_NAMES.has(name)) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c
    current = parent;
  }
  return null;
}

function candidateDirsFromArgv1(argv1: string): string[] {
  const normalized = path.resolve(argv1);
  const candidates = [path.dirname(normalized)];
  const parts = normalized.split(path.sep);
  const binIndex = parts.lastIndexOf(".bin");
  if (binIndex > 0 && parts[binIndex - 1] === "node_modules") {
    const binName = path.basename(normalized);
    const nodeModulesDir = parts.slice(0, binIndex).join(path.sep);
    candidates.push(path.join(nodeModulesDir, binName));
  }
  return candidates;
}

export async function resolveOpenClawPackageRoot(opts: {
  cwd?: string;
  argv1?: string;
  moduleUrl?: string;
}): Promise<string | null> {
  const candidates: string[] = [];

  if (opts.moduleUrl) {
    candidates.push(path.dirname(fileURLToPath(opts.moduleUrl)));
  }
  if (opts.argv1) {
    candidates.push(...candidateDirsFromArgv1(opts.argv1));
  }
  if (opts.cwd) {
    candidates.push(opts.cwd);
  }

  for (const candidate of candidates) {
<<<<<<< HEAD
    const root = await findPackageRoot(candidate);
    if (root) return root;
=======
    const found = await findPackageRoot(candidate);
    if (found) {
      return found;
    }
  }

  return null;
}

export function resolveOpenClawPackageRootSync(opts: {
  cwd?: string;
  argv1?: string;
  moduleUrl?: string;
}): string | null {
  const candidates: string[] = [];

  if (opts.moduleUrl) {
    candidates.push(path.dirname(fileURLToPath(opts.moduleUrl)));
  }
  if (opts.argv1) {
    candidates.push(...candidateDirsFromArgv1(opts.argv1));
  }
  if (opts.cwd) {
    candidates.push(opts.cwd);
  }

  for (const candidate of candidates) {
    const found = findPackageRootSync(candidate);
    if (found) {
      return found;
    }
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c
  }

  return null;
}
