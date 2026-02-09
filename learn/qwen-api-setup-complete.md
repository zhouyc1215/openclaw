# Clawdbot 通义千问 API 配置完成

## 配置摘要

### 1. 清理工作
- ✅ 停止并删除星火桥接服务测试
- ✅ 删除 `~/openai-style-api` 目录
- ✅ 删除测试脚本 `~/test-spark-auth.py`

### 2. 模型配置
- **Provider**: `qwen-portal`
- **Base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **API Key**: `sk-3effff40719b46259d25ae1b16dfdaea`
- **API 类型**: `openai-completions`

### 3. 可用模型

| 模型 ID | 名称 | 上下文窗口 | 最大输出 | 成本 (输入/输出) |
|---------|------|-----------|---------|-----------------|
| `qwen-plus` | Qwen Plus | 131,072 | 8,192 | ¥0.0004 / ¥0.002 |
| `qwen-turbo` | Qwen Turbo | 131,072 | 8,192 | ¥0.0003 / ¥0.0006 |
| `qwen-max` | Qwen Max | 32,768 | 8,192 | ¥0.02 / ¥0.06 |

### 4. 默认配置
- **主模型**: `qwen-portal/qwen-plus`
- **上下文窗口**: 131,072 tokens
- **超时时间**: 600 秒（10 分钟）
- **思考模式**: low
- **并发数**: 1

### 5. 模型别名
- `qwen-plus` → `qwen-portal/qwen-plus`
- `qwen-turbo` → `qwen-portal/qwen-turbo`
- `qwen-max` → `qwen-portal/qwen-max`

## 验证结果

```bash
$ pnpm clawdbot models list

Model                                      Input      Ctx      Local Auth  Tags
qwen-portal/qwen-plus                      text       128k     no    yes   default,configured,alias:qwen-plus
qwen-portal/qwen-turbo                     text       128k     no    yes   configured,alias:qwen-turbo
qwen-portal/qwen-max                       text       32k      no    yes   configured,alias:qwen-max
```

✅ 所有模型状态正常，已配置并可用

## 服务状态

```bash
$ systemctl --user status clawdbot-gateway.service
● clawdbot-gateway.service - Clawdbot Gateway (v2026.1.24-1)
   Active: active (running)
```

✅ Gateway 服务运行正常
✅ 飞书 WebSocket 连接已建立

## 测试方法

### 方法 1: 在飞书群聊中测试
直接在飞书群里 @Clawdbot 发送消息：
```
@Clawdbot 你好，请用一句话介绍你自己
```

### 方法 2: 使用 CLI 测试（需要正确的 open_id）
```bash
pnpm clawdbot message send --channel feishu --target <正确的open_id> --message "测试消息"
```

## 配置文件位置
- **主配置**: `~/.clawdbot/clawdbot.json`
- **备份**: `~/.clawdbot/clawdbot.json.backup`

## 性能对比

| 模型 | 类型 | 响应速度 | 成本 | 推荐场景 |
|------|------|---------|------|---------|
| Ollama qwen2.5:3b | 本地 | 很慢（5分钟+超时） | 免费 | 离线/隐私场景 |
| Qwen Turbo | 云端 | 快（秒级） | 低 | 日常对话 |
| Qwen Plus | 云端 | 快（秒级） | 中 | 复杂任务（默认） |
| Qwen Max | 云端 | 快（秒级） | 高 | 高难度任务 |

## 下一步
现在可以在飞书中测试 Clawdbot 的响应速度和质量了。使用云端 API 后，响应速度应该从之前的 5 分钟超时降低到几秒钟内完成。
