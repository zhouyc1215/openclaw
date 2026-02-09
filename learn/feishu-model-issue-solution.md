# 飞书 Clawdbot 模型问题分析和解决方案

## 问题描述

飞书端收到的回复都是工具调用的原始格式：
```
{"name": "system", "arguments": {}}
</tool_call>
```

或者：
```
{"name": "feishu_wiki", "arguments": {"action": "nodes", "title": ""}}
```

## 根本原因

**qwen2.5:1.5b 模型太小（1.5B 参数），无法正确理解和执行工具调用。**

### 问题分析

1. **模型能力不足**
   - 1.5B 参数的模型无法理解复杂的工具调用协议
   - 模型只是"模仿"工具调用的格式，而不是真正执行

2. **输出格式错误**
   - 模型输出了工具调用的 JSON 格式
   - 甚至包含了 XML 标签 `</tool_call>`
   - 这些内容被直接发送给用户

3. **工具未执行**
   - 日志显示：`deliver called: text={"name": "system", "arguments": {}}`
   - 工具调用没有被解析和执行
   - 原始文本直接发送到飞书

---

## 解决方案

### 方案1: 使用更大的模型（推荐）

#### 选项A: qwen2.5:7b（推荐）
```bash
# 下载模型
ollama pull qwen2.5:7b

# 更新配置
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:7b"

# 重启 Gateway
pnpm clawdbot gateway restart
```

**优点**：
- ✅ 7B 参数，能力强大
- ✅ 支持工具调用
- ✅ 中英文都很好
- ✅ 上下文窗口 32K

**缺点**：
- ⚠️ 模型大小约 4.7GB
- ⚠️ CPU 占用较高
- ⚠️ 响应时间较长（约 2-3 分钟）

#### 选项B: qwen2.5:3b（平衡选择）
```bash
# 下载模型
ollama pull qwen2.5:3b

# 更新配置
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:3b"

# 重启 Gateway
pnpm clawdbot gateway restart
```

**优点**：
- ✅ 3B 参数，能力较好
- ✅ 可能支持简单的工具调用
- ✅ 模型大小适中（约 2GB）
- ✅ 响应时间适中

**缺点**：
- ⚠️ 工具调用能力可能不如 7B
- ⚠️ 复杂任务可能失败

---

### 方案2: 禁用工具（不推荐）

如果必须使用 1.5B 模型，可以禁用工具：

```bash
# 禁用所有工具
pnpm clawdbot config set tools.deny '["*"]'

# 或者只禁用飞书工具
pnpm clawdbot config set tools.deny '["feishu_doc","feishu_wiki","feishu_drive","feishu_bitable"]'

# 重启 Gateway
pnpm clawdbot gateway restart
```

**优点**：
- ✅ 可以继续使用 1.5B 模型
- ✅ 响应快

**缺点**：
- ❌ 无法使用飞书文档、知识库等工具
- ❌ 功能大幅受限

---

### 方案3: 使用云端模型（最佳但需要 API Key）

使用更强大的云端模型：

#### OpenAI GPT-4
```bash
# 设置 API Key
export OPENAI_API_KEY="your_key_here"

# 更新配置
pnpm clawdbot config set agents.defaults.model.primary "openai/gpt-4"

# 重启 Gateway
pnpm clawdbot gateway restart
```

#### Anthropic Claude
```bash
# 设置 API Key
export ANTHROPIC_API_KEY="your_key_here"

# 更新配置
pnpm clawdbot config set agents.defaults.model.primary "anthropic/claude-3-5-sonnet-20241022"

# 重启 Gateway
pnpm clawdbot gateway restart
```

**优点**：
- ✅ 能力最强
- ✅ 工具调用完美支持
- ✅ 响应快
- ✅ 质量最高

**缺点**：
- ❌ 需要付费 API Key
- ❌ 需要网络连接
- ❌ 有使用成本

---

## 推荐配置

