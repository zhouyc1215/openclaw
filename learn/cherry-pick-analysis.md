# Cherry-pick 可行性分析报告

## 📋 目标

将修复提交 `ddc5683c6` (fix: resolve workspace templates from package root) cherry-pick 到当前分支 `v2026.1.24-1`。

---

## 🔍 依赖分析

### 修复提交涉及的文件

```
ddc5683c675d77427a06a3fb8b79b186e9723a2e
├── src/agents/workspace-templates.test.ts  (新增)
├── src/agents/workspace-templates.ts       (新增)
├── src/agents/workspace.ts                 (修改)
└── src/cli/gateway-cli/dev.ts              (修改)
```

### 关键依赖

修复提交依赖于 `src/infra/openclaw-root.ts` 中的 `resolveOpenClawPackageRoot()` 函数：

```typescript
// src/agents/workspace-templates.ts
import { resolveOpenClawPackageRoot } from "../infra/openclaw-root.js";
```

### 依赖链分析

```
ddc5683c6 (修复提交, 2026-01-31)
    ↓ 依赖
9a7160786 (refactor: rename to openclaw, 2026-01-30)
    ↓ 引入 openclaw-root.ts
    ↓ 122 个提交
v2026.1.24-1 (当前版本, 2026-01-24)
```

**提交距离**:
- v2026.1.24-1 → 9a7160786: **377 个提交**
- 9a7160786 → ddc5683c6: **122 个提交**
- **总计**: **499 个提交**

---

## ⚠️ 问题分析

### 问题 1: 缺失依赖文件

**当前版本 (v2026.1.24-1) 不存在**:
```bash
$ git ls-tree v2026.1.24-1 src/infra/openclaw-root.ts
# (无输出 - 文件不存在)
```

**该文件在 9a7160786 提交中引入**:
```
commit 9a7160786a7dbd21469fad73992158e415e4686e
Date:   Fri Jan 30 03:15:10 2026 +0100
refactor: rename to openclaw
```

### 问题 2: 命名空间变更

在 9a7160786 提交中，项目进行了大规模重命名：
- `clawdbot` → `openclaw`
- `CLAWDBOT_*` → `OPENCLAW_*`
- `clawd` → `.openclaw/workspace`

**workspace.ts 中的变更**:
```diff
- const profile = env.CLAWDBOT_PROFILE?.trim();
+ const profile = env.OPENCLAW_PROFILE?.trim();

- return path.join(homedir(), `clawd-${profile}`);
+ return path.join(homedir(), ".openclaw", `workspace-${profile}`);

- return path.join(homedir(), "clawd");
+ return path.join(homedir(), ".openclaw", "workspace");
```

### 问题 3: 其他代码变更

在 499 个提交中，可能还有其他相关的代码变更：
- 新增的常量 (`DEFAULT_MEMORY_FILENAME`, `DEFAULT_MEMORY_ALT_FILENAME`)
- 代码风格调整
- 其他重构

---

## 🎯 Cherry-pick 可行性评估

### ❌ 直接 Cherry-pick: **不可行**

```bash
git cherry-pick ddc5683c6
```

**预期结果**: ❌ **失败**

**失败原因**:
1. ✗ 缺少依赖文件 `src/infra/openclaw-root.ts`
2. ✗ 编译错误: `Cannot find module '../infra/openclaw-root.js'`
3. ✗ 命名空间不匹配 (CLAWDBOT vs OPENCLAW)
4. ✗ 路径不匹配 (clawd vs .openclaw/workspace)

---

## 🔧 可行的解决方案

### 方案 1: 多提交 Cherry-pick ⭐⭐ (复杂)

**步骤**:
```bash
# 1. Cherry-pick openclaw-root.ts 引入提交
git cherry-pick 9a7160786

# 2. 解决冲突（可能有数百个文件冲突）
# ...

# 3. Cherry-pick 修复提交
git cherry-pick ddc5683c6
```

**问题**:
- ⚠️ 9a7160786 是大规模重命名提交，会影响数百个文件
- ⚠️ 需要手动解决大量冲突
- ⚠️ 可能破坏现有功能
- ⚠️ 工作量巨大（377 个提交的变更）

**评估**: ❌ **不推荐** - 风险太高，工作量太大

---

### 方案 2: 手动移植修复 ⭐⭐⭐ (可行但需要适配)

**步骤**:

#### 2.1 创建简化版 openclaw-root.ts

```bash
# 创建文件
mkdir -p src/infra
cat > src/infra/openclaw-root.ts << 'EOF'
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

// 简化版：只支持 clawdbot (不支持 openclaw)
const CORE_PACKAGE_NAMES = new Set(["clawdbot"]);

async function readPackageName(dir: string): Promise<string | null> {
  try {
    const raw = await fs.readFile(path.join(dir, "package.json"), "utf-8");
    const parsed = JSON.parse(raw) as { name?: unknown };
    return typeof parsed.name === "string" ? parsed.name : null;
  } catch {
    return null;
  }
}

async function findPackageRoot(startDir: string, maxDepth = 12): Promise<string | null> {
  let current = path.resolve(startDir);
  for (let i = 0; i < maxDepth; i += 1) {
    const name = await readPackageName(current);
    if (name && CORE_PACKAGE_NAMES.has(name)) return current;
    const parent = path.dirname(current);
    if (parent === current) break;
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
    const root = await findPackageRoot(candidate);
    if (root) return root;
  }

  return null;
}
EOF
```

