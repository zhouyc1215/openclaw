#!/bin/bash
# 手动添加任务到 cron jobs

set -e

CRON_FILE="/home/tsl/.openclaw/cron/jobs.json"
EXAMPLE_FILE="example-task-config.json"

echo "📝 手动添加任务工具"
echo "===================="
echo ""

if [ ! -f "$EXAMPLE_FILE" ]; then
    echo "❌ 找不到示例配置文件: $EXAMPLE_FILE"
    exit 1
fi

if [ ! -f "$CRON_FILE" ]; then
    echo "❌ 找不到 cron 配置文件: $CRON_FILE"
    exit 1
fi

# 生成 UUID
TASK_ID=$(uuidgen)
CREATED_AT=$(date +%s)000

echo "生成的任务 ID: $TASK_ID"
echo "创建时间: $CREATED_AT"
echo ""

# 备份
echo "📦 备份当前配置..."
cp "$CRON_FILE" "${CRON_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# 读取示例配置
TASK_CONFIG=$(cat "$EXAMPLE_FILE")

# 替换占位符
TASK_CONFIG=$(echo "$TASK_CONFIG" | sed "s/REPLACE_WITH_UUID/$TASK_ID/g")
TASK_CONFIG=$(echo "$TASK_CONFIG" | jq ".createdAtMs = $CREATED_AT | .updatedAtMs = $CREATED_AT")

echo "任务配置："
echo "$TASK_CONFIG" | jq '.'
echo ""

read -p "确认添加此任务？(y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "❌ 取消添加"
    exit 0
fi

# 添加任务
jq --argjson task "$TASK_CONFIG" '.jobs += [$task]' "$CRON_FILE" > "${CRON_FILE}.tmp"
mv "${CRON_FILE}.tmp" "$CRON_FILE"

echo "✅ 任务已添加"
echo ""
echo "📊 当前任务总数: $(jq '.jobs | length' "$CRON_FILE")"
echo ""
echo "🔄 请重启 Gateway: openclaw gateway restart"