### 配置1: 本地 qwen2.5:7b（推荐）

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama-local",
        "api": "openai-completions",
        "models": [
          {
            "id": "qwen2.5:7b",
            "name": "Qwen 2.5 7B",
            "contextWindow": 32768,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "workspace": "~/clawd",
      "repoRoot": "~/clawdbot",
      "model": {
        "primary": "ollama/qwen2.5:7b"
      },
      "thinkingDefault": "low",
      "verboseDefault": "off",
      "timeoutSeconds": 600
    }
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_a90d40fc70b89bc2",
      "appSecret": "jEFgKlvjq5c0aYRuh7YaecohSuV7IPUF",
      "domain": "feishu",
      "groupPolicy": "allowlist",
      "connectionMode": "websocket"
    }
  }
}
```

### 配置2: 混合模式（主模型 + 备用模型）

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen2.5:7b",
        "fallbacks": ["ollama/qwen2.5:3b"]
      }
    }
  }
}
```

---

## 快速修复步骤

### 步骤1: 下载更大的模型
```bash
ollama pull qwen2.5:7b
```

### 步骤2: 更新配置
```bash
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:7b"
pnpm clawdbot config set agents.defaults.timeoutSeconds 600
```

### 步骤3: 重启 Gateway
```bash
pnpm clawdbot gateway restart
```

### 步骤4: 测试
在飞书中发送消息测试

---

## 模型对比

| 模型 | 参数量 | 大小 | 工具调用 | 响应时间 | 推荐度 |
|------|--------|------|----------|----------|--------|
| qwen2.5:1.5b | 1.5B | 986MB | ❌ 不支持 | ~80秒 | ⭐ |
| qwen2.5:3b | 3B | ~2GB | ⚠️ 部分支持 | ~120秒 | ⭐⭐⭐ |
| qwen2.5:7b | 7B | ~4.7GB | ✅ 支持 | ~180秒 | ⭐⭐⭐⭐⭐ |
| qwen2.5:14b | 14B | ~9GB | ✅ 完美支持 | ~300秒 | ⭐⭐⭐⭐ |
| GPT-4 | - | 云端 | ✅ 完美支持 | ~5秒 | ⭐⭐⭐⭐⭐ |
| Claude-3.5 | - | 云端 | ✅ 完美支持 | ~5秒 | ⭐⭐⭐⭐⭐ |

---

## 验证修复

### 1. 检查模型配置
```bash
pnpm clawdbot config get agents.defaults.model
```

### 2. 查看 Gateway 日志
```bash
tail -f /tmp/clawdbot/clawdbot-2026-02-08.log | grep "agent model"
```

应该看到：
```
[gateway] agent model: ollama/qwen2.5:7b
```

### 3. 测试工具调用
在飞书中发送：
```
帮我列出知识库空间
```

**预期结果**：
- 模型应该调用 `feishu_wiki` 工具
- 返回知识库列表
- 而不是返回 JSON 格式的工具调用

---

## 常见问题

### Q1: 下载 7B 模型很慢怎么办？
**答**: 可以先试试 3B 模型：
```bash
ollama pull qwen2.5:3b
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:3b"
```

### Q2: 7B 模型响应太慢怎么办？
**答**: 
1. 增加超时时间：`pnpm clawdbot config set agents.defaults.timeoutSeconds 900`
2. 或者使用云端模型（需要 API Key）

### Q3: 没有 GPU，7B 模型能跑吗？
**答**: 可以，但会很慢。建议：
- 使用 3B 模型
- 或者使用云端模型

### Q4: 如何回退到 1.5B 模型？
**答**:
```bash
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:1.5b"
pnpm clawdbot config set tools.deny '["*"]'  # 禁用所有工具
pnpm clawdbot gateway restart
```

---

## 总结

**问题根源**: qwen2.5:1.5b 模型太小，无法正确处理工具调用

**最佳解决方案**: 升级到 qwen2.5:7b 或更大的模型

**快速修复**:
```bash
ollama pull qwen2.5:7b
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:7b"
pnpm clawdbot gateway restart
```

**验证**: 在飞书中测试，应该能看到正常的回复而不是 JSON 格式的工具调用
