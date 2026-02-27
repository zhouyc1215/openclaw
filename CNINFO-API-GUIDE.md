# 巨潮网 API 使用指南

## API 信息

- **接口名称**: p_public0001
- **URL**: http://webapi.cninfo.com.cn/api/stock/p_public0001
- **请求方式**: GET, POST
- **最大记录数**: 20000

## 当前状态

⚠️ API 需要授权 Token

- 测试结果：`{"resultmsg":"未经授权的访问,code_005_ipban_notoken false true","resultcode":401}`
- 需要先获取巨潮网 API Token 才能使用

## 获取 Token

### 正确的请求头格式

巨潮网使用 `cninfo-token` 请求头（不是 Bearer Token）：

```bash
curl 'http://www.cninfo.com.cn/new/hisAnnouncement/query' \
  -H 'cninfo-token: YOUR_TOKEN_HERE'
```

### 方法 1: 巨潮资讯官网注册

1. 访问巨潮资讯网：http://www.cninfo.com.cn/
2. 注册账号并登录
3. 打开浏览器开发者工具（F12）
4. 访问任意公告页面
5. 在 Network 标签中查看请求头，找到 `cninfo-token`
6. 复制 token 值

### 方法 2: 申请开发者权限

- 客服电话：0755-83521430
- 邮箱：service@cninfo.com.cn
- 说明用途并申请 API 访问权限

### 方法 3: 使用浏览器 Cookie

登录巨潮网后，token 会保存在浏览器中，可以从开发者工具中提取。

## 配置 Token

获取到 Token 后，设置环境变量：

```bash
# 添加到 ~/.bashrc
echo 'export CNINFO_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

## 使用脚本

已创建脚本：`/home/tsl/clawd/get_cninfo_report.sh`

### 基本用法

```bash
# 查询股票数据（默认）
/home/tsl/clawd/get_cninfo_report.sh 000001

# 查询公告信息
/home/tsl/clawd/get_cninfo_report.sh 600519 announcement
```

### 完整示例

```bash
# 1. 设置 Token
export CNINFO_TOKEN="your_actual_token_here"

# 2. 查询平安银行股票数据
/home/tsl/clawd/get_cninfo_report.sh 000001 stock

# 3. 查询贵州茅台公告
/home/tsl/clawd/get_cninfo_report.sh 600519 announcement
```

## 重要说明

### 巨潮网数据范围

巨潮网主要提供**中国A股上市公司**的信息，包括：

- 深圳证券交易所上市公司
- 上海证券交易所上市公司
- 北京证券交易所上市公司

### 查询美股财报（如英伟达 NVDA）

巨潮网**不包含美股数据**。查询美股财报建议使用：

#### 1. SEC EDGAR API（免费，官方数据）

```bash
# 英伟达 CIK: 0001045810
curl "https://data.sec.gov/submissions/CIK0001045810.json" \
  -H "User-Agent: YourName your@email.com"
```

#### 2. Alpha Vantage API（有免费额度）

```bash
# 获取免费 API Key: https://www.alphavantage.co/support/#api-key
curl "https://www.alphavantage.co/query?function=EARNINGS&symbol=NVDA&apikey=YOUR_KEY"
```

#### 3. Yahoo Finance（非官方，可能不稳定）

```bash
curl "https://query1.finance.yahoo.com/v10/finance/quoteSummary/NVDA?modules=earnings"
```

#### 4. OpenRouter 搜索工具（推荐，已配置）

Agent 现在可以使用搜索工具获取最新财报信息：

- 搜索提供商：Perplexity（通过 OpenRouter）
- 已配置 API Key
- 可以搜索实时财报新闻和数据

在飞书中直接问：

- "搜索英伟达最新财报"
- "查询 NVDA Q4 2025 财报"
- "英伟达最新季度营收"

## 常见 A股公司代码

| 公司名称 | 股票代码 | 交易所 |
| -------- | -------- | ------ |
| 平安银行 | 000001   | 深交所 |
| 万科A    | 000002   | 深交所 |
| 贵州茅台 | 600519   | 上交所 |
| 中国平安 | 601318   | 上交所 |
| 工商银行 | 601398   | 上交所 |
| 比亚迪   | 002594   | 深交所 |
| 宁德时代 | 300750   | 深交所 |

## API 参数说明

### 请求参数

```json
{
  "scode": "股票代码",
  "sdate": "开始日期 YYYY-MM-DD",
  "edate": "结束日期 YYYY-MM-DD"
}
```

### 响应格式

```json
{
  "resultcode": 200,
  "resultmsg": "成功",
  "records": [
    {
      "SECCODE": "股票代码",
      "SECNAME": "股票名称",
      "REPORTDATE": "报告日期",
      "REVENUE": "营业收入",
      "NETPROFIT": "净利润",
      ...
    }
  ]
}
```

## 为 Agent 添加财报查询能力

### 方案 1: 配置巨潮网 Token（查询 A股）

1. 获取 Token
2. 设置环境变量
3. Agent 可以使用 `~/clawd/get_cninfo_report.sh` 脚本

### 方案 2: 使用搜索工具（推荐，查询全球股票）

已配置完成，Agent 可以直接搜索任何公司的财报信息。

### 方案 3: 配置其他财报 API

可以添加更多数据源：

- Tushare（需要积分）
- 东方财富 API
- 同花顺 API
- Wind API（付费）

## 测试

```bash
# 测试巨潮网 API（需要 Token）
~/clawd/get_cninfo_report.sh 600519

# 测试搜索工具（已配置，无需额外设置）
# 在飞书中问："搜索贵州茅台最新财报"
```

## 故障排查

### 401 未授权错误

- 检查 Token 是否正确
- 确认 Token 未过期
- 验证 IP 是否在白名单中

### 连接超时

- 检查网络连接
- 确认 VPN 状态（如需要）
- 尝试使用代理

### 数据为空

- 确认股票代码正确
- 检查日期范围
- 验证公司是否已披露财报
