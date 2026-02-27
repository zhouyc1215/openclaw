# Brave Search API 配置指南

## 已完成的配置

已在 `~/.openclaw/openclaw.json` 中添加了以下配置：

```json
{
  "search": {
    "provider": "brave",
    "brave": {
      "apiKey": "YOUR_BRAVE_API_KEY_HERE"
    }
  },
  "tools": {
    "allow": ["exec", "read", "write", "search", "fetch"]
  }
}
```

## 获取 Brave Search API Key

### 方法 1: Brave Search API（推荐）

1. 访问 Brave Search API 官网：https://brave.com/search/api/
2. 点击 "Get Started" 或 "Sign Up"
3. 注册账号并登录
4. 在 Dashboard 中创建新的 API Key
5. 复制 API Key

### 方法 2: 使用其他搜索 API

如果不想使用 Brave，也可以配置其他搜索服务：

#### Tavily Search API

```json
{
  "search": {
    "provider": "tavily",
    "tavily": {
      "apiKey": "YOUR_TAVILY_API_KEY"
    }
  }
}
```

获取地址：https://tavily.com/

#### SerpAPI

```json
{
  "search": {
    "provider": "serpapi",
    "serpapi": {
      "apiKey": "YOUR_SERPAPI_KEY"
    }
  }
}
```

获取地址：https://serpapi.com/

#### DuckDuckGo（免费，无需 API Key）

```json
{
  "search": {
    "provider": "duckduckgo"
  }
}
```

## 配置 API Key

获取到 API Key 后，运行以下命令：

```bash
# 方法 1: 使用 jq 命令
jq '.search.brave.apiKey = "YOUR_ACTUAL_API_KEY"' ~/.openclaw/openclaw.json > /tmp/openclaw-temp.json && mv /tmp/openclaw-temp.json ~/.openclaw/openclaw.json

# 方法 2: 使用环境变量
export BRAVE_SEARCH_API_KEY="YOUR_ACTUAL_API_KEY"
```

## 重启 Gateway

配置完成后重启 Gateway：

```bash
pnpm openclaw gateway stop
nohup pnpm openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &
```

## 测试搜索功能

配置完成后，Agent 将能够：

- 搜索实时信息（新闻、股票、财报等）
- 获取网页内容
- 回答需要最新数据的问题

示例：

- "搜索英伟达最新财报"
- "查询今天的科技新闻"
- "获取比特币当前价格"

## 当前配置状态

✅ 搜索工具已启用：`tools.web.search.enabled = true`
✅ Web 抓取已启用：`tools.web.fetch.enabled = true`
✅ 搜索提供商：`perplexity`（通过 OpenRouter）
✅ tools.allow 已包含 "search" 和 "fetch"
⏳ 需要配置 OpenRouter API Key
⏳ 需要重启 Gateway 使配置生效

## 推荐方案：使用 OpenRouter（免费额度）

OpenRouter 提供免费额度，支持 Perplexity 搜索模型。

### 获取 OpenRouter API Key

1. 访问：https://openrouter.ai/
2. 注册并登录
3. 进入 Keys 页面：https://openrouter.ai/keys
4. 创建新的 API Key
5. 复制 API Key

### 配置 API Key

方法 1：使用环境变量（推荐）

```bash
echo 'export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"' >> ~/.bashrc
source ~/.bashrc
```

方法 2：直接配置到文件

```bash
pnpm openclaw config set tools.web.search.perplexity.apiKey "sk-or-v1-YOUR_KEY_HERE"
```

### 重启 Gateway

```bash
pnpm openclaw gateway stop
nohup pnpm openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &
```

## 其他可选方案

### Brave Search API

需要申请 API Key：https://brave.com/search/api/

```bash
pnpm openclaw config set tools.web.search.provider brave
export BRAVE_API_KEY="YOUR_BRAVE_KEY"
```

### Perplexity 直连

如果有 Perplexity API Key：

```bash
pnpm openclaw config set tools.web.search.perplexity.baseUrl "https://api.perplexity.ai"
export PERPLEXITY_API_KEY="YOUR_PERPLEXITY_KEY"
```
