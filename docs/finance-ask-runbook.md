# `finance_ask` 观测与排障 Runbook

## 目的

本页用于排查 OpenClaw `finance_ask` 工具调用 `claw-finance-agent /ask` 的问题，覆盖以下链路：

1. Gateway / agent 侧是否真正调用了 `finance_ask`
2. `finance_ask` 是否成功发起 `POST /ask`
3. `claw-api` 是否返回有效 JSON
4. 超时、重试、HTTP 异常时应如何定位

## 关键日志前缀

`finance_ask` 工具的结构化日志前缀固定为：

```text
finance_ask
```

当前实现会输出以下关键日志：

- `finance_ask start`
  - 字段：`url`、`timeout_ms`、`retries`、`question_preview`
- `finance_ask ok`
  - 字段：`status`、`elapsed_ms`、`used_llm`、`retrieval_status`
- `finance_ask http_retry`
  - 字段：`status`、`attempt`
- `finance_ask timeout_retry`
  - 字段：`attempt`、`timeout_ms`
- `finance_ask fail`
  - 字段：`elapsed_ms`、`last_http_status`、`err`

源码位置：

- [finance-ask-tool.ts](/home/tsl/openclaw/extensions/claw-finance/src/finance-ask-tool.ts)

## 预期链路

单次正常调用的最小链路应可串成：

```text
finance_ask start
-> claw-api /ask 处理
-> finance_ask ok
```

若中间失败，则应看到：

```text
finance_ask start
-> finance_ask http_retry / timeout_retry（可选）
-> finance_ask fail
```

## OpenClaw 侧排查

### 1. 确认插件与工具已启用

检查 `openclaw` 配置中：

1. `plugins.entries.claw-finance.enabled = true`
2. 承接会话的 agent 允许 `finance_ask`

若需要看配置原文：

- [migration-feishu-finance.md](/home/tsl/openclaw/docs/migration-feishu-finance.md)

### 2. 查 Gateway 日志中的 `finance_ask`

```bash
journalctl --user -u openclaw-gateway --since "15 minutes ago" --no-pager | grep 'finance_ask'
```

期望看到：

- `finance_ask start`
- `finance_ask ok`

若仅看到 `start` 无 `ok` / `fail`，优先怀疑：

1. Gateway 进程被中断
2. `fetch` 卡在网络 / 超时
3. 日志窗口不完整

### 3. 检查 `CLAW_API_URL`

在 **运行 Gateway 的同一网络视角** 下验证：

```bash
curl -sS "${CLAW_API_URL:-http://127.0.0.1:9000}/health"
```

若这里不通，`finance_ask` 一定会失败。

## `claw-api` 侧排查

### 4. 开启 `FINANCE_ASK_TRACE`

在 `claw-finance-agent` 所在环境开启：

```bash
export FINANCE_ASK_TRACE=1
```

然后重启 `claw-api` 所在进程或服务。

开启后，`/ask` 侧应输出更细的请求处理轨迹，便于确认：

1. 是否命中 RAG
2. 是否走披露分支
3. 是否触发爬取回退
4. 是否发生上游 LLM 限流 / 生成降级

### 5. 直接对 `/ask` 做冒烟

```bash
curl -sS --max-time 600 -X POST "${CLAW_API_URL:-http://127.0.0.1:9000}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"紫金矿业 2025 年报","top_k":5,"use_llm":true}'
```

若这里成功，而 `finance_ask` 失败，则优先怀疑：

1. Gateway 环境变量未生效
2. Gateway 网络视角与当前 shell 不一致
3. `finance_ask` 超时 / 重试配置过小

## 常见故障对照

### 故障 1：`question required`

表现：

- `finance_ask` 工具直接抛错

原因：

- 模型调用时未传 `question`
- 工具参数被错误裁剪

动作：

1. 检查 agent 工具调用原文
2. 确认工具 schema 与模型调用参数一致

### 故障 2：`finance_ask invalid JSON from /ask`

表现：

- `finance_ask fail err=Error: finance_ask invalid JSON from /ask`

原因：

- `claw-api` 返回了非 JSON
- 反代 / 网关返回了 HTML 错页

动作：

1. 直接 `curl /ask`
2. 检查 `claw-api` 进程与反代日志

### 故障 3：`HTTP 429 / 502 / 503 / 504`

表现：

- 先出现 `finance_ask http_retry`
- 最终可能 `ok` 或 `fail`

动作：

1. 看是否为短暂上游抖动
2. 若连续失败，检查 `claw-api`、上游模型与网络

### 故障 4：超时

表现：

- `finance_ask timeout_retry`
- 最终 `finance_ask fail`

动作：

1. 检查 `CLAW_FINANCE_ASK_TIMEOUT_MS`
2. 确认 `/ask` 是否进入长爬取 / 长生成
3. 用 `FINANCE_ASK_TRACE=1` 看慢点位置

## 建议巡检命令

```bash
journalctl --user -u openclaw-gateway --since "15 minutes ago" --no-pager | grep 'finance_ask'
curl -sS "${CLAW_API_URL:-http://127.0.0.1:9000}/health"
curl -sS --max-time 600 -X POST "${CLAW_API_URL:-http://127.0.0.1:9000}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"紫金矿业 2025 年报","top_k":5,"use_llm":true}'
```

## 关联文档

- [migration-feishu-finance.md](/home/tsl/openclaw/docs/migration-feishu-finance.md)
- [phase4-feishu-airflow-signoff-2026-04-14.md](/home/tsl/openclaw/docs/phase4-feishu-airflow-signoff-2026-04-14.md)
