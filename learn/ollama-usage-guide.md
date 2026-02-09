# Clawdbot + Ollama 使用指南

## ✅ 当前状态

- **Clawdbot 版本**: 2026.1.24-1
- **Ollama 服务**: 运行中
- **配置模型**: ollama/qwen2.5:7b
- **网关**: 运行中 (PID 97715, 端口 18789)

## 📝 使用方法

### 方法 1: 使用 TUI (终端用户界面) - 推荐 ⭐

```bash
clawdbot tui
```

这会打开一个交互式终端界面，你可以直接输入问题。

### 方法 2: 直接使用 Ollama CLI - 最简单 ⭐⭐⭐

```bash
ollama run qwen2.5:7b "什么是 MSTP 协议？"
```

这是测试模型最直接的方法！

### 方法 3: 通过网关发送消息

```bash
# 需要先获取或创建一个 session
clawdbot agent --agent main --message "你的问题"
```

### 方法 4: 使用 Ollama API

```bash
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "什么是 MSTP 协议？",
  "stream": false
}'
```

## 🔧 常用命令

```bash
# 查看模型列表
clawdbot models list

# 查看网关状态
clawdbot gateway status

# 查看 Ollama 模型
ollama list

# 停止网关
clawdbot gateway stop

# 启动网关
clawdbot gateway start
```

## ⚠️ 重要提示

1. **没有 `ask` 命令**: v2026.1.24-1 中使用 `agent` 而不是 `ask`
2. **网关端点**: `/v1/models` 不存在（Clawdbot 不是 OpenAI API）
3. **推荐方式**: 
   - 交互式使用 → `clawdbot tui`
   - 快速测试 → `ollama run qwen2.5:7b "问题"`

## 🎯 快速测试 MSTP 协议查询

```bash
# 方法 1: 使用 Ollama CLI（最简单）
ollama run qwen2.5:7b "什么是 MSTP 协议？请用中文简要介绍。"

# 方法 2: 使用 Clawdbot TUI
clawdbot tui
# 然后在界面中输入: 什么是 MSTP 协议？
```

## 📚 相关文档

- 完整配置: ~/ollama-setup-complete.txt
- 安装总结: ~/openclaw-installation-summary.txt
- 快速参考: ~/ollama-quick-reference.sh
