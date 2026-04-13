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

Query financial data, stock reports, and analysis via the claw-finance-agent API running at http://localhost:9000.

When the OpenClaw Gateway has the **`claw-finance`** plugin enabled, prefer the **`finance_ask`** tool for `/ask` (RAG + disclosure + crawl fallback + LLM) instead of shell `curl` from the agent, so timeouts and JSON fields stay consistent.

## Query Stock Reports (RAG)

Search for stock reports using semantic search:

```bash
curl -s -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "股票代码 财务指标", "top_k": 5}'
```

## Get Company Announcements

Get all announcements for a company (annual reports, interim reports, quarterly reports, etc.):

```bash
curl -s -X POST http://localhost:9000/announcements \
  -H "Content-Type: application/json" \
  -d '{"code": "002202"}'
```

Parameters:

- `code`: Stock code (e.g., "002202", "600000")
- `year`: Filter by year (optional)
- `announcement_type`: Filter by type (optional)

## Get Financial Metrics

Get financial metrics for a specific stock:

```bash
curl -s -X POST http://localhost:9000/metrics \
  -H "Content-Type: application/json" \
  -d '{"code": "000858"}'
```

## Get Analysis Report

Generate investment analysis for a stock:

```bash
curl -s -X GET "http://localhost:9000/analysis?stock=000858"
```

## Ask Question

Ask a financial question using RAG + LLM:

```bash
curl -s -X POST http://localhost:9000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "五粮液的盈利能力如何？"}'
```

## API Endpoints Summary

| Endpoint         | Method | Description                                          |
| ---------------- | ------ | ---------------------------------------------------- |
| `/query`         | POST   | Semantic search on annual reports                    |
| `/announcements` | POST   | Get company announcements (annual/quarterly reports) |
| `/metrics`       | POST   | Get structured financial metrics                     |
| `/analysis`      | GET    | Generate AI investment analysis                      |
| `/ask`           | POST   | RAG + LLM Q&A                                        |

## Example: Get 金风科技 (002202) Announcements

```bash
curl -s -X POST http://localhost:9000/announcements \
  -H "Content-Type: application/json" \
  -d '{"code": "002202"}' | jq '.[:5]'
```

This returns all announcements including:

- Annual reports (年度报告)
- Interim reports (半年报)
- Quarterly reports (季报)
- Stock rights announcements (权益变动)
- Corporate governance (治理)
- And more...

## Important Notes

- The API runs on port **9000**
- Use stock codes like `002202` (金风科技), `600000` (浦发银行)
- Query endpoint uses semantic search on annual reports
- Announcements endpoint provides comprehensive company disclosures
- Metrics endpoint returns structured financial data

## Example Usage

```python
import requests

# Get company announcements
resp = requests.post("http://localhost:9000/announcements", json={
    "code": "002202"
})
announcements = resp.json()
print(f"Found {len(announcements)} announcements")

# Query stock reports
resp = requests.post("http://localhost:9000/query", json={
    "question": "金风科技 2024年 财务",
    "top_k": 3
})
print(resp.json())

# Get metrics
resp = requests.post("http://localhost:9000/metrics", json={
    "code": "002202"
})
print(resp.json())
```
