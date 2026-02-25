# WebSocket 协议详解

## 目录

1. [什么是 WebSocket](#什么是-websocket)
2. [为什么需要 WebSocket](#为什么需要-websocket)
3. [WebSocket 工作原理](#websocket-工作原理)
4. [协议握手过程](#协议握手过程)
5. [数据帧格式](#数据帧格式)
6. [OpenClaw 中的 WebSocket 实现](#openclaw-中的-websocket-实现)
7. [常见问题与调试](#常见问题与调试)

---

## 什么是 WebSocket

WebSocket 是一种在单个 TCP 连接上进行全双工通信的协议。它使得客户端和服务器之间的数据交换变得更加简单，允许服务端主动向客户端推送数据。

### 核心特性

- **全双工通信**：客户端和服务器可以同时发送和接收数据
- **持久连接**：一次握手后保持连接，无需重复建立
- **低延迟**：没有 HTTP 请求/响应的开销
- **轻量级**：数据帧头部开销小（2-14 字节）
- **支持二进制和文本**：可以传输任意格式的数据

### 与 HTTP 的对比

| 特性       | HTTP                      | WebSocket              |
| ---------- | ------------------------- | ---------------------- |
| 通信模式   | 请求-响应（半双工）       | 全双工                 |
| 连接       | 短连接（HTTP/1.1 可保持） | 长连接                 |
| 服务器推送 | 不支持（需轮询）          | 原生支持               |
| 协议开销   | 每次请求都有完整 HTTP 头  | 握手后仅 2-14 字节帧头 |
| 实时性     | 差（需轮询或长轮询）      | 优秀                   |

---

## 为什么需要 WebSocket

### 传统 HTTP 的局限性

在 WebSocket 出现之前，实现实时通信主要有以下方式：

1. **轮询（Polling）**

   ```javascript
   // 客户端每隔一段时间发送请求
   setInterval(() => {
     fetch("/api/messages")
       .then((res) => res.json())
       .then((data) => updateUI(data));
   }, 1000); // 每秒请求一次
   ```

   - 缺点：大量无效请求，浪费带宽和服务器资源

2. **长轮询（Long Polling）**

   ```javascript
   // 客户端发送请求，服务器有数据才返回
   function longPoll() {
     fetch("/api/messages?timeout=30")
       .then((res) => res.json())
       .then((data) => {
         updateUI(data);
         longPoll(); // 继续下一次长轮询
       });
   }
   ```

   - 缺点：仍需频繁建立连接，延迟较高

3. **Server-Sent Events (SSE)**
   - 单向推送，客户端无法主动发送数据
   - 不支持二进制数据

### WebSocket 的优势

- **真正的双向通信**：服务器和客户端都可以主动发送消息
- **低延迟**：消息可以立即发送，无需等待
- **高效**：减少了 HTTP 头部开销
- **适用场景**：
  - 聊天应用
  - 实时协作工具
  - 在线游戏
  - 股票行情推送
  - IoT 设备通信
  - **AI Agent 交互**（OpenClaw 的核心场景）

---

## WebSocket 工作原理

### 1. 连接建立流程

```
客户端                                服务器
  |                                     |
  |  HTTP Upgrade Request              |
  |------------------------------------>|
  |  GET /chat HTTP/1.1                |
  |  Upgrade: websocket                |
  |  Connection: Upgrade               |
  |  Sec-WebSocket-Key: xxx            |
  |                                     |
  |  HTTP 101 Switching Protocols      |
  |<------------------------------------|
  |  Upgrade: websocket                |
  |  Connection: Upgrade               |
  |  Sec-WebSocket-Accept: yyy         |
  |                                     |
  |  WebSocket 连接建立                 |
  |<===================================>|
  |                                     |
  |  数据帧交换                          |
  |<===================================>|
  |                                     |
```

### 2. 握手请求示例

**客户端请求：**

```http
GET /chat HTTP/1.1
Host: example.com:8080
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: http://example.com
```

**服务器响应：**

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

### 3. 关键握手字段

- **Upgrade: websocket** - 请求升级到 WebSocket 协议
- **Connection: Upgrade** - 表示这是一个升级请求
- **Sec-WebSocket-Key** - 客户端生成的随机 Base64 编码值
- **Sec-WebSocket-Version** - WebSocket 协议版本（通常是 13）
- **Sec-WebSocket-Accept** - 服务器根据 Key 计算的响应值

**Accept 值计算方法：**

```javascript
// 服务器端计算
const key = request.headers["sec-websocket-key"];
const magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"; // RFC 6455 定义的魔术字符串
const accept = crypto
  .createHash("sha1")
  .update(key + magic)
  .digest("base64");
```

---

## 协议握手过程

### 完整握手流程

```javascript
// 1. 客户端发起 WebSocket 连接
const ws = new WebSocket("ws://10.71.1.116:18789/");

// 2. 浏览器自动发送 HTTP Upgrade 请求
// GET / HTTP/1.1
// Host: 10.71.1.116:18789
// Upgrade: websocket
// Connection: Upgrade
// Sec-WebSocket-Key: [随机生成]
// Sec-WebSocket-Version: 13

// 3. 服务器验证并响应
// HTTP/1.1 101 Switching Protocols
// Upgrade: websocket
// Connection: Upgrade
// Sec-WebSocket-Accept: [计算得出]

// 4. 连接建立，触发 open 事件
ws.onopen = () => {
  console.log("WebSocket 连接已建立");
  // 可以开始发送数据
  ws.send(JSON.stringify({ type: "hello" }));
};

// 5. 接收消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("收到消息:", data);
};

// 6. 处理错误
ws.onerror = (error) => {
  console.error("WebSocket 错误:", error);
};

// 7. 连接关闭
ws.onclose = (event) => {
  console.log("连接关闭:", event.code, event.reason);
};
```

### 关闭握手

```
客户端                                服务器
  |                                     |
  |  Close Frame (code: 1000)          |
  |------------------------------------>|
  |                                     |
  |  Close Frame (code: 1000)          |
  |<------------------------------------|
  |                                     |
  |  TCP 连接关闭                        |
  |                                     |
```

**常见关闭代码：**

- `1000` - 正常关闭
- `1001` - 端点离开（如页面关闭）
- `1002` - 协议错误
- `1003` - 不支持的数据类型
- `1006` - 异常关闭（无关闭帧）
- `1008` - 策略违规（OpenClaw 中用于验证失败）
- `1009` - 消息过大
- `1011` - 服务器错误
- `1012` - 服务重启

---

## 数据帧格式

### WebSocket 帧结构

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
:                     Payload Data continued ...                :
+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
```

### 字段说明

1. **FIN (1 bit)** - 是否为最后一个分片
   - `1` = 最后一个分片
   - `0` = 还有后续分片

2. **RSV1, RSV2, RSV3 (各 1 bit)** - 保留位，通常为 0

3. **Opcode (4 bits)** - 操作码
   - `0x0` - 继续帧
   - `0x1` - 文本帧（UTF-8）
   - `0x2` - 二进制帧
   - `0x8` - 关闭连接
   - `0x9` - Ping
   - `0xA` - Pong

4. **MASK (1 bit)** - 是否使用掩码
   - 客户端发送的数据必须掩码（`1`）
   - 服务器发送的数据不掩码（`0`）

5. **Payload length (7 bits, 7+16 bits, 或 7+64 bits)**
   - `0-125` - 实际长度
   - `126` - 后续 16 位表示长度
   - `127` - 后续 64 位表示长度

6. **Masking-key (0 或 4 bytes)** - 掩码密钥

7. **Payload Data** - 实际数据

### 数据掩码

客户端发送的所有数据必须使用掩码：

```javascript
// 掩码算法
for (let i = 0; i < payloadLength; i++) {
  maskedData[i] = originalData[i] ^ maskingKey[i % 4];
}
```

**为什么需要掩码？**

- 防止缓存污染攻击
- 防止代理服务器误解析 WebSocket 数据

---

## OpenClaw 中的 WebSocket 实现

### 1. Gateway WebSocket 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Control UI (浏览器)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  GatewayBrowserClient                                │  │
│  │  - 连接管理                                           │  │
│  │  - 自动重连                                           │  │
│  │  - 请求/响应匹配                                      │  │
│  │  - 事件分发                                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket
                            │ ws://10.71.1.116:18789/
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Gateway Server                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WebSocket Server (ws)                               │  │
│  │  - 连接验证                                           │  │
│  │  - 协议版本协商                                       │  │
│  │  - 客户端认证                                         │  │
│  │  - 消息路由                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Protocol Handler                                    │  │
│  │  - 帧解析                                             │  │
│  │  - Schema 验证                                        │  │
│  │  - 方法调用                                           │  │
│  │  - 事件广播                                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2. OpenClaw WebSocket 协议

OpenClaw 在 WebSocket 之上定义了自己的应用层协议：

#### 帧类型

```typescript
// 请求帧
type RequestFrame = {
  type: "req";
  id: string; // 唯一请求 ID
  method: string; // 方法名，如 "connect", "chat.send"
  params?: unknown; // 方法参数
};

// 响应帧
type ResponseFrame = {
  type: "res";
  id: string; // 对应的请求 ID
  ok: boolean; // 是否成功
  payload?: unknown; // 返回数据
  error?: {
    // 错误信息
    code: string;
    message: string;
    details?: unknown;
  };
};

// 事件帧
type EventFrame = {
  type: "event";
  event: string; // 事件名，如 "chat", "agent"
  payload?: unknown; // 事件数据
  seq?: number; // 序列号（用于检测丢失）
  stateVersion?: {
    // 状态版本
    presence?: number;
    health?: number;
  };
};
```

#### 连接握手流程

```javascript
// 1. WebSocket 连接建立后，服务器发送挑战
{
  type: 'event',
  event: 'connect.challenge',
  payload: {
    nonce: 'random-uuid',
    ts: 1234567890
  }
}

// 2. 客户端发送 connect 请求
{
  type: 'req',
  id: 'request-uuid',
  method: 'connect',
  params: {
    minProtocol: 3,
    maxProtocol: 3,
    client: {
      id: 'openclaw-control-ui',  // 客户端标识
      version: '2026.2.6-3',
      platform: 'web',
      mode: 'webchat'
    },
    device: {                      // 设备认证（可选）
      id: 'device-uuid',
      publicKey: '...',
      signature: '...',
      signedAt: 1234567890
    },
    auth: {                        // 认证信息（可选）
      token: 'gateway-token',
      password: 'gateway-password'
    }
  }
}

// 3. 服务器响应 hello-ok
{
  type: 'res',
  id: 'request-uuid',
  ok: true,
  payload: {
    type: 'hello-ok',
    protocol: 3,
    server: {
      version: '2026.2.6-3',
      connId: 'connection-uuid'
    },
    features: {
      methods: ['chat.send', 'agent.identity.get', ...],
      events: ['chat', 'agent', 'presence', ...]
    },
    snapshot: {                    // 初始状态快照
      presence: [...],
      health: {...}
    }
  }
}
```

### 3. 客户端实现示例

```typescript
// ui/src/ui/gateway.ts
class GatewayBrowserClient {
  private ws: WebSocket | null = null;
  private pending = new Map<
    string,
    {
      resolve: (value: unknown) => void;
      reject: (error: Error) => void;
    }
  >();

  connect() {
    this.ws = new WebSocket(this.opts.url);

    this.ws.addEventListener("open", () => {
      this.queueConnect();
    });

    this.ws.addEventListener("message", (event) => {
      this.handleMessage(String(event.data));
    });

    this.ws.addEventListener("close", (event) => {
      this.opts.onClose?.({
        code: event.code,
        reason: event.reason,
      });
      this.scheduleReconnect();
    });
  }

  async request<T>(method: string, params?: unknown): Promise<T> {
    const id = randomUUID();
    const frame: RequestFrame = {
      type: "req",
      id,
      method,
      params,
    };

    const promise = new Promise<T>((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });

    this.ws?.send(JSON.stringify(frame));
    return promise;
  }

  private handleMessage(raw: string) {
    const frame = JSON.parse(raw);

    if (frame.type === "res") {
      const pending = this.pending.get(frame.id);
      if (pending) {
        this.pending.delete(frame.id);
        if (frame.ok) {
          pending.resolve(frame.payload);
        } else {
          pending.reject(new Error(frame.error?.message));
        }
      }
    } else if (frame.type === "event") {
      this.opts.onEvent?.(frame);
    }
  }
}
```

### 4. 服务器端实现

```typescript
// src/gateway/server/ws-connection.ts
wss.on('connection', (socket, upgradeReq) => {
  // 1. 发送连接挑战
  const connectNonce = randomUUID();
  socket.send(JSON.stringify({
    type: 'event',
    event: 'connect.challenge',
    payload: { nonce: connectNonce, ts: Date.now() }
  }));

  // 2. 等待 connect 请求
  socket.on('message', (raw) => {
    const frame = JSON.parse(raw.toString());

    if (frame.type === 'req' && frame.method === 'connect') {
      // 3. 验证连接参数
      if (!validateConnectParams(frame.params)) {
        socket.close(1008,
          `invalid connect params: ${formatValidationErrors(
            validateConnectParams.errors
          )}`
        );
        return;
      }

      // 4. 验证客户端 ID
      const clientId = frame.params.client.id;
      if (!isValidClientId(clientId)) {
        socket.close(1008, 'invalid client id');
        return;
      }

      // 5. 认证
      if (!authenticate(frame.params.auth, frame.params.device)) {
        socket.close(1008, 'authentication failed');
        return;
      }

      // 6. 发送 hello-ok
      socket.send(JSON.stringify({
        type: 'res',
        id: frame.id,
        ok: true,
        payload: buildHelloOk()
      }));

      // 7. 连接建立成功
      clients.add({ socket, clientId, ... });
    }
  });
});
```

---

## 常见问题与调试

### 1. 连接失败排查

**问题：WebSocket 连接无法建立**

检查清单：

```bash
# 1. 检查 Gateway 是否运行
ss -ltnp | grep 18789

# 2. 检查防火墙
sudo iptables -L -n | grep 18789

# 3. 测试 HTTP 连接
curl http://10.71.1.116:18789/

# 4. 使用 wscat 测试 WebSocket
npm install -g wscat
wscat -c ws://10.71.1.116:18789/
```

### 2. 握手失败（1008 错误）

**错误信息：**

```
disconnected (1008): invalid connect params:
at /client/id: must be equal to constant;
at /client/id: must match a schema in anyOf
```

**原因：**

- 客户端发送的 `client.id` 不在服务器允许的列表中
- 浏览器缓存了旧版本的 Control UI

**解决方案：**

```bash
# 1. 清除浏览器缓存
# Chrome: Ctrl + Shift + Delete

# 2. 强制刷新
# Chrome: Ctrl + F5

# 3. 重新构建 Control UI
pnpm ui:build

# 4. 重启 Gateway
pkill -9 -f clawdbot-gateway
clawdbot gateway run --bind lan --port 18789
```

### 3. 浏览器开发者工具调试

**查看 WebSocket 连接：**

1. 打开开发者工具（F12）
2. 切换到 Network 标签
3. 筛选 WS（WebSocket）
4. 点击连接查看详情

**查看帧数据：**

```
Messages 标签显示：
↑ 发送的帧（绿色）
↓ 接收的帧（白色）
```

**常见帧示例：**

```json
// 发送 connect 请求
↑ {
  "type": "req",
  "id": "abc-123",
  "method": "connect",
  "params": {
    "client": {
      "id": "openclaw-control-ui",
      "version": "2026.2.6-3"
    }
  }
}

// 接收 hello-ok 响应
↓ {
  "type": "res",
  "id": "abc-123",
  "ok": true,
  "payload": {
    "type": "hello-ok",
    "protocol": 3
  }
}

// 接收 chat 事件
↓ {
  "type": "event",
  "event": "chat",
  "payload": {
    "state": "delta",
    "message": "Hello, world!"
  }
}
```

### 4. 服务器端日志

```bash
# 查看 Gateway 日志
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log

# 筛选 WebSocket 相关日志
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log | grep "gateway/ws"

# 查看连接错误
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log | grep "closed before connect"
```

### 5. 性能监控

**客户端监控：**

```javascript
const ws = new WebSocket("ws://10.71.1.116:18789/");

// 监控消息大小
ws.addEventListener("message", (event) => {
  console.log("Message size:", event.data.length, "bytes");
});

// 监控延迟
const startTime = Date.now();
ws.send(JSON.stringify({ type: "ping" }));
ws.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "pong") {
    console.log("Latency:", Date.now() - startTime, "ms");
  }
});
```

**服务器端监控：**

```typescript
// 连接数统计
console.log("Active connections:", clients.size);

// 消息速率
let messageCount = 0;
setInterval(() => {
  console.log("Messages/sec:", messageCount);
  messageCount = 0;
}, 1000);

socket.on("message", () => {
  messageCount++;
});
```

---

## 最佳实践

### 1. 连接管理

```javascript
class RobustWebSocket {
  constructor(url) {
    this.url = url;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("Connected");
      this.reconnectDelay = 1000; // 重置延迟
    };

    this.ws.onclose = () => {
      console.log("Disconnected, reconnecting...");
      setTimeout(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        this.connect();
      }, this.reconnectDelay);
    };
  }
}
```

### 2. 心跳保活

```javascript
// 客户端
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ping" }));
  }
}, 30000); // 每 30 秒发送一次

// 服务器端
socket.on("message", (data) => {
  const frame = JSON.parse(data);
  if (frame.type === "ping") {
    socket.send(JSON.stringify({ type: "pong" }));
  }
});
```

### 3. 消息队列

```javascript
class MessageQueue {
  constructor(ws) {
    this.ws = ws;
    this.queue = [];
    this.processing = false;
  }

  send(message) {
    this.queue.push(message);
    this.process();
  }

  async process() {
    if (this.processing || this.queue.length === 0) {
      return;
    }

    this.processing = true;
    while (this.queue.length > 0) {
      const message = this.queue.shift();
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
    }
    this.processing = false;
  }
}
```

---

## 参考资料

- [RFC 6455 - The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [WebSocket.org](https://www.websocket.org/)
- [OpenClaw Gateway Protocol](./src/gateway/protocol/schema/frames.ts)

---

## 相关文档

- [OpenClaw 架构](./OPENCLAW-ARCHITECTURE.md)
- [WebSocket 连接修复指南](./WEBSOCKET-CONNECTION-FIX.md)
- [Gateway 局域网访问配置](./GATEWAY-LAN-ACCESS-SETUP.md)
- [Control UI 设置指南](./CONTROL-UI-SETUP-COMPLETE.md)
