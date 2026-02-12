# 修复总结 - Clawdbot 死循环问题

## 已完成的工作 ✅

### 1. 问题诊断
- ✅ 分析了会话日志，发现 agent 陷入工具调用死循环
- ✅ 识别了三种重复的错误模式：
  - feishu_doc: 无效的 action "update"
  - feishu_drive: 400 错误
  - feishu_doc: 缺少 document_id 参数
- ✅ 确认循环持续了至少 4 分钟，约 20+ 次调用

### 2. 创建防护机制
- ✅ 实现了 `ToolRetryGuard` 类 (`src/agents/tool-retry-guard.ts`)
- ✅ 添加了单元测试 (`src/agents/tool-retry-guard.test.ts`)
- ✅ 功能包括：
  - 失败计数和跟踪
  - 智能阻断（默认 3 次失败）
  - 参数相似度检测
  - 自动清理过期记录
  - 统计信息

### 3. 立即修复
- ✅ 重启了 gateway (PID: 333005)
- ✅ 验证了 gateway 运行正常
- ✅ 死循环已被打断

### 4. 文档
- ✅ 创建了问题分析文档 (`learn/feishu-loop-analysis.md`)
- ✅ 创建了修复方案文档 (`learn/tool-retry-guard-fix.md`)
- ✅ 创建了本总结文档

## 待完成的工作 📋

### 1. 集成 ToolRetryGuard (高优先级)

需要在以下位置集成：

**位置 1: Agent 运行时**
```typescript
// src/agents/pi-embedded-runner/run/attempt.ts
// 在工具调用循环中添加检查和记录
```

**位置 2: 会话管理**
```typescript
// src/agents/session-manager.ts
// 在会话级别维护 guard 实例
```

**位置 3: Gateway 层**
```typescript
// src/gateway/server.impl.ts
// 添加全局监控
```

### 2. 配置支持

添加配置选项到 `src/config/types.agent-defaults.ts`:
```typescript
export type AgentDefaultsConfig = {
  // ... existing fields
  toolRetryGuard?: {
    enabled?: boolean;
    maxConsecutiveFailures?: number;
    failureWindowMs?: number;
    checkParamSimilarity?: boolean;
  };
};
```

### 3. 修复 feishu_doc 工具

需要检查和修复 feishu_doc 工具的 schema：
- 确认有效的 action 值列表
- 添加文档重命名支持（如果需要）
- 或者明确说明不支持的操作

### 4. 改进错误处理

在 agent prompt 中添加指导：
- 工具调用失败后应该尝试其他方法
- 不要使用相同参数重复调用
- 失败 2-3 次后应该向用户报告

### 5. 测试

- 修复单元测试中的问题
- 添加集成测试
- 在实际场景中测试防护机制

## 使用指南

### 当前如何避免死循环

1. **在飞书中**:
   - 如果 bot 没有响应，发送 "/new" 开始新会话
   - 或者发送 "停止" 尝试打断当前任务

2. **在服务器上**:
   ```bash
   # 重启 gateway
   pnpm clawdbot gateway restart
   
   # 或者清理问题会话
   rm ~/.clawdbot/agents/main/sessions/<session-id>.jsonl
   ```

### 未来集成后

ToolRetryGuard 会自动：
- 检测重复失败
- 阻止继续调用
- 向 agent 返回明确的错误信息
- Agent 会尝试其他方法或向用户报告

## 技术细节

### ToolRetryGuard 工作原理

```
用户请求 → Agent 尝试工具调用
              ↓
         检查 Guard
              ↓
    是否超过失败阈值？
         ↙        ↘
       是          否
       ↓           ↓
   阻止调用    执行工具
   返回错误        ↓
                成功？
              ↙      ↘
            是        否
            ↓         ↓
         清除计数  记录失败
                     ↓
                  增加计数
```

### 配置示例

```json
{
  "agents": {
    "defaults": {
      "toolRetryGuard": {
        "enabled": true,
        "maxConsecutiveFailures": 3,
        "failureWindowMs": 300000,
        "checkParamSimilarity": true
      }
    }
  }
}
```

## 相关文件

