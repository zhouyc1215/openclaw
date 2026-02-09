# Clawdbot Bug 分析报告

## 🐛 Bug 确认

**结论**: ✅ **这是一个已确认的 Bug，并且已在后续版本中修复**

---

## 📋 Bug 详情

### Bug 描述

在 v2026.1.24-1 版本中，当 Gateway 启动失败时，Clawdbot 会 fallback 到 embedded 模式。但 embedded 模式在加载工作空间模板文件时，使用了错误的路径解析逻辑，导致无法找到模板文件。

### 错误信息

```
Gateway agent failed; falling back to embedded: Error: Error: Missing workspace template: AGENTS.md (/home/tsl/docs/reference/templates/AGENTS.md). Ensure docs/reference/templates are packaged.
```

### 问题代码 (v2026.1.24-1)

**文件**: `src/agents/workspace.ts`

```typescript
const TEMPLATE_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../docs/reference/templates",
);

async function loadTemplate(name: string): Promise<string> {
  const templatePath = path.join(TEMPLATE_DIR, name);
  try {
    const content = await fs.readFile(templatePath, "utf-8");
    return stripFrontMatter(content);
  } catch {
    throw new Error(
      `Missing workspace template: ${name} (${templatePath}). Ensure docs/reference/templates are packaged.`,
    );
  }
}
```

### 问题分析

**路径计算逻辑**:
```
TEMPLATE_DIR = path.dirname(fileURLToPath(import.meta.url)) + "../../docs/reference/templates"
```

**不同场景下的路径**:

1. **开发环境** (源码目录):
   - `import.meta.url`: `file:///home/tsl/openclaw/src/agents/workspace.ts`
   - `TEMPLATE_DIR`: `/home/tsl/openclaw/docs/reference/templates` ✅ 正确

2. **全局安装** (npm link):
   - `import.meta.url`: `file:///usr/lib/node_modules/clawdbot/dist/agents/workspace.js`
   - `TEMPLATE_DIR`: `/usr/lib/node_modules/clawdbot/docs/reference/templates` ✅ 正确

3. **当前工作目录运行** (embedded 模式):
   - `import.meta.url`: `file:///usr/lib/node_modules/clawdbot/dist/agents/workspace.js`
   - 当前目录: `/home/tsl/openclaw`
   - `TEMPLATE_DIR`: `/usr/lib/node_modules/clawdbot/docs/reference/templates` ✅ 应该正确
   - **实际错误路径**: `/home/tsl/docs/reference/templates` ❌ 错误

**根本原因**: 
在某些情况下（可能是符号链接或特殊的模块加载路径），`import.meta.url` 的解析会受到当前工作目录的影响，导致路径计算错误。

---

## ✅ Bug 修复

### 修复提交

**Commit**: `ddc5683c675d77427a06a3fb8b79b186e9723a2e`
**作者**: Peter Steinberger <steipete@gmail.com>
**日期**: 2026-01-31 09:07:41 +0000
**标题**: fix: resolve workspace templates from package root

### 修复版本

该修复包含在以下版本中：
- ✅ **v2026.1.30** (2026-01-31)
- ✅ **v2026.2.1** (2026-02-02)
- ✅ **v2026.2.2** (2026-02-03)
- ✅ **v2026.2.3** (2026-02-04)
- ✅ **v2026.2.4** (2026-02-05)

**当前使用版本**: ❌ v2026.1.24-1 (2026-01-24) - **不包含修复**

**版本差距**: 499 个提交 (v2026.1.24-1 → ddc5683c6)

---

## 🔧 修复方案

### 新增文件: `src/agents/workspace-templates.ts`

