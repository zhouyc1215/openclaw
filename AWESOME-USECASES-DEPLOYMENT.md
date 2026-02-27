# awesome-openclaw-usecases 部署方案

## 当前配置概览

你的 clawdbot 已配置：

- 飞书集成（Feishu）
- 4 个定时任务（天气预报、AI 项目、自动提交、备份）
- 多个 AI 模型提供商（Qwen、MiniMax、Ollama）
- Gateway 运行在局域网模式（10.71.1.116:18789）

## 推荐部署的用例

### 1. 每日科技新闻摘要（Multi-Source Tech News Digest）

**适合原因**：

- 与你现有的"每日 AI 项目"任务互补
- 自动聚合 109+ 个来源（RSS、Twitter、GitHub、搜索）
- 支持质量评分和去重

**部署步骤**：

```bash
# 1. 安装 tech-news-digest skill
openclaw skills install tech-news-digest

# 2. 配置环境变量（可选，提升功能）
# 在 ~/.openclaw/openclaw.json 的 env 部分添加：
# "X_BEARER_TOKEN": "your_twitter_token"
# "BRAVE_API_KEY": "your_brave_api_key"
# "GITHUB_TOKEN": "your_github_token"
```

**定时任务配置**：

```json
{
  "id": "tech-news-digest",
  "agentId": "main",
  "name": "tech_news_digest",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "生成过去 24 小时的科技新闻摘要，包括 AI、开源项目和前沿技术。按质量评分排序，去除重复内容。格式化为清晰的列表，每条新闻包含标题、来源和链接。",
    "timeoutSeconds": 180
  },
  "delivery": {
    "mode": "announce",
    "channel": "feishu",
    "to": "ou_b3afb7d2133e4d689be523fc48f3d2b3",
    "bestEffort": true
  }
}
```

---

### 2. Reddit 每日摘要（Daily Reddit Digest）

**适合原因**：

- 简单易用，无需认证
- 可以关注技术、AI、编程相关 subreddit
- 支持偏好学习和记忆

**部署步骤**：

```bash
# 安装 reddit-readonly skill
openclaw skills install reddit-readonly
```

**Prompt 配置**：
通过飞书发送给 clawdbot：

```
我想让你每天下午 6 点给我推送以下 subreddit 的热门帖子摘要：
- r/MachineLearning
- r/LocalLLaMA
- r/OpenAI
- r/programming
- r/golang

为 reddit 流程创建一个单独的记忆文件，记录我喜欢的帖子类型。每天询问我是否喜欢推送的内容，并将我的偏好保存为规则，用于更好的内容筛选（例如：不包含 meme）。

每天 18:00 运行此流程并发送摘要到飞书。
```

---

### 3. 自定义晨报（Custom Morning Brief）

**适合原因**：

- 整合多个信息源（新闻、任务、建议）
- 充分利用夜间空闲时间
- 可以与你现有的天气预报任务配合

**部署步骤**：
通过飞书发送给 clawdbot：

```
设置每日晨报，每天早上 7:30 发送到飞书。

晨报内容包括：
1. 西安今日天气（从现有天气任务获取）
2. AI 和科技领域的重要新闻（3-5 条）
3. 今日推荐的 AI 项目或工具
4. 你认为今天可以帮我完成的任务建议

新闻部分要有深度，不只是标题，包含关键信息摘要。
项目推荐要有实用价值，说明为什么推荐。
```

---

### 4. 个人知识库（Knowledge Base RAG）

**适合原因**：

- 可以保存和检索你收藏的技术文章、文档
- 支持语义搜索
- 与其他工作流集成

**部署步骤**：

```bash
# 安装 knowledge-base skill（如果 ClawHub 有的话）
openclaw skills install knowledge-base
```

**配置方式**：
通过飞书发送给 clawdbot：

```
设置知识库功能：

当我在飞书发送 URL 链接时：
1. 自动抓取内容（文章、推文、YouTube 字幕、PDF）
2. 将内容存入知识库，包含元数据（标题、URL、日期、类型）
3. 回复确认：已存入什么内容和分块数量

当我提问时（例如"我保存了哪些关于 LLM 的内容？"）：
1. 在知识库中进行语义搜索
2. 返回最相关的结果，包含来源和相关摘录
3. 如果没有匹配结果，告诉我

知识库存储在 ~/.openclaw/knowledge-base/ 目录。
```

---

### 5. AI 财报追踪（Earnings Tracker）

**适合原因**：

- 自动追踪科技公司财报
- 动态创建一次性定时任务
- 适合关注 AI 行业动态

**部署步骤**：
通过飞书发送给 clawdbot：

```
设置财报追踪功能：

每周日晚上 8 点运行定时任务：
1. 搜索下周的科技公司财报日程
2. 筛选我关注的公司（NVDA、MSFT、GOOGL、META、AMZN、TSLA、AMD、AAPL）
3. 发送列表到飞书
4. 等待我确认要追踪哪些公司

当我回复确认后：
1. 为每个财报日期创建一次性定时任务
2. 财报发布后，搜索财报结果
3. 格式化摘要：业绩表现、营收、EPS、关键指标、AI 相关亮点、指引
4. 发送到飞书

记住我通常追踪的公司，每周自动建议。
```

---

## 快速部署脚本

我将为你创建一个自动化部署脚本，可以一键添加这些用例。

## 注意事项

1. **Skill 安装**：某些用例需要从 ClawHub 安装 skill，确保网络连接正常
2. **API 密钥**：部分功能需要额外的 API 密钥（Twitter、Brave Search 等）
3. **超时设置**：根据任务复杂度调整 `timeoutSeconds`（建议 120-240 秒）
4. **测试验证**：每个新任务部署后先手动触发测试
5. **内存管理**：知识库和记忆文件会占用存储空间，定期清理

## 下一步

选择你想部署的用例，我可以：

1. 生成完整的 cron 任务配置
2. 创建自动化部署脚本
3. 提供详细的测试步骤
4. 帮助配置所需的 API 密钥