### 新增文件
- `src/agents/tool-retry-guard.ts` - 核心实现
- `src/agents/tool-retry-guard.test.ts` - 单元测试
- `learn/feishu-loop-analysis.md` - Feishu 问题分析
- `learn/cron-loop-analysis.md` - Cron 问题分析（通用）
- `learn/cron-loop-latest-analysis.md` - Cron 最新实例分析（kind: "exec" 问题）
- `learn/cron-loop-fix-complete.md` - Cron 修复完成总结
- `learn/why-cannot-stop-loop.md` - 为什么无法通过消息停止循环的深度分析
- `learn/tool-retry-guard-fix.md` - 修复方案
- `learn/fix-summary.md` - 本文档
- `skills/cron/SKILL.md` - Cron 工具使用指南
- `analyze-cron-loop.py` - 循环分析脚本

### 需要修改的文件
- `src/agents/pi-embedded-runner/run/attempt.ts` - 集成 guard
- `src/agents/session-manager.ts` - 会话级别 guard
- `src/gateway/server.impl.ts` - 全局监控
- `src/config/types.agent-defaults.ts` - 配置类型
- ✅ `src/agents/tools/cron-tool.ts` - 改进错误消息（已完成）

## 相关问题：Cron 任务创建循环

在分析过程中发现了另一个相同模式的循环问题：Agent 创建 cron 任务时反复失败。

### Cron 循环的根本原因

1. **Payload Schema 理解错误**
   - Agent 混淆了 schedule.kind 和 payload.kind
   - 使用了不存在的属性（command, atMs 在 payload 中）
   - 对 isolated session 使用 text 而不是 message

2. **强制关系未理解**
   - `sessionTarget: "main"` 必须使用 `payload.kind: "systemEvent"`
   - `sessionTarget: "isolated"` 必须使用 `payload.kind: "agentTurn"`

3. **错误消息不够清晰**
   - 验证错误只说"unexpected property"，没有给出正确示例
   - Agent 无法从错误中学习正确的格式

### 已完成的 Cron 相关工作

- ✅ 创建详细的 cron 循环分析文档（`learn/cron-loop-analysis.md`）
- ✅ 分析最新的循环实例（`learn/cron-loop-latest-analysis.md`）
  - 发现 Agent 使用了无效的 `payload.kind: "exec"`
  - 循环了 72+ 次，浪费约 $36 和 2.5 小时
  - Agent 误解了错误消息，认为应该使用 "exec"
- ✅ 创建 cron skill 文档（`skills/cron/SKILL.md`）提供清晰示例和常见错误说明
- ✅ 改进 cron tool 错误消息（`src/agents/tools/cron-tool.ts`）
  - 添加前置验证，在 tool 层就捕获错误
  - 提供具体的错误消息和正确示例
  - 明确说明 cron 不能直接执行命令

### Cron 相关待办

- ⏳ 改进 cron tool 的错误消息，提供具体修复建议
- ⏳ ToolRetryGuard 集成后将同时防止 feishu 和 cron 循环

## 下一步行动

### 高优先级（防止循环）
1. ✅ 创建 ToolRetryGuard 类
2. ✅ 添加单元测试
3. ✅ 分析 cron 循环问题
4. ✅ 创建 cron skill 文档
5. ✅ 集成 ToolRetryGuard 到 agent runtime
   - ✅ `src/agents/pi-tool-definition-adapter.ts` - 添加 guard 检查
   - ✅ `src/agents/pi-embedded-runner/tool-split.ts` - 传递 guard
   - ✅ `src/agents/pi-embedded-runner/run/attempt.ts` - 创建 guard 实例
6. ✅ 创建集成测试并验证通过
7. ⏳ 在实际场景中测试效果

### 中优先级（改进错误提示）
7. ✅ 改进 cron tool 错误消息（`src/agents/tools/cron-tool.ts`）
8. ⏳ 改进 feishu_doc 工具 schema 和错误消息
9. ⏳ 添加工具使用指南到 agent prompt

### 低优先级（长期改进）
10. ⏳ 考虑为所有工具添加使用示例到错误消息中
11. ⏳ 创建工具使用最佳实践文档

## 验证

当前状态：
- ✅ Gateway 运行中 (PID: 333005)
- ✅ RPC probe: ok
- ✅ 死循环已打断
- ⏳ 等待飞书测试确认

---

**修复完成时间**: 2026-02-11 19:15
**Gateway 重启**: 成功
**状态**: 立即问题已解决，长期修复待集成
