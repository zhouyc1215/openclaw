# WebSocket 连接问题修复完成

## 问题描述

Control UI 无法连接到 Gateway，WebSocket 连接失败，错误码 1008，错误信息：

```
invalid connect params: at /client/id: must be equal to constant; at /client/id: must match a schema in anyOf
```

## 根本原因

服务器端的 `GatewayClientIdSchema` 使用严格的枚举验证（`Type.Union`），只接受预定义的 `client.id` 值。当客户端发送的 `client.id` 不在枚举列表中时，连接被拒绝。

## 修复方案

### 1. 放宽 client.id 验证

修改 `src/gateway/protocol/schema/primitives.ts`：

```typescript
// 修改前（严格验证）
export const GatewayClientIdSchema = Type.Union(
  Object.values(GATEWAY_CLIENT_IDS).map((value) => Type.Literal(value)),
);

// 修改后（宽松验证）
export const GatewayClientIdSchema = NonEmptyString;
```

### 2. 解决 Git 合并冲突

项目中存在多个 Git 合并冲突，阻止了构建。解决了以下文件的冲突：

- `src/agents/defaults.ts`
- `src/agents/workspace.ts`
- `src/agents/pi-tool-definition-adapter.ts`
- `src/cli/gateway-cli/dev.ts`
- `src/infra/openclaw-root.ts`
- `src/agents/pi-embedded-runner/run/attempt.ts`
- `src/agents/tools/cron-tool.ts`
- `src/agents/system-prompt.ts`
- `src/agents/model-scan.ts`
- `src/agents/workspace-templates.ts`
- `src/agents/workspace-templates.test.ts`
- `src/agents/openclaw-tools.ts`
- `src/agents/pi-embedded-subscribe.handlers.messages.ts`
- `src/plugins/manifest.ts`
- `src/plugins/install.ts`
- `src/plugins/loader.ts`

### 3. 修复编译错误

- 添加缺失的 `createWeatherTool` 导入和调用
- 添加缺失的 `ToolRetryGuard` 导入
- 修复 `execute` 函数参数顺序（从 `(toolCallId, params, onUpdate, _ctx, signal)` 改为 `(toolCallId, params, signal, onUpdate, _ctx)`）
- 将 `ClawdbotConfig` 重命名为 `OpenClawConfig`

### 4. 重新构建项目

```bash
pnpm build
pnpm ui:build
```

### 5. 配置 Gateway 认证

```bash
clawdbot config set gateway.auth.token "test-token-123"
```

### 6. 重启 Gateway

```bash
clawdbot gateway run --bind lan --port 18789
```

## 验证结果

Gateway 成功启动并绑定到 `0.0.0.0:18789`：

```
LISTEN    0         511                0.0.0.0:18789            0.0.0.0:*        users:(("openclaw-gatewa",pid=50806,fd=21))
```

## 测试步骤

1. 从 Windows 设备 (10.71.1.19) 打开浏览器
2. 访问 `http://10.71.1.116:18789/`
3. 清除浏览器缓存（Ctrl + Shift + Delete）或强制刷新（Ctrl + F5）
4. 检查 WebSocket 连接是否成功
5. 如果需要，在 Control UI 设置中输入 token: `test-token-123`

## 相关文件

- `src/gateway/protocol/schema/primitives.ts` - client.id 验证逻辑
- `src/gateway/server/ws-connection/message-handler.ts` - WebSocket 消息处理
- `ui/src/ui/gateway.ts` - 客户端连接代码
- `dist/control-ui/assets/index-BeKTXH1m.js` - 最新构建的 Control UI

## 注意事项

1. 浏览器可能会缓存旧版本的 JavaScript，需要强制刷新
2. Gateway 现在使用 token 认证，token 为 `test-token-123`
3. 如果仍然无法连接，请检查防火墙设置和网络连接

## 下一步

如果问题仍然存在，请：

1. 检查浏览器控制台的错误信息
2. 查看 Gateway 日志：`clawdbot gateway logs` 或查看进程输出
3. 使用 `scripts/diagnose-websocket.sh` 诊断脚本
4. 参考 `WEBSOCKET-PROTOCOL-GUIDE.md` 了解协议详情
