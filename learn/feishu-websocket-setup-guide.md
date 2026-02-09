# 飞书长连接配置指南

## 问题描述
在飞书开放平台配置事件订阅时，选择"使用长连接接收事件"返回错误：
```
应用未建立长连接
```

## 原因分析
飞书的长连接（WebSocket）机制要求：
1. **先启动应用并建立连接**
2. **然后在开放平台配置事件订阅**

顺序不能颠倒！必须先让 Clawdbot 连接到飞书，飞书检测到连接后，才能在后台配置事件订阅。

---

## 解决步骤

### 步骤1: 配置 Clawdbot

#### 方法A: 使用配置向导（推荐）
```bash
pnpm clawdbot configure
```

选择：
1. Channels → Configure/link
2. 选择 Feishu
3. 输入 App ID 和 App Secret
4. 其他选项可以使用默认值

#### 方法B: 手动编辑配置文件
编辑 `~/.clawdbot/clawdbot.json`：

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxxxxxxxxxxxx",
      "appSecret": "your_app_secret_here",
      "domain": "feishu",
      "connectionMode": "websocket",
      "dmPolicy": "pairing",
      "groupPolicy": "allowlist",
      "requireMention": true
    }
  },
  "gateway": {
    "mode": "local"
  }
}
```

**重要配置项**：
- `appId`: 从飞书开放平台获取
- `appSecret`: 从飞书开放平台获取
- `connectionMode`: 必须设置为 `"websocket"`
- `enabled`: 必须设置为 `true`

---

### 步骤2: 启动 Clawdbot Gateway

```bash
pnpm clawdbot gateway run
```

**预期输出**：
```
🦞 Clawdbot Gateway starting...
[feishu] Connecting to Feishu WebSocket...
[feishu] WebSocket connected successfully
[feishu] Long connection established
```

**重要**：保持这个进程运行！不要关闭终端。

---

### 步骤3: 验证连接状态

打开新的终端窗口，运行：

```bash
pnpm clawdbot channels status
```

**预期输出**：
```
Feishu: connected (websocket)
```

或者查看详细状态：

```bash
pnpm clawdbot status --deep
```

---

### 步骤4: 在飞书开放平台配置事件订阅

**现在**可以去飞书开放平台配置了：

1. 进入应用后台
2. 点击 **事件与回调**
3. 事件配置方式：选择 **使用长连接接收事件**
4. 此时应该不会再报错了
5. 添加事件订阅：
   - ✅ `im.message.receive_v1` - 接收消息（必需）
   - ✅ `im.message.message_read_v1` - 消息已读
   - ✅ `im.chat.member.bot.added_v1` - 机器人进群
   - ✅ `im.chat.member.bot.deleted_v1` - 机器人被移出群

6. 点击保存

---

## 常见问题

### Q1: 启动 Gateway 后仍然报错
**可能原因**：
- App ID 或 App Secret 配置错误
- 网络连接问题
- 飞书服务器延迟

**解决方法**：
```bash
# 1. 检查配置
pnpm clawdbot config get channels.feishu

# 2. 查看详细日志
pnpm clawdbot gateway run --verbose

# 3. 等待几秒后重试配置事件订阅
```

---

### Q2: Gateway 启动失败
**错误示例**：
```
Error: Invalid appId or appSecret
```

**解决方法**：
1. 检查 App ID 和 App Secret 是否正确
2. 确保没有多余的空格或引号
3. 重新从飞书开放平台复制凭证

```bash
# 重新设置
pnpm clawdbot config set channels.feishu.appId "cli_xxxxx"
pnpm clawdbot config set channels.feishu.appSecret "your_secret"
```

---

### Q3: 连接建立后断开
**可能原因**：
- 网络不稳定
- 防火墙阻止
- 飞书服务器维护

**解决方法**：
```bash
# 1. 检查网络连接
ping open.feishu.cn

# 2. 重启 Gateway
pnpm clawdbot gateway restart

# 3. 查看日志
pnpm clawdbot logs gateway
```

---

### Q4: 配置了事件但收不到消息
**检查清单**：
- ✅ Gateway 是否在运行？
- ✅ 长连接是否已建立？
- ✅ 事件订阅是否已保存？
- ✅ 权限是否已申请并通过？
- ✅ 应用是否已发布（至少测试版本）？

**验证命令**：
```bash
# 查看 Gateway 状态
pnpm clawdbot status

# 查看频道状态
pnpm clawdbot channels status --probe

