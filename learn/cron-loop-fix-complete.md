# Cron 循环问题修复完成

## 执行时间
2026-02-12 10:49 - 11:15 (约 26 分钟)

## 问题回顾

Agent 在尝试创建 cron 任务时陷入死循环：
- **循环次数**: 72+ 次
- **持续时间**: 2.5 小时
- **浪费成本**: 约 $36
- **根本原因**: Agent 使用了无效的 `payload.kind: "exec"`

## 完成的工作

### 1. 问题分析 ✅

创建了详细的分析文档：
- `learn/cron-loop-analysis.md` - 通用 cron 问题分析
- `learn/cron-loop-latest-analysis.md` - 最新实例的深度分析
- `analyze-cron-loop.py` - 循环分析脚本

关键发现：
- Agent 误认为可以使用 `payload.kind: "exec"` 来直接执行脚本
- 错误消息 "must be equal to constant" 太模糊，没有说明有效值
- Agent 从错误中得出了错误的结论，导致重复相同的错误

### 2. 文档创建 ✅

创建了完整的 cron 使用指南：
- `skills/cron/SKILL.md` - 包含：
  - 核心概念说明
  - 正确的使用示例
  - 常见错误对比（包括 kind: "exec" 错误）
  - 故障排查指南
  - Cron 表达式示例

### 3. 代码改进 ✅

改进了 `src/agents/tools/cron-tool.ts`：

```typescript
// 添加了前置验证
if (kind && kind !== "systemEvent" && kind !== "agentTurn") {
  throw new Error(
    `Invalid payload.kind: "${kind}". Must be "systemEvent" or "agentTurn". ` +
    `Cron jobs cannot directly execute commands. ...`
  );
}

// 检查 sessionTarget 和 payload.kind 的匹配
if (sessionTarget === "main" && kind && kind !== "systemEvent") {
  throw new Error(
    `sessionTarget "main" requires payload.kind "systemEvent" (not "${kind}"). ...`
  );
}

// 提供具体的字段要求
if (kind === "systemEvent") {
  if (typeof text !== "string" || !text.trim()) {
    throw new Error(
      'payload.kind "systemEvent" requires a non-empty "text" field. ...'
    );
  }
}
```

改进效果：
- ✅ 在 tool 层就捕获错误，不需要等到 gateway 验证
- ✅ 错误消息包含具体的有效值
- ✅ 提供正确的使用示例
- ✅ 明确说明 cron 不能直接执行命令

### 4. 停止循环 ✅

重启了 gateway：
```bash
pkill -9 -f "clawdbot.*gateway"
pnpm clawdbot gateway run --bind loopback --port 18789 --force
```

验证状态：
```
Gateway reachable.
- Feishu default: enabled, configured, running, works
```

## 测试改进效果

现在如果 Agent 再次尝试使用 `kind: "exec"`，会立即收到清晰的错误：

```
Invalid payload.kind: "exec". Must be "systemEvent" (for main session) or 
"agentTurn" (for isolated session). Cron jobs cannot directly execute commands. 
For main session, use: { kind: "systemEvent", text: "Task description" }. 
For isolated session, use: { kind: "agentTurn", message: "Task description" }.
```

这个错误消息：
1. ✅ 明确指出 "exec" 是无效的
2. ✅ 列出了有效的选项
3. ✅ 说明了 cron 不能直接执行命令
4. ✅ 提供了正确的示例

## 仍需完成的工作

### 高优先级
1. ⏳ 集成 ToolRetryGuard 到 agent runtime
   - 即使有了更好的错误消息，仍需要循环检测作为最后防线
   - 防止其他工具出现类似问题

### 中优先级
2. ⏳ 改进 feishu_doc 工具的错误消息
3. ⏳ 在 agent prompt 中添加 cron 使用说明

### 低优先级
4. ⏳ 考虑是否需要支持直接执行命令的功能
   - 如果这是常见需求，可以考虑添加新的 payload kind
   - 但需要仔细考虑安全性

## 影响评估

### 立即影响
- ✅ 当前循环已停止
- ✅ 新的错误消息会防止相同的错误
- ✅ Skill 文档提供了正确的使用方法

### 预期效果
- 🎯 Agent 会更快理解错误并使用正确的格式
- 🎯 减少因错误理解导致的循环
- 🎯 降低 token 浪费和成本

### 局限性
- ⚠️  仍然依赖 Agent 正确理解错误消息
- ⚠️  没有循环检测机制（ToolRetryGuard 未集成）
- ⚠️  其他工具可能有类似问题

## 相关文件

### 新增
- `learn/cron-loop-analysis.md`
- `learn/cron-loop-latest-analysis.md`
- `learn/cron-loop-fix-complete.md` (本文档)
- `skills/cron/SKILL.md`
- `analyze-cron-loop.py`

### 修改
- `src/agents/tools/cron-tool.ts` - 添加前置验证和改进错误消息
- `learn/fix-summary.md` - 更新总体进度

### 待修改
- `src/agents/pi-embedded-runner/run/attempt.ts` - 集成 ToolRetryGuard
- `src/agents/session-manager.ts` - 会话级别 guard
- `src/gateway/server.impl.ts` - 全局监控

## 验证清单

- [x] 分析了最新的循环实例
- [x] 理解了 Agent 的错误理解（kind: "exec"）
- [x] 创建了详细的分析文档
- [x] 创建了 cron skill 文档
- [x] 改进了 cron tool 的错误消息
- [x] 代码通过了语法检查
- [x] 重启了 gateway
- [x] 验证了 gateway 正常运行
- [x] 更新了总结文档
- [ ] 集成 ToolRetryGuard（下一步）
- [ ] 在实际场景中测试改进效果

## 下一步建议

1. **立即测试** - 在飞书中尝试创建 cron 任务，验证新的错误消息是否有效
2. **集成 ToolRetryGuard** - 作为最后的防线，防止任何工具陷入循环
3. **监控效果** - 观察 Agent 是否能更快地从错误中恢复

## 总结

通过分析、文档和代码改进，我们显著提升了 cron 工具的可用性：
- 错误消息从模糊的 "must be equal to constant" 变为具体的指导
- 提供了完整的使用文档和示例
- 在 tool 层就捕获常见错误，避免到 gateway 层才发现

但最重要的是，我们需要尽快集成 ToolRetryGuard，因为：
- 更好的错误消息可以减少循环，但不能完全防止
- Agent 在某些情况下仍可能误解错误
- 循环检测是必要的安全网

---

**修复完成时间**: 2026-02-12 11:15
**Gateway 状态**: 运行正常
**下一步**: 集成 ToolRetryGuard
