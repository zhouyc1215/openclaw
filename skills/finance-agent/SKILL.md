---
name: finance-agent
description: "Query financial data, stock reports, and announcements via claw-finance-agent API. Use for stock analysis, financial metrics, and annual report queries."
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires":
          {
            "api": "http://localhost:9000",
            "endpoints": ["/query", "/metrics", "/analysis", "/ask", "/announcements"],
          },
      },
  }
---

# Finance Agent Skill

> **默认工具**：所有上市公司财报（一季报、半年报、年报、季报）查询，默认使用 `claw-finance-agent` API。
>
> 仅在 claw-finance-agent 不可用时，fallback 到 tushare 或手动上传PDF。

## 工作流程

```
用户询问财报 → finance_ask（/ask端点）→ RAG检索 → 若无命中则自动爬取巨潮PDF → LLM分析 → 返回完整报告
```

**工具选择规则：**

- **财报分析请求** → 优先 `finance_ask`（自动走claw-finance-agent，支持巨潮PDF回退）
- **行情/交易数据** → 用 tushare skill
- **本地PDF文件** → 直接读取分析

---

## 工具一：finance_ask（首选，用于财报问答）

当用户提到以下关键词时，优先使用此工具：

- "财报"、"财务报告"、"季报"、"半年报"、"年报"
- "分析" + 股票名称/代码
- "营收"、"净利润"、"毛利率"、"费用"

```python
# 内部调用
finance_ask(question="英维克 2026年一季度财报 营收净利润毛利率费用分析", top_k=10)
```

**功能：**

1. RAG 向量库检索匹配片段
2. 若无命中 → 自动从巨潮资讯网下载对应PDF并切片
3. LLM 生成完整分析

---

## 工具二：直接调API（结构化数据）

### 查询个股公告（获取披露时间线）

```bash
curl -s -X POST http://localhost:9000/announcements \
  -H "Content-Type: application/json" \
  -d '{"code": "002837"}'
```

### 查询语义搜索（年报/研报内容）

```bash
curl -s -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "英维克 毛利率 费用 净利润", "top_k": 5}'
```

### 获取财务指标结构化数据

```bash
curl -s -X POST http://localhost:9000/metrics \
  -H "Content-Type: application/json" \
  -d '{"code": "002837"}'
```

---

## 标准财报分析流程（以英维克2026年Q1为例）

```
1. finance_ask(question="英维克 002837 2026年一季度财报 营收 净利润 毛利率 费用 同比环比", top_k=10)
   ↓
2. claw-finance-agent 检索知识库
   ↓ 无命中
3. 自动爬取巨潮 PDF → /data/reports/002837/002837__2026年一季度报告.pdf
   ↓
4. 切片 + RAG + LLM 分析
   ↓
5. 返回完整财报分析
```

---

## API 端点速查

| 端点             | 方法 | 用途                  |
| ---------------- | ---- | --------------------- |
| `/ask`           | POST | 财报 RAG 问答（首选） |
| `/query`         | POST | 语义搜索年报/研报     |
| `/announcements` | POST | 公司披露公告列表      |
| `/metrics`       | POST | 财务指标结构化数据    |
| `/analysis`      | GET  | AI 生成投资分析报告   |

**API 地址**：`http://localhost:9000`

---

## 典型问法示例

| 用户问法                   | 使用工具    | 问题构造                                            |
| -------------------------- | ----------- | --------------------------------------------------- |
| "英维克一季度财报分析一下" | finance_ask | 英维克 002837 2026年一季度财报 营收净利润毛利率费用 |
| "帮我查一下万科最新年报"   | finance_ask | 万科A 000002 最新年报 营收净利润毛利率              |
| "获取平安银行季报数据"     | finance_ask | 平安银行 000001 最新季度报告 财务数据               |
| "这家公司财务指标怎么样"   | metrics     | code: 股票代码                                      |

---

## 注意事项

- `finance_ask` 是内置 tool，调用方式为 `finance_ask(question="...", top_k=N)`
- 不需要 exec curl，直接调用 tool 即可
- claw-finance-agent 支持自动回退：若知识库无数据，会自动从巨潮下载PDF
- 使用股票代码（如 `002837`）而非名称，可提升检索精度
