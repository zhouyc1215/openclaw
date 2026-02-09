# 飞书会话历史问题分析

## 问题现象
清空会话历史后,飞书消息可以正常处理并返回文本回复。
清空前,即使配置了 `tools.deny: ["*"]` 并修改了系统提示,模型仍然生成工具调用JSON。

## 会话历史内容分析

### 1. 早期消息(使用 ollama qwen2.5:1.5b)
```json
{"type":"message","role":"assistant","content":"{"name": "feishu_wiki", "arguments": {"action": "nodes", "title": ""}}"}
{"type":"message","role":"assistant","content":"{"name": "system", "arguments": {"event": "received message from user", "user_id": "835332"}}"}
```

**特征**:
- 模型直接返回工具调用JSON字符串
- 没有使用标准的 `toolCall` 类型
- 这是因为当时工具列表中包含了飞书插件工具

### 2. 切换到 qwen2.5:3b 后
```json
{"type":"message","role":"assistant","content":[],"stopReason":"error","errorMessage":"Cannot read properties of undefined (reading 'includes')"}
```

**特征**:
- 大量错误消息(model.input 未定义的bug)
- 这些错误消息也被记录在会话历史中

### 3. 修复 model.input bug 后
```json
{"type":"message","role":"assistant","content":[{"type":"toolCall","id":"call_sabh8lr2","name":"memory_search","arguments":{"query":"今天几号"}}]}
{"type":"message","role":"assistant","content":[{"type":"toolCall","id":"call_6xy8ddf7","name":"web_search","arguments":{"query":"How to make a chicken salad","count":5}}]}
{"type":"message","role":"assistant","content":[{"type":"toolCall","id":"call_kz1ixhs8","name":"feishu_bitable_get_meta","arguments":{"url":"/wiki/ou_fce4d2a4ccbf3fde"}}]}
```

**特征**:
- 模型开始使用标准的 `toolCall` 格式
- 调用了各种工具:memory_search, web_search, feishu_bitable_get_meta
- 这些工具调用被成功执行,并返回了结果

### 4. 切换到 qwen-plus 后
```json
{"type":"message","role":"user","content":"你好"}
{"type":"message","role":"assistant","content":[],"stopReason":"error","errorMessage":"400 Access denied..."}
```

**特征**:
- 阿里云账户欠费错误
- 但会话历史中已经积累了大量工具调用示例

### 5. 配置 tools.deny: ["*"] 后
```json
{"type":"message","role":"user","content":"你好"}
// 模型仍然生成工具调用JSON
```

**问题**:
- 即使系统提示说"工具已禁用"
- 会话历史中有**30多条工具调用示例**
- 模型从历史中学习到了"应该使用工具调用"的模式

## 根本原因

### 1. 上下文学习(In-Context Learning)
大语言模型会从对话历史中学习模式:
- **历史中有大量工具调用示例** → 模型认为"这是正常的对话模式"
- **系统提示说"工具已禁用"** → 但历史示例的权重更高
- **结果**: 模型继续生成工具调用,忽略系统提示

### 2. 会话历史的影响力
```
会话历史(30+条工具调用) > 系统提示("工具已禁用")
```

会话历史中的示例对模型行为的影响非常大,尤其是:
- **重复模式**: 用户消息 → 工具调用 → 工具结果 → 用户消息 → 工具调用...
- **最近的示例**: 最后几条消息都是工具调用
- **成功的示例**: 工具调用被执行并返回了结果

### 3. 系统提示的局限性
系统提示虽然重要,但在以下情况下会被"覆盖":
- 会话历史中有大量相反的示例
- 历史示例形成了强烈的模式
- 模型倾向于保持对话的连贯性

## 为什么清空历史后就正常了?

### 清空前的上下文
```
系统提示: "工具已禁用,请仅使用文本回复"
会话历史: [30+条工具调用示例]
用户消息: "你好"
模型推理: "历史中都是工具调用,我应该继续这个模式" → 生成工具调用JSON
```

### 清空后的上下文
```
系统提示: "工具已禁用,请仅使用文本回复"
会话历史: []
用户消息: "你好"
模型推理: "系统提示说工具已禁用,没有历史示例,我应该直接回复文本" → 生成文本回复
```

