# 飞书下载命令问题分析

## 问题现象
- 用户在飞书发送下载命令
- Clawdbot 返回"下载成功"的消息
- 但实际上找不到下载的文件

## 根本原因

### 1. 工具被全局禁用
```bash
$ pnpm clawdbot config get tools.deny
["*"]
```

**`tools.deny: ["*"]` 表示所有工具都被禁用！**

### 2. Agent 行为分析
从日志可以看到：

```
[system-prompt] 33 tools available: [ 'read', 'edit', 'write', 'exec', 'process' ]
```

虽然系统提示显示有 33 个工具可用，但由于 `tools.deny: ["*"]`，这些工具实际上都被过滤掉了。

### 3. 日志证据
查看日志发现：
- ✅ Agent 收到了下载指令
- ✅ Agent 生成了"正在下载"的文本回复
- ❌ **没有任何工具调用记录**（没有 exec、write、curl、wget 等）
- ❌ **没有文件写入操作**

Agent 只是**模拟**了下载过程，生成了看起来像是在执行的文本，但实际上**没有调用任何工具**。

## 为什么会这样？

### 上下文学习问题
即使工具被禁用，模型仍然可能：
1. 从训练数据中学习到"下载"的概念
2. 生成看起来像是在执行命令的文本
3. 返回"成功"的消息

但由于工具被禁用，这些都只是**文本生成**，不是真正的**工具调用**。

## 解决方案

### 方案 1: 启用所有工具（推荐）
```bash
pnpm clawdbot config set tools.deny '[]'
pnpm clawdbot gateway restart
```

### 方案 2: 只启用必要的工具
```bash
# 启用下载相关的工具
pnpm clawdbot config set tools.deny '["feishu_*"]'
pnpm clawdbot gateway restart
```

这样会禁用飞书插件工具，但保留核心工具（exec、write 等）。

### 方案 3: 使用工具白名单
```bash
# 只允许特定工具
pnpm clawdbot config set tools.allow '["exec", "write", "read"]'
pnpm clawdbot config set tools.deny '[]'
pnpm clawdbot gateway restart
```

## 验证修复

### 1. 检查工具配置
```bash
pnpm clawdbot config get tools.deny
pnpm clawdbot config get tools.allow
```

### 2. 查看系统提示
```bash
tail -f /tmp/clawdbot/clawdbot-2026-02-09.log | grep "system-prompt"
```

应该看到工具列表不为空。

### 3. 测试下载命令
在飞书发送简单的测试命令：
```
请执行命令：echo "test" > /tmp/test.txt
```

然后检查文件是否存在：
```bash
cat /tmp/test.txt
```

### 4. 查看工具调用日志
```bash
tail -f /tmp/clawdbot/clawdbot-2026-02-09.log | grep -E "(tool|exec|write)"
```

应该能看到工具调用的记录。

## 相关配置

### 当前配置
- `tools.deny: ["*"]` - 禁用所有工具
- 系统提示显示 33 个工具，但都被过滤
- Agent 只能生成文本，无法执行命令

### 推荐配置
- `tools.deny: []` - 不禁用任何工具
- 或 `tools.deny: ["feishu_*"]` - 只禁用飞书插件工具
- 保留核心工具（exec、write、read 等）

## 注意事项

1. **会话历史清理**：修改 `tools.deny` 后，会话历史会被自动清理（我们实现的功能）
2. **配置热重载**：修改配置后会自动生效，无需手动重启（除非修改了其他需要重启的配置）
3. **安全考虑**：如果担心安全问题，可以使用沙箱模式或工具白名单

## 时间线
- **03:21:50** - Agent 收到下载指令
- **03:21:56** - Agent 返回"正在下载"的文本
- **03:21:56** - Agent 运行结束，无工具调用
- **问题**: `tools.deny: ["*"]` 导致所有工具被禁用

## 结论
问题的根本原因是 `tools.deny: ["*"]` 配置导致所有工具被禁用。Agent 只能生成文本回复，无法真正执行下载命令。解决方法是修改配置，启用必要的工具。
