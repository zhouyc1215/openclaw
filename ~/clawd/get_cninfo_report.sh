#!/bin/bash
# 巨潮网财报查询脚本
# API: http://webapi.cninfo.com.cn/api/stock/p_public0001

# 使用说明：
# 1. 需要先获取巨潮网 API Token
# 2. 设置环境变量 CNINFO_TOKEN
# 3. 运行脚本查询财报

CNINFO_API="http://webapi.cninfo.com.cn/api/stock/p_public0001"
TOKEN="${CNINFO_TOKEN:-}"

if [ -z "$TOKEN" ]; then
    echo "错误：未设置 CNINFO_TOKEN 环境变量"
    echo "请先获取巨潮网 API Token 并设置："
    echo "export CNINFO_TOKEN='your_token_here'"
    exit 1
fi

# 股票代码（默认查询英伟达相关的中国上市公司）
STOCK_CODE="${1:-}"

if [ -z "$STOCK_CODE" ]; then
    echo "用法: $0 <股票代码>"
    echo "示例: $0 000001  # 查询平安银行"
    echo "示例: $0 600519  # 查询贵州茅台"
    exit 1
fi

# 发送请求
curl -s -X POST "$CNINFO_API" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"scode\":\"$STOCK_CODE\"}" | jq '.'

# 注意：巨潮网主要提供中国A股上市公司信息
# 英伟达(NVDA)是美股，不在巨潮网数据库中
# 如需查询美股财报，建议使用：
# - SEC EDGAR API (免费)
# - Alpha Vantage API (有免费额度)
# - Yahoo Finance API
# - OpenRouter 搜索工具（已配置）
