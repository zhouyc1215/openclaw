# 阶段 2 白名单灰度观察记录

## 基本信息

- 文档名称：飞书财经入口迁移 阶段 2 白名单灰度观察记录
- 文档编号：`phase2-gray-observation-2026-04-14`
- 启动日期：`2026-04-14`
- 关联文档：[migration-feishu-finance.md](/home/tsl/openclaw/docs/migration-feishu-finance.md)
- 灰度范围：仅测试 `open_id` 私聊进入 `openclaw-gateway`；群消息关闭；`airflowIngest` 同步使用相同白名单

## Day 0 基线

| 项目                | 当前值                                                            | 说明                                                                               |
| ------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Gateway 服务状态    | `active (running)`                                                | `openclaw-gateway` 已于 `2026-04-14 13:30 CST` 完成重启并恢复                      |
| 飞书灰度准入        | `dmPolicy=allowlist`                                              | 当前仅测试 `open_id` 可进入 Gateway                                                |
| 群消息策略          | `groupPolicy=disabled`                                            | 阶段 2 初始灰度不放开群消息                                                        |
| Airflow ingest 准入 | `airflowIngest.allowFrom` 已同步白名单                            | 避免灰度外用户误触发 DAG                                                           |
| 旧链路回滚入口      | `docker compose --profile standalone-feishu-bot up -d feishu-bot` | 独立旧 Bot 当前未运行                                                              |
| 最近 6 小时进线范围 | 单一测试 `open_id`                                                | `journalctl --user -u openclaw-gateway --since '6 hours ago'` 仅观察到同一测试用户 |

## 观察指标

每日补充以下字段：

| 日期       | 观察窗口       | 进线用户范围       | `/ask` 5xx | P95 延迟 | 飞书限频 | 客诉/异常 | 结论             | 执行人 |
| ---------- | -------------- | ------------------ | ---------- | -------- | -------- | --------- | ---------------- | ------ |
| 2026-04-14 | Day 0 启动基线 | 单一测试 `open_id` | 待观察     | 待观察   | 待观察   | 待观察    | 白名单灰度已启动 | tsl    |

## 巡检命令

```bash
systemctl --user status openclaw-gateway --no-pager
journalctl --user -u openclaw-gateway --since "24 hours ago" --no-pager | rg 'received message from|dispatching to agent|finance_ask|airflow_dag_run_enqueued'
cd /home/tsl/claw-finance-agent && docker compose logs --since=24h api
cd /home/tsl/claw-finance-agent && docker compose exec -T airflow-scheduler airflow dags list-runs -d ingest_cninfo_pdf --no-backfill | tail -n 20
```

## 下一步

1. 在受控介质补录白名单审批单号、切流窗口和值班负责人。
2. 连续观察至少 7 天，每日回填本表。
3. 观察期内完成回滚演练，并记录实际回切耗时。
