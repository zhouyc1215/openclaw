# Web 搜索工具配置完成

## 配置状态

✅ 搜索工具已启用：`tools.web.search.enabled = true`
✅ Web 抓取已启用：`tools.web.fetch.enabled = true`
✅ 搜索提供商：`perplexity`（通过 OpenRouter）
✅ API Key 已配置
✅ Gateway 正常运行（端口 18789）
✅ Feishu 通道正常

## 当前配置

```json
{
  "tools": {
    "allow": ["exec", "read", "write", "search", "fetch"]
  },
  "tools.web.search": {
    "enabled": true,
    "provider": "perplexity",
    "perplexity": {
      "apiKey": "sk-or-v1-***",
      "baseUrl": "https://openrouter.ai/api/v1"
    }
  },
  "tools.web.fetch": {
    "enabled": true
  }
}
```

## Agent 新增能力

现在 Agent 可以：

1. **实时搜索信息**
   - 搜索最新新闻、财报、股票信息
   - 查询技术文档和教程
   - 获取实时数据和统计信息

2. **抓取网页内容**
   - 读取网页文本内容
   - 提取特定信息
   - 分析网页数据

## 使用示例

在飞书中可以直接问：

- "搜索英伟达最新财报"
- "查询今天的科技新闻"
- "获取比特币当前价格"
- "搜索 Python 3.12 新特性"
- "查找 React 19 发布信息"

Agent 会自动使用搜索工具获取最新信息并回复。

## 解决的问题

之前遇到的问题：

- ❌ Agent 尝试用 curl 访问外部 API，被 Cloudflare 拦截
- ❌ Agent 陷入循环，不断尝试不同的失败方法
- ❌ 飞书响应慢，每 6 秒发送"正在输入"提示

现在：

- ✅ Agent 使用专业的搜索 API（OpenRouter/Perplexity）
- ✅ 可以快速获取实时信息
- ✅ 避免无效的 curl 尝试和循环

## 技术细节

- **搜索提供商**: Perplexity（通过 OpenRouter）
- **API 端点**: https://openrouter.ai/api/v1
- **模型**: perplexity/sonar-pro（默认）
- **免费额度**: OpenRouter 提供免费额度用于测试

## 下一步优化建议

1. **监控 API 使用量**
   - 查看 OpenRouter Dashboard 了解使用情况
   - 根据需要升级套餐

2. **调整搜索参数**

   ```bash
   # 设置最大结果数（1-10）
   pnpm openclaw config set tools.web.search.maxResults 5

   # 设置超时时间（秒）
   pnpm openclaw config set tools.web.search.timeoutSeconds 30

   # 设置缓存时间（分钟）
   pnpm openclaw config set tools.web.search.cacheTtlMinutes 60
   ```

3. **添加中文回复指令**
   - 已配置 Agent 默认使用中文回复
   - 新 session 会自动使用中文

## 故障排查

如果搜索不工作：

1. 检查 API Key 是否有效
2. 查看 Gateway 日志：`tail -f /tmp/openclaw-gateway.log`
3. 验证配置：`pnpm openclaw config get tools.web.search`
4. 重启 Gateway：`pnpm openclaw gateway stop && nohup pnpm openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &`

## 相关文档

- OpenRouter 文档: https://openrouter.ai/docs
- Perplexity API: https://docs.perplexity.ai/
- OpenClaw 配置: https://docs.openclaw.ai/cli/config
