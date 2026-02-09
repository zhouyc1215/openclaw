# 会话历史自动清理功能实现完成

## 问题背景
当配置 `tools.deny: ["*"]` 禁用所有工具后，模型仍然从会话历史中学习工具调用模式，导致继续生成工具调用 JSON。这是因为会话历史中积累了大量工具调用示例，模型通过上下文学习（In-Context Learning）学会了工具调用模式。

## 解决方案
在 `tools.deny` 配置变更为禁用所有工具时，自动清理会话历史中的工具调用相关消息。

## 实现细节

### 1. 会话清理模块 (`src/gateway/session-tool-cleanup.ts`)
创建了专门的会话清理模块，包含以下功能：

- `isToolRelatedMessage()`: 检查消息是否包含工具调用或工具结果
- `cleanSessionTranscript()`: 清理单个会话文件中的工具调用
- `cleanAllSessionTranscripts()`: 清理所有会话文件
- `areAllToolsDisabled()`: 检查 tools.deny 是否禁用所有工具

### 2. 配置重载规则 (`src/gateway/config-reload.ts`)
添加了 `tools.deny` 的热重载规则：

```typescript
{ prefix: "tools.deny", kind: "hot" }
```

这确保 `tools.deny` 的变更会触发热重载，而不是被视为动态读取配置（`kind: "none"`）。

### 3. 重载处理器 (`src/gateway/server-reload-handlers.ts`)
在 `applyHotReload` 函数中添加了自动清理逻辑：

```typescript
// Check if tools.deny changed to disable all tools
const prevToolsDeny = currentConfig?.tools?.deny;
const nextToolsDeny = nextConfig.tools?.deny;
const toolsWereEnabled = !areAllToolsDisabled(prevToolsDeny);
const toolsNowDisabled = areAllToolsDisabled(nextToolsDeny);

if (toolsWereEnabled && toolsNowDisabled) {
  params.logReload.info(
    "tools.deny changed to disable all tools; cleaning session transcripts to remove tool call history",
  );
  
  // Clean all session transcripts asynchronously
  void cleanAllSessionTranscripts({
    log: (msg) => params.logReload.info(msg),
  }).catch((err) => {
    params.logReload.warn(`session cleanup failed: ${String(err)}`);
  });
}
```

## 测试结果

### 测试步骤
1. 恢复包含工具调用的会话历史（65 行）
2. 修改配置：`tools.deny: [] → ["*"]`
3. 观察日志和会话文件变化

### 测试日志
```
01:40:01 config change detected; evaluating reload (tools.deny)
01:40:01 tools.deny changed to disable all tools; cleaning session transcripts to remove tool call history
01:40:01 config hot reload applied (tools.deny)
01:40:01 Cleaned 3 tool-related messages from main/sessions/a562eea8-efca-4aeb-8c9b-e24266d84d1d.jsonl
01:40:01 Session cleanup complete: processed 8 files, cleaned 1 files, removed 3 tool-related messages
```

### 验证结果
- ✅ 会话文件从 65 行减少到 62 行（移除 3 条工具相关消息）
- ✅ 所有 `type: "toolCall"` 的消息已被清理
- ✅ 所有 `type: "toolResult"` 的消息已被清理
- ✅ 配置热重载成功，无需重启 Gateway

## 工作原理

### 规则匹配顺序
配置重载规则按顺序匹配，第一个匹配的规则会被使用：
1. `BASE_RELOAD_RULES`（包含 `tools.deny`）
2. `channelReloadRules`（插件贡献的规则）
3. `BASE_RELOAD_RULES_TAIL`（包含通用的 `tools` 规则）

由于 `tools.deny` 规则在 `tools` 规则之前，所以 `tools.deny` 的变更会触发热重载，而不是被 `tools` 规则捕获为动态读取。

### 清理逻辑
1. 检测配置变更：`tools.deny` 从不禁用所有工具 → 禁用所有工具
2. 触发热重载：调用 `applyHotReload`
3. 执行清理：遍历所有会话文件，移除工具调用和工具结果消息
4. 记录日志：输出清理统计信息

## 影响范围
- 只在 `tools.deny` 变更为 `["*"]` 时触发清理
- 清理所有 agent 的所有会话文件
- 异步执行，不阻塞配置重载
- 清理失败不影响配置重载的成功

## 后续优化建议
1. 支持更细粒度的清理（例如只清理特定 agent 的会话）
2. 支持清理特定工具的调用（而不是全部工具）
3. 添加清理前的备份机制
4. 支持手动触发清理的 CLI 命令

## 相关文件
- `src/gateway/session-tool-cleanup.ts` - 会话清理核心逻辑
- `src/gateway/config-reload.ts` - 配置重载规则
- `src/gateway/server-reload-handlers.ts` - 重载处理器
- `src/gateway/server.impl.ts` - Gateway 服务器实现

## 时间线
- **2026-02-09 01:32** - 首次尝试，发现 `tools.deny` 被识别为 `noopPaths`
- **2026-02-09 01:40** - 添加 `tools.deny` 热重载规则，自动清理成功触发 ✅
