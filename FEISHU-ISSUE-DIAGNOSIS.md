# 飞书消息无响应问题诊断

## 问题描述

飞书发送消息后没有响应。

## 根本原因

**飞书渠道未配置！**

通过 `clawdbot channels status` 检查发现：

```
- Feishu default: enabled, not configured, stopped, error:not configured
```

通过 `clawdbot config get channels.feishu` 确认：

```
Config path not found: channels.feishu
```

查看配置文件 `~/.openclaw/openclaw.json` 发现没有 `channels.feishu` 配置段。

## 当前配置状态

配置文件 `~/.openclaw/openclaw.json` 包含：

- ✅ models.providers.ollama - Ollama 模型配置
- ✅ agents.defaults - Agent 默认配置
- ✅ gateway - Gateway 配置（端口 18789，LAN 绑定，token 认证）
- ❌ channels.feishu - **缺失！**

## 解决方案

### 方案 1：使用命令行配置飞书

```bash
# 设置飞书 App ID
clawdbot config set channels.feishu.appId "YOUR_APP_ID"

# 设置飞书 App Secret
clawdbot config set channels.feishu.appSecret "YOUR_APP_SECRET"

# 设置飞书 Verification Token
clawdbot config set channels.feishu.verificationToken "YOUR_VERIFICATION_TOKEN"

# 设置飞书 Encrypt Key（如果启用了加密）
clawdbot config set channels.feishu.encryptKey "YOUR_ENCRYPT_KEY"

# 启用飞书渠道
clawdbot config set channels.feishu.enabled true

# 设置 DM 策略（可选）
clawdbot config set channels.feishu.dmPolicy "open"  # 或 "allowlist" 或 "disabled"

# 设置群组策略（可选）
clawdbot config set channels.feishu.groupPolicy "open"  # 或 "allowlist" 或 "disabled"
```

### 方案 2：直接编辑配置文件

编辑 `~/.openclaw/openclaw.json`，添加飞书配置：

```json
{
  "meta": {
    "lastTouchedVersion": "2026.2.6-3",
    "lastTouchedAt": "2026-02-25T09:13:49.514Z"
  },
  "models": {
    // ... 现有配置 ...
  },
  "agents": {
    // ... 现有配置 ...
  },
  "messages": {
    // ... 现有配置 ...
  },
  "commands": {
    // ... 现有配置 ...
  },
  "gateway": {
    // ... 现有配置 ...
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "YOUR_APP_ID",
      "appSecret": "YOUR_APP_SECRET",
      "verificationToken": "YOUR_VERIFICATION_TOKEN",
      "encryptKey": "YOUR_ENCRYPT_KEY",
      "dmPolicy": "open",
      "groupPolicy": "open",
      "allowFrom": [],
      "groupAllowFrom": []
    }
  }
}
```

### 方案 3：使用 onboarding 向导

```bash
clawdbot onboard feishu
```

这将启动交互式配置向导，引导你完成飞书配置。

## 配置参数说明

### 必需参数

- `appId`: 飞书应用的 App ID
- `appSecret`: 飞书应用的 App Secret
- `verificationToken`: 飞书应用的 Verification Token（用于验证回调请求）

### 可选参数

- `encryptKey`: 飞书应用的 Encrypt Key（如果启用了消息加密）
- `enabled`: 是否启用飞书渠道（默认 true）
- `dmPolicy`: 私聊策略
  - `"open"`: 接受所有私聊
  - `"allowlist"`: 只接受白名单用户的私聊
  - `"disabled"`: 禁用私聊
- `groupPolicy`: 群组策略
  - `"open"`: 接受所有群组消息
  - `"allowlist"`: 只接受白名单群组的消息
  - `"disabled"`: 禁用群组消息
- `allowFrom`: 私聊白名单（用户 open_id 列表）
- `groupAllowFrom`: 群组白名单（群组 chat_id 列表）

## 获取飞书应用凭证

1. 访问飞书开放平台：https://open.feishu.cn/
2. 创建或选择你的应用
3. 在"凭证与基础信息"页面获取：
   - App ID
   - App Secret
4. 在"事件订阅"页面获取：
   - Verification Token
   - Encrypt Key（如果启用了加密）

## 配置后的操作

1. 重启 Gateway：

   ```bash
   clawdbot gateway stop
   clawdbot gateway run --bind lan --port 18789
   ```

2. 验证配置：

   ```bash
   clawdbot channels status
   ```

3. 测试飞书连接：
   ```bash
   clawdbot channels probe feishu
   ```

## 其他注意事项

### 重复插件警告

日志中出现警告：

```
plugins.entries.feishu: plugin feishu: duplicate plugin id detected
```

这可能是因为飞书插件被加载了多次。检查：

- `~/.openclaw/plugins/` 目录
- 项目的 `extensions/feishu/` 目录
- 配置文件中的 `plugins.entries` 配置

### Gateway 日志

如果配置后仍有问题，可以查看 Gateway 日志：

```bash
# 查看运行中的 Gateway 进程
ps aux | grep openclaw-gateway

# 如果使用 systemd 服务
journalctl --user -u openclaw-gateway.service -f

# 或者直接运行 Gateway 查看输出
clawdbot gateway run --bind lan --port 18789
```

## 快速检查清单

- [ ] 飞书应用已创建并获取凭证
- [ ] 配置文件中添加了 `channels.feishu` 配置
- [ ] `appId`、`appSecret`、`verificationToken` 已正确填写
- [ ] `enabled` 设置为 `true`
- [ ] Gateway 已重启
- [ ] `clawdbot channels status` 显示飞书状态正常
- [ ] 飞书应用的事件订阅 URL 已配置为 Gateway 地址
