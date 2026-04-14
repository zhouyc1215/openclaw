# 阶段 2 生产拓扑真相表

## 基本信息

- 文档名称：飞书财经入口迁移 阶段 2 生产拓扑真相表
- 文档编号：`phase2-topology-truth-table-2026-04-14`
- 生成日期：`2026-04-14`
- 关联文档：[migration-feishu-finance.md](/home/tsl/openclaw/docs/migration-feishu-finance.md)
- 适用范围：生产灰度前拓扑盘点、值班交接、回滚演练准备

## 当前事实

| 项目                    | 当前事实                                                                                                                               | 证据来源                                                          | 备注                                           |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------- |
| 飞书生产接入主链路      | `openclaw-gateway` 用户级 systemd 服务当前处于 `active (running)`                                                                      | `systemctl --user status openclaw-gateway`                        | 当前 IM 入口已由 Gateway 常驻进程承接          |
| Gateway 部署形态        | 宿主机 systemd 进程，不在 `claw-finance-agent` compose 内                                                                              | `openclaw-gateway.service`                                        | 与 `claw-api` 通过宿主机映射端口通信           |
| `claw-api` 部署形态     | Docker Compose 服务 `api`，宿主机映射 `0.0.0.0:9000->9000/tcp`                                                                         | `docker compose ps`                                               | Gateway 当前通过 `http://127.0.0.1:9000` 访问  |
| 独立旧链路 `feishu-bot` | 仍保留在 compose 中，但默认 `profiles: [standalone-feishu-bot]`，当前未运行                                                            | `claw-finance-agent/docker-compose.yml`、`docker compose ps`      | 可作为阶段 2 回滚入口                          |
| 飞书插件连接模式        | `connectionMode = websocket`                                                                                                           | 目标环境 `~/.openclaw/openclaw.json`                              | 当前为 WebSocket 进线，不是 webhook 反代模式   |
| 当前测试会话路由        | 指定飞书 DM 已通过 `bindings` 路由到 `finance-tools`                                                                                   | 目标环境 `~/.openclaw/openclaw.json`、阶段 1 联调记录             | 仅证明测试会话路由已生效，不等于生产全量已切换 |
| 当前灰度准入范围        | 飞书私聊已显式切为 `dmPolicy=allowlist`，仅测试 `open_id` 放行；`groupPolicy=disabled`；`airflowIngest.allowFrom` 同步仅测试 `open_id` | 目标环境 `~/.openclaw/openclaw.json`、2026-04-14 Gateway 配置变更 | 当前阶段 2 为白名单生产灰度，不是全量放开      |
| 最近 6 小时实际进线     | 仅观察到同一测试 `open_id` 进线                                                                                                        | `journalctl --user -u openclaw-gateway --since '6 hours ago'`     | 说明当前灰度范围与测试租户一致                 |
| 财经工具前置            | `plugins.entries.claw-finance.enabled=true`，测试链路已完成 `finance_ask` 验证                                                         | 阶段 1 电子签字、迁移文档阶段 1 记录                              | 阶段 2 的技术前置已满足                        |
| Airflow ingest 旁路     | Gateway 已启用 `channels.feishu.airflowIngest` 灰度能力                                                                                | 目标环境 `~/.openclaw/openclaw.json`、阶段 4 验证记录             | 是否随生产灰度一并放量，需单独确认             |

## 尚待补录的信息

以下信息属于生产切流必填，但当前不写入 Git 明文；建议在执行灰度前由运维在受控介质补全：

1. 飞书应用 ID、事件订阅 URL、应用凭证保管位置
2. 生产白名单 `open_id` / 测试群名单的受控介质记录与审批单号
3. 回滚时需要恢复的旧入口地址或控制台配置项
4. 值班负责人、切流窗口、审批单号

## 阶段 2 执行建议

1. 先按本表确认“当前谁在收消息、回滚谁来接”。
2. 当前已进入“仅测试租户”白名单灰度；下一步补切流窗口、值班负责人与日报模板。
3. 并行观察期间每天记录错误率、P95、飞书限频、客诉。
4. 回滚演练必须在正式全量前完成，并记录实际耗时。
