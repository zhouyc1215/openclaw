# 默认模型更改为 MiniMax

## 更改内容

将默认 AI 模型从 `ollama/qwen2.5:7b` 更改为 `minimax/MiniMax-M2.1`

## 执行命令

```bash
clawdbot config set agents.defaults.model.primary "minimax/MiniMax-M2.1"
```

## 验证结果

```bash
$ clawdbot config get agents.defaults.model.primary
minimax/MiniMax-M2.1
```

## MiniMax M2.1 模型信息

- **模型 ID**: MiniMax-M2.1
- **提供商**: MiniMax
- **API 端点**: https://api.minimaxi.com/v1
- **上下文窗口**: 200,000 tokens
- **最大输出**: 8,192 tokens
- **支持输入**: 文本
- **推理能力**: 否
- **成本**:
  - 输入: 15 tokens/元
  - 输出: 60 tokens/元
  - 缓存读取: 0
  - 缓存写入: 0

## 配置状态

### 当前配置文件: `~/.openclaw/openclaw.json`

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "minimax/MiniMax-M2.1"
      },
      "models": {
        "qwen-portal/qwen-turbo": {
          "alias": "qwen-turbo"
        },
        "qwen-portal/qwen-plus": {
          "alias": "qwen-plus"
        },
        "qwen-portal/qwen-max": {
          "alias": "qwen-max"
        }
      }
    }
  }
}
```

## 可用模型列表

### 主模型（默认）

- ✅ **minimax/MiniMax-M2.1** - MiniMax M2.1（200k 上下文）

### 备用模型

- qwen-portal/qwen-plus（别名：qwen-plus）- Qwen Plus（131k 上下文）
- qwen-portal/qwen-turbo（别名：qwen-turbo）- Qwen Turbo（131k 上下文）
- qwen-portal/qwen-max（别名：qwen-max）- Qwen Max（32k 上下文）
- ollama/qwen2.5:7b - Qwen 2.5 7B 本地模型（32k 上下文）
- ollama/qwen2.5:3b - Qwen 2.5 3B 本地模型（32k 上下文）
- ollama/qwen2.5:1.5b - Qwen 2.5 1.5B 本地模型（32k 上下文）

## Gateway 状态

- 运行中：PID 59074
- 绑定地址：0.0.0.0:18789
- 配置已自动重新加载

## 使用说明

### 默认使用 MiniMax

现在所有新的对话会话都将默认使用 MiniMax M2.1 模型。

### 临时切换模型

如果需要临时使用其他模型，可以在命令中指定：

```bash
# 使用 Qwen Plus
clawdbot chat --model qwen-plus "你的问题"

# 使用本地 Ollama 模型
clawdbot chat --model ollama/qwen2.5:7b "你的问题"
```

### 在飞书中切换模型

在飞书对话中，可以使用命令切换模型（如果支持）：

```
/model minimax/MiniMax-M2.1
/model qwen-plus
/model ollama/qwen2.5:7b
```

## 注意事项

### API Key 配置

MiniMax API Key 已在配置中设置：

```json
{
  "env": {
    "MINIMAX_API_KEY": "sk-api-PT9gHJYDG9PdBL097V52ddUKSoKh4OCZOHvkKRjbeAlvNZXJoy0GUcq3IHQCffPy0n-36YnB3jjvRDij7rC-K-C2hoejP6-BW4d1RkF3p9sLrcoKpDtfFPs"
  }
}
```

### 成本考虑

MiniMax M2.1 是付费模型，使用时会产生费用：

- 输入 token 成本较低（15/元）
- 输出 token 成本较高（60/元）
- 建议监控 API 使用量

### 性能特点

- **优势**:
  - 超大上下文窗口（200k tokens）
  - 适合处理长文档和复杂对话
  - 中文理解能力强
- **劣势**:
  - 有使用成本
  - 需要网络连接
  - 响应速度取决于网络和 API 负载

### 回退到本地模型

如果 MiniMax API 不可用或需要节省成本，可以随时切换回本地 Ollama 模型：

```bash
clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:7b"
```

## 相关文件

- `~/.openclaw/openclaw.json` - 主配置文件
- `update-openclaw-config.sh` - 配置更新脚本

## 测试建议

1. 在飞书中发送消息测试 MiniMax 模型响应
2. 观察响应质量和速度
3. 监控 API 使用量和成本
4. 根据需要调整模型选择

## 故障排查

如果遇到问题：

1. **API Key 错误**:

   ```bash
   # 检查 API Key 是否正确
   clawdbot config get env.MINIMAX_API_KEY
   ```

2. **网络连接问题**:

   ```bash
   # 测试 MiniMax API 连接
   curl -H "Authorization: Bearer YOUR_API_KEY" https://api.minimaxi.com/v1/models
   ```

3. **回退到本地模型**:

   ```bash
   clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:7b"
   ```

4. **查看日志**:
   ```bash
   # 查看 Gateway 日志
   journalctl --user -u openclaw-gateway.service -f
   ```
