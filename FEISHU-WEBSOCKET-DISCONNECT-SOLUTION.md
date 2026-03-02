# 飞书 WebSocket 连接断开问题解决方案

## 问题现象

- 飞书发送消息后长时间没有回复
- Gateway 正常运行，但无法接收飞书消息
- WebSocket 连接断开（`ss -tn` 看不到飞书服务器连接）

## 根本原因

### 1. WebSocket 连接僵死

**症状**：

- Gateway 运行一段时间后（通常 30-60 分钟），WebSocket 连接进入僵死状态
- 连接看起来是 ESTABLISHED，但实际上无法接收新消息
- 飞书服务器 IP：113.201.x.x, 123.6.x.x, 180.95.x.x

**原因**：

- 网络波动或临时断线
- 飞书服务器主动断开长时间空闲的连接
- NAT 超时（家庭路由器通常 30-60 分钟）
- Agent 长时间执行任务，期间没有心跳保持连接

### 2. 缺少自动重连机制

**当前实现**：

- 飞书 SDK (`@larksuiteoapi/node-sdk`) 的 `WSClient` 没有内置自动重连
- OpenClaw 的 `extensions/feishu/src/monitor.ts` 也没有实现重连逻辑
- 一旦连接断开，需要手动干预

**代码位置**：

```typescript
// extensions/feishu/src/monitor.ts
const wsClient = createFeishuWSClient(account);
wsClients.set(accountId, wsClient);
void wsClient.start({ eventDispatcher });
// 没有错误处理和重连逻辑
```

## 解决方案

### 方案 A：重启飞书频道（推荐，不重启 Gateway）

使用配置热重载机制触发频道重启：

```bash
/home/tsl/clawd/restart-feishu-channel.sh
```

**脚本内容**：

```bash
#!/bin/bash
# 重启飞书频道（不重启 Gateway）

CONFIG_FILE="$HOME/.openclaw/openclaw.json"

echo "正在重启飞书频道..."

# 备份配置
cp "$CONFIG_FILE" "$CONFIG_FILE.bak"

# 添加临时字段触发重载
jq '.channels.feishu._restart_trigger = (now | tostring)' "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

echo "等待 Gateway 检测配置变化..."
sleep 2

# 删除临时字段
jq 'del(.channels.feishu._restart_trigger)' "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

echo "飞书频道重启完成！"
```

**验证**：

```bash
# 检查 WebSocket 连接
ss -tn | grep -E "113.201|123.6|180.95"

# 检查频道状态
pnpm openclaw channels status --probe
```

### 方案 B：重启 Gateway（彻底但会中断所有服务）

```bash
pkill -9 -f openclaw-gateway
sleep 2
nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &
```

### 方案 C：定期自动重启（预防性）

创建定时任务，每小时重启一次飞书频道：

```bash
# 添加到 cron
0 * * * * /home/tsl/clawd/restart-feishu-channel.sh >> /tmp/feishu-restart.log 2>&1
```

或者创建 OpenClaw 定时任务：

```json
{
  "id": "restart-feishu-hourly",
  "name": "重启飞书频道",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 * * * *"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "Execute /home/tsl/clawd/restart-feishu-channel.sh to restart Feishu channel",
    "timeoutSeconds": 30
  },
  "delivery": {
    "mode": "none"
  }
}
```

## 长期解决方案（需要代码修改）

### 1. 添加 WebSocket 重连机制

修改 `extensions/feishu/src/monitor.ts`：

