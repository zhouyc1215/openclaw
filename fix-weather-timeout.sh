#!/bin/bash
# 修复天气预报任务的超时配置

CRON_FILE="$HOME/.openclaw/cron/jobs.json"
BACKUP_FILE="$HOME/.openclaw/cron/jobs.json.bak-weather-timeout"

echo "=== 修复天气预报任务超时配置 ==="
echo ""

# 备份
echo "1. 备份当前配置..."
cp "$CRON_FILE" "$BACKUP_FILE"
echo "   备份文件: $BACKUP_FILE"
echo ""

# 更新配置
echo "2. 更新超时配置..."
jq '(.jobs[] | select(.id == "bad3205a-ddab-4efe-9426-1703b9b757c4").payload.timeoutSeconds) = 240' \
  "$CRON_FILE" > "$CRON_FILE.tmp" && mv "$CRON_FILE.tmp" "$CRON_FILE"

echo "   ✅ 已将 timeoutSeconds 从 180 改为 240"
echo ""

# 验证
echo "3. 验证修改..."
TIMEOUT=$(jq -r '.jobs[] | select(.id == "bad3205a-ddab-4efe-9426-1703b9b757c4").payload.timeoutSeconds' "$CRON_FILE")
echo "   当前 timeoutSeconds: $TIMEOUT"
echo ""

if [ "$TIMEOUT" = "240" ]; then
  echo "✅ 修复成功！"
else
  echo "❌ 修复失败，请手动检查"
  exit 1
fi
