#!/bin/bash
# 测试定时任务 announce 修复

echo "=== 测试定时任务结果通知 ==="
echo ""

# 获取一个定时任务 ID（get_xian_weather_forecast）
TASK_ID="440648af-dcab-4cc7-8086-45c0f87263c6"

echo "任务 ID: $TASK_ID"
echo "超时时间: 180 秒"
echo ""

echo "执行定时任务..."
pnpm openclaw cron run "$TASK_ID" --timeout 180000

echo ""
echo "=== 测试完成 ==="
echo ""
echo "请检查飞书是否收到任务结果通知"
echo "如果收到通知，说明修复成功！"
