# 飞书错误 520 深度分析

## 问题现状

即使配置了任务级别的超时（`timeoutSeconds`），飞书仍然收到错误消息：

```
unknown error, 520 (1000)
```

## 根本原因

通过日志分析发现：

1. **错误不是超时**：任务实际上成功完成了（例如 35.5 秒，远低于 120 秒的超时）
2. **错误来源**：`console.log` 在 `entry.js:971` 打印
3. **错误时机**：在 `embedded run done` 之后立即出现
4. **错误格式**：`unknown error, 520 (1000)`
   - `520`: HTTP 状态码（通常由 CDN/代理返回，表示"Unknown Error"）
   - `(1000)`: 用户 UID

## 日志证据

```json
{"0":"{\"subsystem\":\"agent/embedded\"}","1":"embedded run done: runId=754c8325-b9c0-4378-a5a9-e39d9f70492b sessionId=754c8325-b9c0-4378-a5a9-e39d9f70492b durationMs=35555 aborted=false"}
{"0":"unknown error, 520 (1000)","_meta":{"runtime":"node","path":{"fullFilePath":"file:///home/tsl/openclaw/dist/entry.js:971:46","method":"console.log"}}}
```

## 技术分析

### 1. 错误传播路径

```
Agent 任务完成
  → 尝试发送结果到飞书
  → 飞书 SDK 发起 HTTP 请求
  → 遇到网络错误（HTTP 520）
  → 错误被捕获
  → 通过 console.log 打印
  → 打印内容被误认为是用户消息
  → 发送到飞书
```

### 2. HTTP 520 错误

HTTP 520 是非标准状态码，通常由以下情况触发：

- **Cloudflare CDN**: 当源服务器返回空响应或未知错误
- **其他代理/负载均衡器**: 无法处理源服务器的响应
- **网络问题**: 连接中断、超时等

### 3. 飞书 API 调用

飞书 SDK (`@larksuiteoapi/node-sdk`) 在发送消息时：

```typescript
// extensions/feishu/src/send.ts
const response = await client.im.message.create({
  params: { receive_id_type: receiveIdType },
  data: {
    receive_id: receiveId,
    content,
    msg_type: msgType,
  },
});

if (response.code !== 0) {
  throw new Error(`Feishu send failed: ${response.msg || `code ${response.code}`}`);
}
```

如果 SDK 底层的 HTTP 请求遇到 520 错误，可能会抛出异常。

### 4. 错误处理链

可能的错误处理位置：

1. **Cron delivery 逻辑** (`src/cron/isolated-agent/run.ts`)
2. **Outbound delivery** (`src/infra/outbound/deliver.ts`)
3. **Feishu outbound adapter** (`extensions/feishu/src/outbound.ts`)
4. **某个全局错误处理器** 捕获并打印错误

## 可能的解决方案

### 方案 A：增加重试机制

为飞书消息发送添加重试逻辑，处理临时网络错误：

```typescript
// 在 extensions/feishu/src/send.ts 中添加重试
async function sendWithRetry(fn: () => Promise<any>, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      await new Promise((resolve) => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### 方案 B：改进错误处理

修改错误处理逻辑，避免将错误消息发送给用户：

1. 识别 HTTP 520 等网络错误
2. 记录到日志而不是 console.log
3. 不要将错误消息发送到飞书

### 方案 C：配置 bestEffort 模式

在 cron 任务配置中启用 `bestEffort` 模式，即使发送失败也不报错：

```json
{
  "delivery": {
    "mode": "announce",
    "channel": "feishu",
    "to": "ou_b3afb7d2133e4d689be523fc48f3d2b3",
    "bestEffort": true
  }
}
```

### 方案 D：临时禁用 delivery（不推荐）

如果问题持续，可以临时禁用结果发送：

```json
{
  "delivery": {
    "mode": "none"
  }
}
```

## 调试步骤

### 1. 查找错误打印位置

```bash
# 搜索可能打印 "unknown error" 的代码
grep -r "console.log" src/ extensions/ --include="*.ts" | grep -i error
```

### 2. 监控飞书 API 调用

```bash
# 查看飞书 API 调用日志
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -i "feishu\|520"
```

### 3. 测试飞书连接

```bash
# 手动发送测试消息
pnpm openclaw message send feishu:ou_b3afb7d2133e4d689be523fc48f3d2b3 "测试消息"
```

### 4. 检查网络连接

```bash
# 测试到飞书 API 的连接
curl -I https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
```

## 下一步行动

1. **短期**：启用 `bestEffort: true`，避免因发送失败导致任务报错
2. **中期**：添加重试机制和更好的错误处理
3. **长期**：改进日志系统，避免 console.log 输出被误认为用户消息

## 相关文件

- `extensions/feishu/src/send.ts` - 飞书消息发送
- `extensions/feishu/src/outbound.ts` - 飞书 outbound adapter
- `src/cron/isolated-agent/run.ts` - Cron 任务执行和 delivery
- `src/infra/outbound/deliver.ts` - 通用 outbound delivery

---

**分析时间**: 2026-02-27 10:45  
**分析人员**: Kiro AI Assistant  
**状态**: 🔍 调查中
