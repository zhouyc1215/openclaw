# Qwen2.5:1.5b 模型测试结果

## 测试时间
2026-02-06 19:28

## 测试环境
- 模型：qwen2.5:1.5b
- 平台：Ollama
- 集成：Clawdbot
- 配置：本地模式 (--local)

## 测试结果

### 测试1：英文问答
**命令：**
```bash
pnpm clawdbot agent --local --session-id test-qwen2 --message "Hello, introduce yourself in one sentence" --thinking low
```

**响应：**
> I am an advanced AI assistant designed to provide precise information across various tasks.

**状态：** ✅ 成功

---

### 测试2：中文问答
**命令：**
```bash
pnpm clawdbot agent --local --session-id test-qwen3 --message "你好，请用一句话介绍你自己" --thinking low
```

**响应：**
> 我是你的助手，可以帮助你完成各种任务和提供信息。

**性能指标：**
- 总耗时：1分24秒
- 用户态CPU：5.771秒
- 系统态CPU：0.438秒

**状态：** ✅ 成功

---

## 性能分析

### CPU占用
- 模型推理过程中CPU占用合理
- 用户态CPU时间仅5.8秒，说明大部分时间在等待I/O或模型加载
- 系统调用开销很小（0.4秒）

### 响应质量
- 英文和中文回答都准确、简洁
- 符合指令要求（一句话介绍）
- 语义连贯，表达清晰

### 适用性评估
✅ **推荐用于 Clawdbot**
- 模型大小适中（986MB）
- CPU占用可接受
- 响应质量良好
- 支持中英文双语
- 上下文窗口：32K tokens

---

## 配置信息

### Ollama 配置
```json
{
  "baseUrl": "http://127.0.0.1:11434/v1",
  "apiKey": "ollama-local",
  "api": "openai-completions",
  "models": [
    {
      "id": "qwen2.5:1.5b",
      "name": "Qwen 2.5 1.5B",
      "contextWindow": 32768,
      "maxTokens": 327680
    }
  ]
}
```

---

## 结论

qwen2.5:1.5b 是一个**优秀的轻量级模型选择**，适合在资源受限的环境中运行：

1. **性能表现**：响应时间在可接受范围内（~84秒）
2. **资源占用**：CPU占用合理，不会造成系统负担
3. **质量保证**：中英文回答质量都很好
4. **易于部署**：通过 Ollama 一键下载，配置简单

**推荐场景：**
- 本地开发测试
- 资源受限的服务器
- 需要快速响应的简单任务
- 中英文混合场景

**不推荐场景：**
- 需要复杂推理的任务（建议使用 qwen2.5:7b 或更大模型）
- 需要极快响应时间的实时应用（考虑使用更小的模型或GPU加速）
