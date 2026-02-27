#!/bin/bash
# 测试新部署的 use cases

set -e

CRON_FILE="/home/tsl/.openclaw/cron/jobs.json"

echo "🧪 OpenClaw Use Cases 测试工具"
echo "================================"
echo ""

# 检查 jq 是否安装
if ! command -v jq &> /dev/null; then
    echo "❌ 需要安装 jq 工具"
    exit 1
fi

# 检查 openclaw 命令
if ! command -v openclaw &> /dev/null; then
    echo "❌ openclaw 命令不可用"
    exit 1
fi

echo "📋 当前定时任务列表："
echo ""

# 列出所有任务
jq -r '.jobs[] | "\(.name) - \(if .enabled then "✅ 启用" else "❌ 禁用" end) - \(.schedule.expr)"' "$CRON_FILE"

echo ""
echo "================================"
echo ""
echo "选择要测试的任务："
echo "1. tech_news_digest (科技新闻摘要)"
echo "2. reddit_daily_digest (Reddit 摘要)"
echo "3. custom_morning_brief (自定义晨报)"
echo "4. earnings_tracker_weekly (财报追踪)"
echo "5. 测试所有新任务"
echo "6. 查看最近的任务执行日志"
echo "0. 退出"
echo ""

read -p "选择 (输入数字): " choice

case $choice in
    1)
        echo "🧪 测试科技新闻摘要..."
        TASK_ID=$(jq -r '.jobs[] | select(.name=="tech_news_digest") | .id' "$CRON_FILE")
        if [ -z "$TASK_ID" ]; then
            echo "❌ 任务未找到，请先部署"
            exit 1
        fi
        echo "任务 ID: $TASK_ID"
        openclaw cron run "$TASK_ID"
        ;;
        
    2)
        echo "🧪 测试 Reddit 摘要..."
        TASK_ID=$(jq -r '.jobs[] | select(.name=="reddit_daily_digest") | .id' "$CRON_FILE")
        if [ -z "$TASK_ID" ]; then
            echo "❌ 任务未找到，请先部署"
            exit 1
        fi
        echo "任务 ID: $TASK_ID"
        openclaw cron run "$TASK_ID"
        ;;
        
    3)
        echo "🧪 测试自定义晨报..."
        TASK_ID=$(jq -r '.jobs[] | select(.name=="custom_morning_brief") | .id' "$CRON_FILE")
        if [ -z "$TASK_ID" ]; then
            echo "❌ 任务未找到，请先部署"
            exit 1
        fi
        echo "任务 ID: $TASK_ID"
        openclaw cron run "$TASK_ID"
        ;;
        
    4)
        echo "🧪 测试财报追踪..."
        TASK_ID=$(jq -r '.jobs[] | select(.name=="earnings_tracker_weekly") | .id' "$CRON_FILE")
        if [ -z "$TASK_ID" ]; then
            echo "❌ 任务未找到，请先部署"
            exit 1
        fi
        echo "任务 ID: $TASK_ID"
        openclaw cron run "$TASK_ID"
        ;;
        
    5)
        echo "🧪 测试所有新任务..."
        echo ""
        
        for task_name in tech_news_digest reddit_daily_digest custom_morning_brief earnings_tracker_weekly; do
            TASK_ID=$(jq -r ".jobs[] | select(.name==\"$task_name\") | .id" "$CRON_FILE")
            if [ -n "$TASK_ID" ]; then
                echo "▶️  测试 $task_name (ID: $TASK_ID)"
                openclaw cron run "$TASK_ID" || echo "⚠️  任务执行失败"
                echo ""
                sleep 2
            else
                echo "⏭️  跳过 $task_name (未部署)"
                echo ""
            fi
        done
        
        echo "✅ 所有测试完成"
        ;;
        
    6)
        echo "📜 最近的任务执行日志："
        echo ""
        
        jq -r '.jobs[] | "
任务: \(.name)
状态: \(if .state.lastStatus == "ok" then "✅ 成功" else "❌ 失败" end)
上次运行: \(.state.lastRunAtMs / 1000 | strftime("%Y-%m-%d %H:%M:%S"))
执行时长: \(.state.lastDurationMs / 1000)秒
连续错误: \(.state.consecutiveErrors)次
下次运行: \(.state.nextRunAtMs / 1000 | strftime("%Y-%m-%d %H:%M:%S"))
---"' "$CRON_FILE"
        ;;
        
    0)
        echo "👋 退出"
        exit 0
        ;;
        
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "💡 提示："
echo "- 查看 Gateway 日志: tail -f /tmp/openclaw-gateway.log"
echo "- 查看任务状态: openclaw cron list"
echo "- 查看飞书消息确认任务结果"
