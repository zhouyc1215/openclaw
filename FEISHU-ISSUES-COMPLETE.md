# 飞书定时任务问题完整解决方案

## 问题历史

### 问题 1: 错误 798 - 缺少发送目标

**症状**: 飞书每小时收到 "unknown error, 798 (1000)" 错误消息

**根本原因**:

- 定时任务配置了 `delivery.channel: "last"` 但没有明确的 `delivery.to` 目标
- 错误 798 是飞书 API 的"无效/缺少发送目标"错误代码

**解决方案**:

- 为所有 4 个定时任务添加明确的飞书用户 ID: `ou_b3afb7d2133e4d689be523fc48f3d2b3`
- 配置: `{mode: "announce", channel: "feishu", to: "ou_b3afb7d2133e4d689be523fc48f3d2b3"}`

**文档**: `FEISHU-ERROR-798-RESOLVED.md`

---

### 问题 2: 错误 520 - Gateway 超时

**症状**: 飞书收到 "unknown error, 520 (1000)" 错误消息

**根本原因**:

- 定时任务在 `isolated` 模式下运行，执行时间较长（58-156 秒）
- 默认 Gateway 超时为 60 秒，导致任务执行超时

**解决方案**:

- 为每个任务添加 `timeoutSeconds` 配置：
  - `get_top_ai_projects`: 120 秒
  - `get_xian_weather_forecast`: 180 秒
  - `auto-commit-openclaw`: 180 秒
  - `backup_cron_results`: 240 秒

**文档**: `FEISHU-TIMEOUT-SOLUTION.md`, `FEISHU-520-ERROR-ANALYSIS.md`

---

### 问题 3: 无错误但无结果通知

**症状**:

- 飞书不再收到错误消息（好）
- 但也没有收到任务执行结果通知（坏）

**根本原因**:

- 任务执行成功，但 subagent announce 流程超时
- `src/agents/subagent-announce.ts` 中有两处硬编码的 60 秒超时
- 即使任务配置了更长的超时时间，announce 流程仍然使用 60 秒超时
- 当任务执行时间 > 60 秒时，announce 超时，结果无法送达飞书

**解决方案**:
修改 `src/agents/subagent-announce.ts`：

1. `sendAnnounce` 函数：添加 `timeoutMs` 参数
2. `maybeQueueSubagentAnnounce` 函数：添加 `timeoutMs` 参数并传递给 `sendAnnounce`
3. `runSubagentAnnounceFlow` 函数：使用 `params.timeoutMs` 替代硬编码的 60_000

**数据流**:

```
定时任务配置 (jobs.json)
  └─> timeoutSeconds: 120-240
       └─> runCronIsolatedAgentTurn
            └─> timeoutMs = resolveAgentTimeoutMs(...)
                 └─> runSubagentAnnounceFlow({ timeoutMs })
                      ├─> maybeQueueSubagentAnnounce({ timeoutMs })
                      │    └─> sendAnnounce(item, timeoutMs)
                      │         └─> callGateway({ timeoutMs })  ✅
                      └─> callGateway({ timeoutMs })  ✅
```

**文档**: `FEISHU-SUBAGENT-ANNOUNCE-TIMEOUT-FIX.md`

---

## 当前配置

### 定时任务配置 (`~/.openclaw/cron/jobs.json`)

所有 4 个定时任务现在都有：

```json
{
  "delivery": {
    "mode": "announce",
    "channel": "feishu",
    "to": "ou_b3afb7d2133e4d689be523fc48f3d2b3",
    "bestEffort": true
  },
  "payload": {
    "kind": "agentTurn",
    "timeoutSeconds": 120-240  // 根据任务不同
  }
}
```

### Gateway 配置

- 地址: `ws://10.71.1.116:18789`
- 模式: LAN (loopback)
- 状态: 运行中

---

## 测试验证

### 手动测试

```bash
./test-cron-announce.sh
```

### 等待自动执行

定时任务执行时间：

- `auto-commit-openclaw`: 每天 00:00
- `get_xian_weather_forecast`: 每天 08:00
- `get_top_ai_projects`: 每天 09:00
- `backup_cron_results`: 每天 10:00

### 验证成功标准

- ✅ 飞书收到任务结果通知
- ✅ 通知内容包含任务执行结果
- ✅ 没有错误消息（798, 520 等）

---

## 相关文件

### 代码修改

- `src/agents/subagent-announce.ts` - 修复 announce 超时问题

### 配置文件

- `~/.openclaw/cron/jobs.json` - 定时任务配置
- `~/.openclaw/openclaw.json` - OpenClaw 主配置（包含飞书配置）

### 文档

- `FEISHU-ERROR-798-RESOLVED.md` - 错误 798 分析和解决
- `FEISHU-TIMEOUT-SOLUTION.md` - 超时问题解决方案
- `FEISHU-520-ERROR-ANALYSIS.md` - 错误 520 详细分析
- `FEISHU-FIX-TEST-REPORT.md` - 修复测试报告
- `FEISHU-SUBAGENT-ANNOUNCE-TIMEOUT-FIX.md` - Announce 超时修复
- `FEISHU-ISSUES-COMPLETE.md` - 完整问题总结（本文档）

### 工具脚本

- `fix-cron-timeout.sh` - 自动修复超时配置
- `test-cron-announce.sh` - 测试 announce 修复

---

## Git 提交

```bash
# 查看更改
git status

# 提交代码修复
git add src/agents/subagent-announce.ts FEISHU-SUBAGENT-ANNOUNCE-TIMEOUT-FIX.md
git commit -m "fix(cron): use configurable timeout for subagent announce flow"

# 推送到远程
git push origin feishu-plugin-fixes
```

---

## 下一步

1. ✅ 代码已修复并提交
2. ✅ Gateway 已重启
3. ⏳ 等待下一次定时任务执行
4. ⏳ 验证飞书是否收到结果通知

如果测试成功，可以：

- 合并 `feishu-plugin-fixes` 分支到 `main`
- 启用 systemd 服务自动管理 Gateway
- 监控后续定时任务执行情况