```typescript
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveOpenClawPackageRoot } from "../infra/openclaw-root.js";

const FALLBACK_TEMPLATE_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../docs/reference/templates",
);

let cachedTemplateDir: string | undefined;
let resolvingTemplateDir: Promise<string> | undefined;

async function pathExists(candidate: string): Promise<boolean> {
  try {
    await fs.access(candidate);
    return true;
  } catch {
    return false;
  }
}

export async function resolveWorkspaceTemplateDir(opts?: {
  cwd?: string;
  argv1?: string;
  moduleUrl?: string;
}): Promise<string> {
  if (cachedTemplateDir) {
    return cachedTemplateDir;
  }
  if (resolvingTemplateDir) {
    return resolvingTemplateDir;
  }

  resolvingTemplateDir = (async () => {
    const moduleUrl = opts?.moduleUrl ?? import.meta.url;
    const argv1 = opts?.argv1 ?? process.argv[1];
    const cwd = opts?.cwd ?? process.cwd();

    // 🔑 关键改进：使用 package root 解析
    const packageRoot = await resolveOpenClawPackageRoot({ moduleUrl, argv1, cwd });
    const candidates = [
      packageRoot ? path.join(packageRoot, "docs", "reference", "templates") : null,
      cwd ? path.resolve(cwd, "docs", "reference", "templates") : null,
      FALLBACK_TEMPLATE_DIR,
    ].filter(Boolean) as string[];

    // 🔑 关键改进：尝试多个候选路径
    for (const candidate of candidates) {
      if (await pathExists(candidate)) {
        cachedTemplateDir = candidate;
        return candidate;
      }
    }

    cachedTemplateDir = candidates[0] ?? FALLBACK_TEMPLATE_DIR;
    return cachedTemplateDir;
  })();

  try {
    return await resolvingTemplateDir;
  } finally {
    resolvingTemplateDir = undefined;
  }
}
```

### 修改文件: `src/agents/workspace.ts`

```typescript
// 旧代码 (v2026.1.24-1)
const TEMPLATE_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../docs/reference/templates",
);

async function loadTemplate(name: string): Promise<string> {
  const templatePath = path.join(TEMPLATE_DIR, name);
  // ...
}

// 新代码 (v2026.1.30+)
import { resolveWorkspaceTemplateDir } from "./workspace-templates.js";

async function loadTemplate(name: string): Promise<string> {
  const templateDir = await resolveWorkspaceTemplateDir();  // 🔑 动态解析
  const templatePath = path.join(templateDir, name);
  // ...
}
```

### 修复的关键改进

1. **Package Root 解析**: 使用 `resolveOpenClawPackageRoot()` 从 package.json 定位包根目录
2. **多候选路径**: 尝试多个可能的模板目录位置
3. **路径存在性检查**: 在使用前验证路径是否存在
4. **缓存机制**: 缓存解析结果以提高性能
5. **Fallback 机制**: 如果所有候选路径都失败，使用默认 fallback 路径

---

## 🎯 解决方案

### 方案 1: 升级到最新版本 ⭐⭐⭐⭐⭐ (强烈推荐)

```bash
# 升级到包含修复的版本
sudo npm install -g clawdbot@latest

# 或升级到特定版本
sudo npm install -g clawdbot@2026.1.30
```

**优点**:
- ✅ 彻底解决 bug
- ✅ 获得其他 bug 修复和新功能
- ✅ 官方支持的解决方案

**缺点**:
- ⚠️ 可能引入其他变更（499 个提交）

---

### 方案 2: 手动应用补丁 ⭐⭐⭐ (临时方案)

```bash
# 切换到源码目录
cd ~/openclaw

# Cherry-pick 修复提交
git cherry-pick ddc5683c675d77427a06a3fb8b79b186e9723a2e

# 重新编译
pnpm build

# 重新安装
sudo npm link
```

**优点**:
- ✅ 只应用 bug 修复，不引入其他变更
- ✅ 保持在 v2026.1.24-1 基础上

**缺点**:
- ⚠️ 可能有依赖冲突
- ⚠️ 需要手动维护

---

### 方案 3: 修复 Gateway 问题 ⭐⭐ (绕过 bug)

```bash
# 杀死旧的 Gateway 进程
kill -9 97715
# 或
pkill -9 -f "openclaw-gateway"

# 重启 Gateway
clawdbot gateway stop
clawdbot gateway start

# 验证状态
clawdbot gateway status
```