```typescript
async function monitorSingleAccount(params: {
  cfg: ClawdbotConfig;
  account: ResolvedFeishuAccount;
  runtime?: RuntimeEnv;
  abortSignal?: AbortSignal;
}): Promise<void> {
  const { cfg, account, runtime, abortSignal } = params;
  const { accountId } = account;
  const log = runtime?.log ?? console.log;
  const error = runtime?.error ?? console.error;

  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;
  const reconnectDelay = 5000; // 5 seconds

  const connect = async () => {
    try {
      const botOpenId = await fetchBotOpenId(account);
      botOpenIds.set(accountId, botOpenId ?? "");

      const wsClient = createFeishuWSClient(account);
      wsClients.set(accountId, wsClient);

      const eventDispatcher = createEventDispatcher(account);
      // ... register events ...

      await wsClient.start({ eventDispatcher });
      log(`feishu[${accountId}]: WebSocket connected`);
      reconnectAttempts = 0; // Reset on successful connection

      // Monitor connection health
      wsClient.on("close", () => {
        log(`feishu[${accountId}]: WebSocket closed, attempting reconnect...`);
        if (!abortSignal?.aborted && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          setTimeout(connect, reconnectDelay * reconnectAttempts);
        }
      });

      wsClient.on("error", (err) => {
        error(`feishu[${accountId}]: WebSocket error: ${err}`);
      });
    } catch (err) {
      error(`feishu[${accountId}]: connection failed: ${err}`);
      if (!abortSignal?.aborted && reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        setTimeout(connect, reconnectDelay * reconnectAttempts);
      }
    }
  };

  await connect();
}
```

### 2. 添加心跳保持连接

在 `monitor.ts` 中添加定期心跳：

```typescript
// 每 30 秒发送一次心跳
const heartbeatInterval = setInterval(() => {
  if (wsClient && !abortSignal?.aborted) {
    // 发送 ping 或调用 API 保持连接活跃
    wsClient.ping?.();
  }
}, 30000);

// 清理时停止心跳
abortSignal?.addEventListener("abort", () => {
  clearInterval(heartbeatInterval);
});
```

### 3. 添加连接监控

创建健康检查机制：

```typescript
// 每 5 分钟检查一次连接状态
const healthCheckInterval = setInterval(async () => {
  try {
    const result = await probeFeishu(account);
    if (!result.ok) {
      log(`feishu[${accountId}]: health check failed, reconnecting...`);
      await reconnect();
    }
  } catch (err) {
    error(`feishu[${accountId}]: health check error: ${err}`);
  }
}, 300000);
```

## 诊断命令

### 检查 WebSocket 连接

```bash
# 查看飞书服务器连接
ss -tn | grep -E "113.201|123.6|180.95"

# 查看 Gateway 进程
ps aux | grep openclaw-gateway

# 查看最近的飞书日志
journalctl -n 100 --no-pager | grep -i feishu
```

### 检查频道状态

```bash
# 基本状态
pnpm openclaw channels status

# 带探测的状态
pnpm openclaw channels status --probe
```

### 测试消息发送

```bash
pnpm openclaw message send \
  --channel feishu \
  --target ou_b3afb7d2133e4d689be523fc48f3d2b3 \
  --message "测试消息 - $(date '+%H:%M:%S')"
```

## 预防措施

1. **定期重启 Gateway**
   - 每天凌晨 4 点自动重启
   - 避免长时间运行导致的各种问题

2. **监控连接状态**
   - 创建监控脚本，定期检查 WebSocket 连接
   - 连接断开时自动重启频道

3. **优化 Agent 任务**
   - 避免单个任务执行时间过长（超过 30 分钟）
   - 长任务拆分成多个短任务

4. **网络优化**
   - 使用稳定的网络连接
   - 配置路由器增加 NAT 超时时间

## 相关文件

- `extensions/feishu/src/monitor.ts` - WebSocket 连接管理
- `extensions/feishu/src/client.ts` - 客户端创建
- `src/gateway/server-reload-handlers.ts` - 频道重启逻辑
- `src/gateway/config-reload.ts` - 配置热重载
- `/home/tsl/clawd/restart-feishu-channel.sh` - 重启脚本

## 总结

飞书 WebSocket 连接断开是由于缺少自动重连机制和长时间运行导致的。短期解决方案是使用重启脚本，长期需要在代码中添加重连和心跳机制。

---

**创建时间**: 2026-03-02 12:42  
**状态**: ✅ 已解决（短期方案）  
**待办**: 实现长期解决方案（自动重连）
