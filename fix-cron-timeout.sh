#!/bin/bash
# 飞书定时任务超时问题修复脚本
# 为所有 cron 任务添加合适的 timeoutSeconds 配置

set -e

CRON_CONFIG="$HOME/.openclaw/cron/jobs.json"
BACKUP_FILE="$HOME/.openclaw/cron/jobs.json.bak-$(date +%Y%m%d-%H%M%S)"

echo "🔧 飞书定时任务超时修复脚本"
echo "================================"
echo ""

# 检查配置文件是否存在
if [ ! -f "$CRON_CONFIG" ]; then
    echo "❌ 错误：找不到配置文件 $CRON_CONFIG"
    exit 1
fi

# 检查 jq 是否安装
if ! command -v jq &> /dev/null; then
    echo "❌ 错误：需要安装 jq 工具"
    echo "   安装命令：sudo apt install jq  或  brew install jq"
    exit 1
fi

# 备份配置文件
echo "📦 备份配置文件..."
cp "$CRON_CONFIG" "$BACKUP_FILE"
echo "   备份位置：$BACKUP_FILE"
echo ""

# 显示当前任务列表
echo "📋 当前定时任务："
jq -r '.jobs[] | "   - \(.name) (ID: \(.id))"' "$CRON_CONFIG"
echo ""

# 为每个任务添加 timeoutSeconds
echo "⏱️  添加超时配置..."

# auto-commit-openclaw: 180 秒
jq '(.jobs[] | select(.id == "5e44ba7a-2a52-48db-815f-56925535d08b") | .payload) += {"timeoutSeconds": 180}' \
  "$CRON_CONFIG" > /tmp/jobs.json && mv /tmp/jobs.json "$CRON_CONFIG"
echo "   ✓ auto-commit-openclaw: 180 秒"

# get_xian_weather_forecast: 180 秒
jq '(.jobs[] | select(.id == "bad3205a-ddab-4efe-9426-1703b9b757c4") | .payload) += {"timeoutSeconds": 180}' \
  "$CRON_CONFIG" > /tmp/jobs.json && mv /tmp/jobs.json "$CRON_CONFIG"
echo "   ✓ get_xian_weather_forecast: 180 秒"

# get_top_ai_projects: 120 秒
jq '(.jobs[] | select(.id == "440648af-dcab-4cc7-8086-45c0f87263c6") | .payload) += {"timeoutSeconds": 120}' \
  "$CRON_CONFIG" > /tmp/jobs.json && mv /tmp/jobs.json "$CRON_CONFIG"
echo "   ✓ get_top_ai_projects: 120 秒"

# backup_cron_results: 240 秒
jq '(.jobs[] | select(.id == "backup-cron-results") | .payload) += {"timeoutSeconds": 240}' \
  "$CRON_CONFIG" > /tmp/jobs.json && mv /tmp/jobs.json "$CRON_CONFIG"
echo "   ✓ backup_cron_results: 240 秒"

echo ""

# 验证配置
echo "✅ 验证配置："
jq -r '.jobs[] | "   - \(.name): \(.payload.timeoutSeconds // "default (600s)") 秒"' "$CRON_CONFIG"
echo ""

# 提示重启 Gateway
echo "🔄 下一步："
echo "   1. 重启 Gateway 使配置生效："
echo "      pkill -9 -f openclaw-gateway || true"
echo "      nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &"
echo ""
echo "   2. 测试单个任务（使用增加的 CLI 超时）："
echo "      openclaw cron run auto-commit-openclaw --timeout 300000"
echo ""
echo "   3. 查看 Gateway 日志："
echo "      tail -f /tmp/openclaw-gateway.log"
echo ""

echo "✨ 配置更新完成！"
echo ""
echo "📚 详细文档：FEISHU-TIMEOUT-SOLUTION.md"
