# 飞书定时任务 Gateway 超时问题解决方案

## 问题描述

修复错误 798 后，手动执行定时任务时出现 Gateway 超时错误：

```
gateway timeout after 60000ms
```

所有 4 个定时任务都遇到超时：

| 任务名称                  | 计划时间   | 实际执行时间 | 状态 |
| ------------------------- | ---------- | ------------ | ---- |
| auto-commit-openclaw      | 每天 0:00  | 121 秒       | 超时 |
| get_xian_weather_forecast | 每天 8:00  | 116 秒       | 超时 |
| get_top_ai_projects       | 每天 9:00  | 58 秒        | 超时 |
| backup_cron_results       | 每天 10:00 | 156 秒       | 超时 |

## 根本原因分析

### 超时层级

OpenClaw 有多个超时配置层级：

1. **CLI 超时**（`openclaw cron run` 命令）
   - 默认值：30 秒（30000ms）
   - 可通过 `--timeout` 选项覆盖
   - 位置：`src/cli/gateway-rpc.ts`

2. **Agent 超时**（任务执行超时）
   - 默认值：600 秒（10 分钟）
   - 可通过配置文件或任务 payload 覆盖
   - 位置：`src/agents/timeout.ts`

3. **Gateway 连接超时**
   - 默认值：10 秒（10000ms）
   - 位置：`src/gateway/call.ts`

### 当前问题

1. **CLI 超时太短**：用户手动运行 `openclaw cron run` 时，CLI 在 60 秒后超时
2. **任务执行时间长**：所有任务都在 `isolated` 模式下运行，需要执行 shell 脚本、网络请求等操作
3. **Gateway 继续运行**：虽然 CLI 超时，但任务在 Gateway 中继续执行并最终完成
4. **错误消息误导**：超时错误被打印到控制台，然后被误认为是要发送给用户的消息

## 解决方案

### 方案 A：增加 CLI 超时（临时测试）

手动运行定时任务时，使用 `--timeout` 选项：

```bash
# 增加超时到 3 分钟（180000 毫秒）
openclaw cron run auto-commit-openclaw --timeout 180000

# 增加超时到 5 分钟（300000 毫秒）
openclaw cron run backup_cron_results --timeout 300000
```

**优点**：

- 快速测试
- 不需要修改配置文件

**缺点**：

- 每次手动运行都需要指定
- 不影响自动执行的定时任务

### 方案 B：配置任务级别超时（推荐）

在每个定时任务的 `payload` 中添加 `timeoutSeconds` 字段：

#### 步骤 1：备份配置

```bash
cp ~/.openclaw/cron/jobs.json ~/.openclaw/cron/jobs.json.bak-$(date +%Y%m%d-%H%M%S)
```

#### 步骤 2：编辑配置文件

```bash
nano ~/.openclaw/cron/jobs.json
```

为每个任务添加 `timeoutSeconds`：

```json
{
  "id": "auto-commit-openclaw",
  "payload": {
    "kind": "agentTurn",
    "message": "Execute /home/tsl/openclaw/autocommit.sh to commit and push changes.",
    "timeoutSeconds": 180
  }
}
```

#### 步骤 3：推荐的超时配置

根据实际执行时间，建议配置：

```json
{
  "jobs": [
    {
      "id": "auto-commit-openclaw",
      "payload": {
        "timeoutSeconds": 180
      }
    },
    {
      "id": "get_xian_weather_forecast",
      "payload": {
        "timeoutSeconds": 180
      }
    },
    {
      "id": "get_top_ai_projects",
      "payload": {
        "timeoutSeconds": 120
      }
    },
    {
      "id": "backup_cron_results",
      "payload": {
        "timeoutSeconds": 240
      }
    }
  ]
}
```

**优点**：

- 每个任务有独立的超时配置
- 自动执行和手动执行都生效
- 不影响其他任务

**缺点**：

- 需要手动编辑配置文件
- 需要重启 Gateway 才能生效

### 方案 C：修改全局 Agent 超时（不推荐）

在 `~/.openclaw/openclaw.json` 中设置全局超时：

```json
{
  "agents": {
    "defaults": {
      "timeoutSeconds": 300
    }
  }
}
```

**优点**：

- 一次配置，所有任务生效

**缺点**：

- 影响所有 agent 任务，不仅是 cron
- 可能导致某些任务运行时间过长

## 实施步骤（推荐方案 B）

### 1. 备份当前配置

```bash
cp ~/.openclaw/cron/jobs.json ~/.openclaw/cron/jobs.json.bak-$(date +%Y%m%d-%H%M%S)
```

### 2. 使用 jq 批量更新配置