## 技术细节

### 会话历史的结构
```json
{
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "toolCall",
      "id": "call_xxx",
      "name": "tool_name",
      "arguments": {...}
    }
  ]
}
```

这种结构明确告诉模型:
- 助手可以返回工具调用
- 工具调用的格式是什么
- 哪些工具可以使用

### 模型的注意力机制
Transformer模型的注意力机制会:
1. 关注最近的消息(位置编码)
2. 关注重复出现的模式(自注意力)
3. 关注成功的示例(强化学习效应)

会话历史中的30+条工具调用形成了一个**非常强的信号**,远超系统提示的影响。

## 解决方案对比

### 方案1: 修改系统提示(已实施,但不够)
```typescript
toolLines.length > 0
  ? "工具列表..."
  : "工具已禁用,请仅使用文本回复"
```

**效果**: 
- ✅ 对新会话有效
- ❌ 对有历史的会话无效(历史示例权重更高)

### 方案2: 清空会话历史(已实施,完全有效)
```bash
mv session.jsonl session.jsonl.backup
```

**效果**:
- ✅ 立即生效
- ✅ 模型只看到系统提示,没有相反的示例
- ❌ 丢失了对话上下文

### 方案3: 过滤会话历史(理想方案)
在加载会话历史时,过滤掉所有工具调用相关的消息:
```typescript
const filteredHistory = history.filter(msg => 
  msg.type !== 'toolCall' && 
  msg.type !== 'toolResult'
);
```

**效果**:
- ✅ 保留对话上下文
- ✅ 移除工具调用示例
- ✅ 模型不会学习到工具调用模式

## 教训总结

### 1. 会话历史的重要性
- 会话历史对模型行为的影响**远大于**系统提示
- 修改配置时,需要考虑现有会话的历史

### 2. 配置变更的影响范围
- 系统提示变更: 只影响新的推理
- 工具列表变更: 只影响新的工具调用
- 会话历史: 持续影响所有后续推理

### 3. 最佳实践
当进行重大配置变更时(如禁用工具):
1. **清空会话历史** 或 **过滤历史中的相关内容**
2. **通知用户** 配置已变更,可能需要重新开始对话
3. **提供命令** 让用户可以手动清空会话(如 `/reset`)

### 4. 代码改进建议
在 `tools.deny` 配置变更时,自动清理会话历史中的工具调用:
```typescript
if (toolsDisabled && sessionHasToolCalls) {
  // 选项1: 清空整个会话
  sessionManager.reset();
  
  // 选项2: 过滤掉工具调用
  sessionManager.filterMessages(msg => 
    msg.type !== 'toolCall' && msg.type !== 'toolResult'
  );
  
  // 选项3: 添加系统消息说明配置已变更
  sessionManager.addSystemMessage(
    "配置已更新:工具已被禁用,后续对话将仅使用文本回复。"
  );
}
```

## 时间线

- **13:26** - 首次使用,模型返回工具调用JSON(ollama qwen2.5:1.5b)
- **13:42** - 切换到 qwen2.5:3b,遇到 model.input bug
- **14:21** - 修复bug后,模型开始正常使用工具调用
- **19:22** - 切换到 qwen-plus,遇到账户欠费
- **19:29** - 充值后,配置 tools.deny: ["*"]
- **19:53** - 修改系统提示,但模型仍生成工具调用(历史影响)
- **19:57** - 清空会话历史,问题解决 ✅

## 结论

**问题的根本原因不是代码bug,而是会话历史的累积效应**:
- 30+条工具调用示例形成了强烈的模式
- 模型从历史中学习到"应该使用工具调用"
- 系统提示的权重不足以对抗历史示例

**解决方案**:
- 短期: 清空会话历史(已完成)
- 长期: 在配置变更时自动清理或过滤会话历史

这是一个典型的**上下文学习(In-Context Learning)问题**,也是大语言模型的一个重要特性:模型会从对话历史中学习并模仿模式,即使这个模式与当前的系统提示相矛盾。
