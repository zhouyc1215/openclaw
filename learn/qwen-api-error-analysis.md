# 通义千问 API 错误分析

## 错误信息
```
HTTP 400: Access denied, please make sure your account is in good standing. 
For details, see: https://help.aliyun.com/zh/model-studio/error-code#overdue-payment
```

## 错误原因分析

### 1. **账户欠费（最可能）**
- 错误码指向 `overdue-payment`（欠费）
- 阿里云账户余额不足或已欠费
- API 调用被阻止，直到充值

### 2. **账户状态异常**
- 账户被冻结或限制
- 实名认证未完成
- 违反服务条款

### 3. **API Key 权限问题**
- API Key 已过期
- API Key 被禁用
- API Key 没有调用该模型的权限

### 4. **服务未开通**
- 通义千问服务未正式开通
- 免费额度已用完，未开通付费服务

## 从日志看到的执行流程

```
11:22:41 - 飞书收到消息
11:22:42 - Agent 开始处理（qwen-portal/qwen-plus）
11:22:42 - Agent 执行完成（耗时 426ms）
11:22:42 - 返回错误：HTTP 400 Access denied
11:22:43 - 错误消息发送到飞书
```

**关键发现**：
- Agent 启动和执行都很快（426ms）
- 错误发生在调用通义千问 API 时
- 不是超时问题，而是认证/授权问题

## 解决方案

### 方案 1：检查账户余额（推荐）
1. 登录阿里云控制台：https://home.console.aliyun.com/
2. 查看账户余额
3. 如果欠费，充值后重试

### 方案 2：检查服务状态
1. 访问模型服务控制台：https://bailian.console.aliyun.com/
2. 检查通义千问服务是否已开通
3. 查看 API Key 状态和权限

### 方案 3：检查 API Key
1. 确认 API Key 是否正确
2. 检查 API Key 是否有调用权限
3. 如果需要，重新生成 API Key

### 方案 4：使用免费模型（临时方案）
如果账户问题无法立即解决，可以：
1. 使用阿里云免费额度的模型
2. 或者切换回本地 Ollama 模型（虽然慢但免费）

## 临时切换回 Ollama 的命令

如果需要立即恢复服务，可以切换回本地模型：

```bash
# 1. 备份当前配置
cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.qwen-backup

# 2. 恢复 Ollama 配置
cp ~/.clawdbot/clawdbot.json.backup ~/.clawdbot/clawdbot.json

# 3. 重启服务
systemctl --user restart clawdbot-gateway.service
```

## 验证 API Key 的方法

可以使用 curl 直接测试 API Key：

```bash
curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer sk-3effff40719b46259d25ae1b16dfdaea" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

如果返回相同的 400 错误，说明是账户问题，不是 Clawdbot 配置问题。

## 建议

**立即行动**：
1. 检查阿里云账户余额
2. 如果欠费，充值后问题即可解决
3. 如果不是欠费，联系阿里云客服查看账户状态

**长期建议**：
- 设置账户余额预警
- 开启自动充值功能
- 定期检查 API 使用量和费用