# 查看最近的日志
pnpm clawdbot logs gateway --tail 50
```

---

## 完整配置示例

### 1. 最小配置
```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_a1b2c3d4e5f6g7h8",
      "appSecret": "your_secret_here",
      "connectionMode": "websocket"
    }
  },
  "gateway": {
    "mode": "local"
  }
}
```

### 2. 完整配置
```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_a1b2c3d4e5f6g7h8",
      "appSecret": "your_secret_here",
      "domain": "feishu",
      "connectionMode": "websocket",
      "dmPolicy": "pairing",
      "groupPolicy": "allowlist",
      "requireMention": true,
      "mediaMaxMb": 30,
      "renderMode": "auto"
    }
  },
  "gateway": {
    "mode": "local",
    "port": 18789,
    "bind": "loopback"
  },
  "agents": {
    "defaults": {
      "workspace": "~/clawd",
      "model": {
        "primary": "ollama/qwen2.5:1.5b"
      }
    }
  }
}
```

---

## 启动脚本

创建一个启动脚本方便使用：

```bash
#!/bin/bash
# ~/start-clawdbot-feishu.sh

echo "🦞 启动 Clawdbot Gateway..."

# 检查配置
if ! pnpm clawdbot config get channels.feishu.appId > /dev/null 2>&1; then
    echo "❌ 错误：飞书未配置"
    echo "请先运行: pnpm clawdbot configure"
    exit 1
fi

# 启动 Gateway
echo "📡 正在连接飞书..."
pnpm clawdbot gateway run

# 如果 Gateway 退出
echo "⚠️  Gateway 已停止"
```

使用方法：
```bash
chmod +x ~/start-clawdbot-feishu.sh
~/start-clawdbot-feishu.sh
```

---

## 后台运行（可选）

如果需要让 Gateway 在后台持续运行：

### 方法1: 使用 tmux
```bash
# 创建新会话
tmux new -s clawdbot

# 在 tmux 中启动
pnpm clawdbot gateway run

# 按 Ctrl+B 然后按 D 退出（保持运行）

# 重新连接
tmux attach -t clawdbot
```

### 方法2: 使用 systemd（Linux）
```bash
# 安装为系统服务
pnpm clawdbot service install

# 启动服务
sudo systemctl start clawdbot-gateway

# 查看状态
sudo systemctl status clawdbot-gateway

# 查看日志
sudo journalctl -u clawdbot-gateway -f
```

### 方法3: 使用 nohup
```bash
# 后台启动
nohup pnpm clawdbot gateway run > ~/clawdbot-gateway.log 2>&1 &

# 查看日志
tail -f ~/clawdbot-gateway.log

# 停止
pkill -f "clawdbot gateway"
```

---

## 调试技巧

### 1. 查看详细日志
```bash
# 启动时显示详细日志
pnpm clawdbot gateway run --verbose

# 或者设置环境变量
DEBUG=feishu:* pnpm clawdbot gateway run
```

### 2. 测试连接
```bash
# 测试飞书 API 连接
curl -X POST "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "your_app_id",
    "app_secret": "your_app_secret"
  }'
```

### 3. 检查配置
```bash
# 查看完整配置
pnpm clawdbot config get

# 只查看飞书配置
pnpm clawdbot config get channels.feishu

# 验证配置有效性
pnpm clawdbot doctor
```

---

## 时序图

```
用户                Clawdbot              飞书开放平台
 │                     │                      │
 │  1. 配置 App ID     │                      │
 │ ─────────────────> │                      │
 │                     │                      │
 │  2. 启动 Gateway    │                      │
 │ ─────────────────> │                      │
 │                     │                      │
 │                     │  3. 建立 WebSocket   │
 │                     │ ──────────────────> │
 │                     │                      │
 │                     │  4. 连接成功         │
 │                     │ <────────────────── │
 │                     │                      │
 │  5. 配置事件订阅    │                      │
 │ ──────────────────────────────────────> │
 │                     │                      │
 │  6. 保存成功        │                      │
 │ <────────────────────────────────────── │
 │                     │                      │
 │                     │  7. 接收事件         │
 │                     │ <────────────────── │
```

**关键点**：步骤3必须在步骤5之前完成！

---

## 总结

### 正确顺序
1. ✅ 配置 App ID 和 App Secret
2. ✅ 启动 Clawdbot Gateway
3. ✅ 等待长连接建立
4. ✅ 在飞书开放平台配置事件订阅
5. ✅ 测试消息收发

### 常见错误
❌ 先配置事件订阅，后启动 Gateway
✅ 先启动 Gateway，后配置事件订阅

### 验证成功
- Gateway 日志显示 "WebSocket connected"
- `pnpm clawdbot channels status` 显示 "connected"
- 飞书开放平台事件订阅配置成功
- 能够收发消息

---

**最后提醒**：保持 Gateway 运行状态，否则长连接会断开，需要重新配置！