#### 2.2 复制 workspace-templates.ts

```bash
# 从修复提交中提取文件
git show ddc5683c6:src/agents/workspace-templates.ts > src/agents/workspace-templates.ts
```

#### 2.3 修改 workspace.ts

```bash
# 手动编辑 src/agents/workspace.ts
# 只修改 loadTemplate 函数，保持其他部分不变
```

**修改内容**:
```typescript
// 在文件顶部添加 import
import { resolveWorkspaceTemplateDir } from "./workspace-templates.js";

// 删除旧的 TEMPLATE_DIR 常量
// const TEMPLATE_DIR = path.resolve(...);

// 修改 loadTemplate 函数
async function loadTemplate(name: string): Promise<string> {
  const templateDir = await resolveWorkspaceTemplateDir();  // 新增
  const templatePath = path.join(templateDir, name);        // 修改
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

#### 2.4 修改 gateway-cli/dev.ts

```bash
# 手动编辑 src/cli/gateway-cli/dev.ts
```

#### 2.5 编译和测试

```bash
# 编译
pnpm build

# 测试
pnpm test src/agents/workspace.test.ts

# 全局安装
sudo npm link

# 验证
clawdbot --version
```

**评估**: ✅ **可行** - 需要手动适配，但工作量可控

**优点**:
- ✅ 只修改必要的文件
- ✅ 保持与 v2026.1.24-1 的兼容性
- ✅ 不引入大规模重命名
- ✅ 风险可控

**缺点**:
- ⚠️ 需要手动编辑和测试
- ⚠️ 需要创建简化版依赖文件
- ⚠️ 可能需要调试

---

### 方案 3: 升级到最新版本 ⭐⭐⭐⭐⭐ (最推荐)

```bash
sudo npm install -g clawdbot@latest
```

**评估**: ✅ **强烈推荐**

**优点**:
- ✅ 一步到位，包含所有修复
- ✅ 官方支持
- ✅ 无需手动操作
- ✅ 获得其他 bug 修复和新功能
- ✅ 零风险

**缺点**:
- ⚠️ 引入 499 个提交的变更
- ⚠️ 可能有配置迁移（clawdbot → openclaw）

---

## 📊 方案对比

| 方案 | 可行性 | 工作量 | 风险 | 推荐度 |
|------|--------|--------|------|--------|
| 直接 Cherry-pick | ❌ 不可行 | - | 极高 | ⭐ |
| 多提交 Cherry-pick | ⚠️ 理论可行 | 极大 | 极高 | ⭐⭐ |
| 手动移植修复 | ✅ 可行 | 中等 | 中等 | ⭐⭐⭐ |
| 升级到最新版本 | ✅ 可行 | 极小 | 极低 | ⭐⭐⭐⭐⭐ |

---

## 🎯 推荐方案

### 首选：升级到最新版本

```bash
# 备份当前配置
cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.backup

# 升级
sudo npm install -g clawdbot@latest

# 验证
clawdbot --version

# 如果需要，迁移配置
# (最新版本可能使用 ~/.openclaw/)
```

### 备选：手动移植修复

如果必须保持在 v2026.1.24-1，可以使用方案 2 手动移植。

**步骤总结**:
1. 创建简化版 `src/infra/openclaw-root.ts`
2. 复制 `src/agents/workspace-templates.ts`
3. 修改 `src/agents/workspace.ts` (只改 loadTemplate)
4. 修改 `src/cli/gateway-cli/dev.ts`
5. 编译、测试、安装

**预计工作量**: 1-2 小时

---

## 📝 结论

### Cherry-pick 可行性

- ❌ **直接 cherry-pick**: 不可行（缺少依赖）
- ⚠️ **多提交 cherry-pick**: 理论可行但不推荐（工作量巨大，风险极高）
- ✅ **手动移植**: 可行（需要适配，工作量中等）
- ✅ **升级版本**: 最佳方案（零风险，一步到位）

### 最终建议

**强烈推荐升级到最新版本** (v2026.2.3+)，原因：
1. ✅ 包含完整修复
2. ✅ 官方支持
3. ✅ 获得其他改进
4. ✅ 零风险
5. ✅ 工作量最小

如果有特殊原因必须保持在 v2026.1.24-1，可以考虑手动移植方案，但需要：
- 投入 1-2 小时进行适配
- 充分测试
- 接受可能的兼容性问题

---

## 🔗 相关文件

- 修复提交: `ddc5683c675d77427a06a3fb8b79b186e9723a2e`
- 依赖提交: `9a7160786a7dbd21469fad73992158e415e4686e`
- 当前版本: `v2026.1.24-1`
- 修复版本: `v2026.1.30+`

---

## 📋 下一步行动

### 如果选择升级（推荐）

```bash
sudo npm install -g clawdbot@latest
clawdbot --version
```

### 如果选择手动移植

1. 阅读完整的移植步骤（方案 2）
2. 创建新分支进行测试
3. 逐步实施修改
4. 充分测试后再部署

### 如果选择保持现状

```bash
# 修复 Gateway 端口冲突
kill -9 97715
clawdbot gateway stop
clawdbot gateway start

# 使用 Ollama 作为替代
ollama run qwen2.5:3b "你的问题"
```