**优点**:
- ✅ 避免触发 embedded 模式
- ✅ 不需要升级或修改代码

**缺点**:
- ❌ 不解决根本问题
- ❌ Gateway 再次失败时仍会遇到 bug

---

### 方案 4: 直接使用 Ollama ⭐⭐⭐⭐ (最简单)

```bash
# 对于简单查询，直接使用 Ollama
ollama run qwen2.5:3b "你的问题"
```

**优点**:
- ✅ 完全绕过 Clawdbot
- ✅ 性能最佳 (8.7秒 vs >90秒)
- ✅ 无需修复任何问题

**缺点**:
- ❌ 失去 Clawdbot 的高级功能（上下文、工具调用）

---

## 📊 影响范围

### 受影响的版本

- ❌ v2026.1.24
- ❌ v2026.1.24-1
- ❌ v2026.1.25 - v2026.1.29 (如果存在)

### 已修复的版本

- ✅ v2026.1.30+
- ✅ v2026.2.x (所有版本)

### 触发条件

该 bug 只在以下情况下触发：

1. **Gateway 启动失败** (例如：端口被占用)
2. **Fallback 到 embedded 模式**
3. **需要加载工作空间模板文件** (例如：`ensureBootstrapFiles: true`)

如果 Gateway 正常运行，不会触发此 bug。

---

## 🔍 相关问题

### 为什么 Gateway 启动失败？

在你的情况下，Gateway 启动失败的原因是：

**旧进程占用端口**:
```
Port 18789 is already in use.
- pid 97715 tsl: openclaw-gateway (127.0.0.1:18789)
```

这是一个独立的问题，与模板路径 bug 无关。

### 两个问题的关系

```
问题 1: Gateway 端口冲突 (PID 97715)
   ↓
Gateway 启动失败
   ↓
Fallback 到 embedded 模式
   ↓
问题 2: 模板路径解析 bug (v2026.1.24-1)
   ↓
Embedded 模式也失败
   ↓
最终结果: 完全无法使用
```

---

## 📝 总结

### Bug 确认

- ✅ **这是一个真实的 bug**
- ✅ **已在 v2026.1.30 中修复** (2026-01-31)
- ✅ **修复提交**: ddc5683c6
- ❌ **你的版本 (v2026.1.24-1) 不包含修复**

### 推荐行动

**立即行动** (解决 Gateway 问题):
```bash
kill -9 97715
clawdbot gateway stop
clawdbot gateway start
```

**长期方案** (解决模板 bug):
```bash
sudo npm install -g clawdbot@latest
```

**临时替代** (绕过所有问题):
```bash
ollama run qwen2.5:3b "你的问题"
```

### 版本建议

- **当前版本**: v2026.1.24-1 (2026-01-24)
- **建议升级到**: v2026.2.3 或更高 (最新稳定版)
- **最小修复版本**: v2026.1.30 (包含模板路径修复)

---

## 🔗 相关链接

- **修复提交**: https://github.com/clawdbot/clawdbot/commit/ddc5683c675d77427a06a3fb8b79b186e9723a2e
- **新增文件**: `src/agents/workspace-templates.ts`
- **修改文件**: `src/agents/workspace.ts`, `src/cli/gateway-cli/dev.ts`
- **测试文件**: `src/agents/workspace-templates.test.ts`

---

## 📈 Bug 时间线

```
2026-01-24: v2026.1.24-1 发布 (包含 bug)
     ↓
2026-01-31: ddc5683c6 提交 (修复 bug)
     ↓
2026-01-31: v2026.1.30 发布 (包含修复)
     ↓
2026-02-02: v2026.2.1 发布
     ↓
2026-02-06: 你发现此问题 (使用 v2026.1.24-1)
```

**Bug 存在时间**: 7 天 (2026-01-24 → 2026-01-31)
**你的版本落后**: 13 天 (2026-01-24 → 2026-02-06)
**修复版本数量**: 5 个版本 (v2026.1.30, v2026.2.1, v2026.2.2, v2026.2.3, v2026.2.4)