```bash
# 为 auto-commit-openclaw 添加 180 秒超时
jq '(.jobs[] | select(.id == "5e44ba7a-2a52-48db-815f-56925535d08b") | .payload) += {"timeoutSeconds": 180}' \
  ~/.openclaw/cron/jobs.json > /tmp/jobs.json && mv /tmp/jobs.json ~/.openclaw/cron/jobs.json

# 为 get_xian_weather_forecast 添加 180 秒超时
jq '(.jobs[] | select(.id == "bad3205a-ddab-4efe-9426-1703b9b757c4") | .payload) += {"timeoutSeconds": 180}' \
  ~/.openclaw/cron/jobs.json > /tmp/jobs.json && mv /tmp/jobs.json ~/.openclaw/cron/jobs.json

# 为 get_top_ai_projects 添加 120 秒超时
jq '(.jobs[] | select(.id == "440648af-dcab-4cc7-8086-45c0f87263c6") | .payload) += {"timeoutSeconds": 120}' \
  ~/.openclaw/cron/jobs.json > /tmp/jobs.json && mv /tmp/jobs.json ~/.openclaw/cron/jobs.json

# 为 backup_cron_results 添加 240 秒超时
jq '(.jobs[] | select(.id == "backup-cron-results") | .payload) += {"timeoutSeconds": 240}' \
  ~/.openclaw/cron/jobs.json > /tmp/jobs.json && mv /tmp/jobs.json ~/.openclaw/cron/jobs.json
```

### 3. 验证配置

```bash
# 查看所有任务的超时配置
jq -r '.jobs[] | "\(.name): \(.payload.timeoutSeconds // "default (600s)")"' ~/.openclaw/cron/jobs.json
```

预期输出：

```
get_top_ai_projects: 120
get_xian_weather_forecast: 180
auto-commit-openclaw: 180
backup_cron_results: 240
```

### 4. 重启 Gateway

```bash
# 停止旧的 Gateway 进程
pkill -9 -f openclaw-gateway || true

# 启动新的 Gateway
nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &
```

### 5. 测试单个任务

```bash
# 使用增加的 CLI 超时测试
openclaw cron run auto-commit-openclaw --timeout 300000

# 查看 Gateway 日志
tail -f /tmp/openclaw-gateway.log
```

## 验证结果

### 检查任务执行状态

```bash
openclaw cron list
```

### 查看任务执行历史

```bash
openclaw cron runs --id auto-commit-openclaw --limit 5
```

### 监控 Gateway 日志

```bash
tail -f /tmp/openclaw-gateway.log | grep -E "cron|timeout|error"
```

## 预期效果

修复后：

1. ✅ 手动运行 `openclaw cron run` 不再超时
2. ✅ 定时任务自动执行时有足够的时间完成
3. ✅ 任务执行结果正常发送到飞书
4. ✅ 不再出现 "unknown error, 520 (1000)" 错误

## 故障排查

### 如果任务仍然超时

1. **检查实际执行时间**

   ```bash
   # 查看 Gateway 日志中的任务执行时间
   grep "cron.*duration" /tmp/openclaw-gateway.log | tail -20
   ```

2. **增加超时时间**

   如果任务执行时间超过配置的超时，继续增加 `timeoutSeconds`

3. **检查任务脚本**

   ```bash
   # 手动运行脚本，测量执行时间
   time /home/tsl/openclaw/autocommit.sh
   ```

### 如果 Gateway 日志中没有错误

任务可能在后台成功执行，只是 CLI 超时了。检查：

```bash
# 查看任务最后执行状态
openclaw cron list | jq '.jobs[] | {name, lastStatus: .state.lastStatus, lastDurationMs: .state.lastDurationMs}'
```

## 技术细节

### 超时配置优先级

1. `payload.timeoutSeconds`（任务级别）- 最高优先级
2. `agents.defaults.timeoutSeconds`（全局配置）
3. `DEFAULT_AGENT_TIMEOUT_SECONDS = 600`（代码默认值）

### 相关代码文件

- `src/agents/timeout.ts` - Agent 超时逻辑
- `src/cli/gateway-rpc.ts` - CLI 超时配置
- `src/cron/types.ts` - Cron 任务类型定义
- `src/gateway/call.ts` - Gateway 调用超时

### 超时计算公式

```typescript
// Agent 超时（任务执行）
const agentTimeoutMs =
  (payload.timeoutSeconds || config.agents.defaults.timeoutSeconds || 600) * 1000;

// CLI 超时（等待响应）
const cliTimeoutMs = parseInt(opts.timeout || "30000");

// 建议：CLI 超时 >= Agent 超时 + 30 秒（缓冲时间）
```

## 相关文档

- `FEISHU-ERROR-798-RESOLVED.md` - 飞书错误 798 解决方案
- `FEISHU-FIX-COMPLETE.md` - 飞书配置修复
- `~/.openclaw/cron/jobs.json` - Cron 任务配置
- `/tmp/openclaw-gateway.log` - Gateway 日志

## 总结

Gateway 超时问题的根本原因是：

1. **CLI 默认超时太短**（30 秒），无法等待长时间运行的任务
2. **任务在 isolated 模式下运行**，需要执行 shell 脚本、网络请求等耗时操作
3. **没有配置任务级别的超时**，使用了默认的 600 秒，但 CLI 在此之前就超时了

通过为每个任务配置合适的 `timeoutSeconds`，并在手动测试时使用 `--timeout` 选项，可以彻底解决超时问题。

---

**创建时间**: 2026-02-27 10:30  
**创建人员**: Kiro AI Assistant  
**状态**: 📝 待实施
