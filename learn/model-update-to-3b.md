# Clawdbot 模型更新记录

## 更新时间
2026-02-08 21:41

## 更新内容

### 模型变更
- **旧模型**: ollama/qwen2.5:1.5b (1.5B 参数)
- **新模型**: ollama/qwen2.5:3b (3B 参数)

### 配置变更
```bash
# 更新主模型
agents.defaults.model.primary: "ollama/qwen2.5:1.5b" → "ollama/qwen2.5:3b"

# 增加超时时间
agents.defaults.timeoutSeconds: 120 → 300
```

---

## 更新原因

### 问题
使用 1.5B 模型时，飞书收到的回复都是工具调用的原始格式：
```
{"name": "system", "arguments": {}}
</tool_call>
```

### 根本原因
qwen2.5:1.5b 模型太小，无法正确理解和执行工具调用。模型只是输出工具调用的格式，而不是真正执行工具。

### 解决方案
升级到 qwen2.5:3b（3B 参数），提供更好的工具调用支持。

---

## 验证结果

### 配置验证
```bash
$ pnpm clawdbot config get agents.defaults.model
{
  "primary": "ollama/qwen2.5:3b"
}
```

### 运行状态
```bash
$ pnpm clawdbot channels status
Gateway reachable.
- Feishu default: enabled, configured, running
```

### 会话状态
```
Sessions: 1 active · default qwen2.5:3b (33k ctx)
Model: qwen2.5:3b
Tokens: 4.1k/33k (13%)
```

✅ **模型已成功更新并运行**

---

## 模型对比

| 特性 | qwen2.5:1.5b | qwen2.5:3b |
|------|--------------|------------|
| 参数量 | 1.5B | 3B |
| 模型大小 | 986MB | ~2GB |
| 工具调用 | ❌ 不支持 | ⚠️ 部分支持 |
| 响应时间 | ~80秒 | ~120秒 |
| 上下文窗口 | 32K | 32K |
| 推荐度 | ⭐ | ⭐⭐⭐ |

---

## 预期改进

### 1. 工具调用
- **之前**: 输出工具调用的原始 JSON 格式
- **现在**: 应该能正确执行工具调用（需要测试验证）

### 2. 响应质量
- **之前**: 简单对话可以，复杂任务失败
- **现在**: 更好的理解能力，支持更复杂的任务

### 3. 响应时间
- **之前**: ~80秒
- **现在**: ~120秒（增加约 50%）

---

## 测试建议

### 测试1: 简单对话
在飞书中发送：
```
你好
```

**预期**: 正常的文本回复

### 测试2: 工具调用
在飞书中发送：
```
帮我列出知识库空间
```

**预期**: 
- 调用 `feishu_wiki` 工具
- 返回知识库列表
- 而不是返回 JSON 格式

### 测试3: 复杂任务
在飞书中发送：
```
帮我搜索包含"项目"的文档
```

**预期**: 
- 调用 `feishu_doc` 工具
- 返回搜索结果

---

## 注意事项

### 1. 响应时间
3B 模型比 1.5B 慢约 50%，需要耐心等待。

### 2. 工具调用能力
3B 模型的工具调用能力可能不如 7B 模型稳定，如果仍然出现问题，建议升级到 7B。

### 3. 超时设置
已将超时时间从 120秒 增加到 300秒，给模型更多时间处理。

### 4. 安全警告
系统仍然会显示"小模型需要沙箱"的警告，这是正常的。如果需要更高安全性，可以：
```bash
pnpm clawdbot config set agents.defaults.sandbox.mode "all"
```

---

## 如果仍有问题

### 选项1: 升级到 7B（推荐）
```bash
ollama pull qwen2.5:7b
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:7b"
pnpm clawdbot config set agents.defaults.timeoutSeconds 600
pnpm clawdbot gateway restart
```

### 选项2: 禁用工具
```bash
pnpm clawdbot config set tools.deny '["feishu_doc","feishu_wiki","feishu_drive","feishu_bitable"]'
pnpm clawdbot gateway restart
```

### 选项3: 使用云端模型
需要 API Key，但效果最好：
```bash
export OPENAI_API_KEY="your_key"
pnpm clawdbot config set agents.defaults.model.primary "openai/gpt-4"
pnpm clawdbot gateway restart
```

---

## 回滚方法

如果需要回退到 1.5B：
```bash
pnpm clawdbot config set agents.defaults.model.primary "ollama/qwen2.5:1.5b"
pnpm clawdbot config set agents.defaults.timeoutSeconds 120
pnpm clawdbot gateway restart
```

---

## 监控命令

### 查看实时日志
```bash
tail -f /tmp/clawdbot/clawdbot-2026-02-08.log
```

### 查看模型使用情况
```bash
pnpm clawdbot status
```

### 查看频道状态
```bash
pnpm clawdbot channels status
```

---

## 总结

✅ **模型已成功从 1.5B 升级到 3B**
✅ **超时时间已增加到 300秒**
✅ **Gateway 已重启并运行正常**
✅ **飞书连接正常**

**下一步**: 在飞书中测试，验证工具调用是否正常工作。

如果 3B 模型仍然无法正确处理工具调用，建议升级到 7B 模型。
