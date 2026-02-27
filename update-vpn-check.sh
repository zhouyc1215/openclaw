#!/bin/bash
# 为所有新增任务添加VPN检查

set -e

CRON_FILE="/home/tsl/.openclaw/cron/jobs.json"
BACKUP_FILE="${CRON_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

echo "📦 备份配置文件..."
cp "$CRON_FILE" "$BACKUP_FILE"

echo "🔧 更新任务配置，添加VPN检查..."

# 为每个新任务添加VPN检查前缀
jq '
.jobs |= map(
  if (.name | test("tech_news_digest|reddit_daily_digest|custom_morning_brief|earnings_tracker_weekly")) then
    .payload.message = "首先检查VPN连接：\n1. 运行 bash /home/tsl/openclaw/check-and-connect-vpn.sh 检查并连接VPN\n2. 如果VPN连接失败，报告错误并停止\n3. 如果VPN连接成功，继续执行以下任务：\n\n" + .payload.message |
    .payload.timeoutSeconds = 360
  else
    .
  end
)
' "$CRON_FILE" > "${CRON_FILE}.tmp" && mv "${CRON_FILE}.tmp" "$CRON_FILE"

echo "✅ 配置更新完成"
echo "📊 更新的任务："
jq -r '.jobs[] | select(.name | test("tech_news_digest|reddit_daily_digest|custom_morning_brief|earnings_tracker_weekly")) | "- \(.name) (timeout: \(.payload.timeoutSeconds)s)"' "$CRON_FILE"
