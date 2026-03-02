#!/bin/bash
# 测试点击并对比截图

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "测试点击并对比截图"
echo "=========================================="
echo ""

# 1. 点击前截图
echo "步骤 1: 点击前截图..."
DISPLAY=:1 scrot before_click.png
echo "✅ 截图已保存: before_click.png"
echo ""

# 2. 运行点击脚本
echo "步骤 2: 运行点击脚本..."
python3 smart-find-button.py
echo ""

# 3. 点击后立即截图
echo "步骤 3: 点击后立即截图..."
sleep 2
DISPLAY=:1 scrot after_click_2s.png
echo "✅ 截图已保存: after_click_2s.png"
echo ""

# 4. 等待5秒后再截图
echo "步骤 4: 等待5秒后再截图..."
sleep 5
DISPLAY=:1 scrot after_click_7s.png
echo "✅ 截图已保存: after_click_7s.png"
echo ""

# 5. 等待10秒后再截图
echo "步骤 5: 等待10秒后再截图..."
sleep 10
DISPLAY=:1 scrot after_click_17s.png
echo "✅ 截图已保存: after_click_17s.png"
echo ""

echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="
echo ""
echo "请对比以下截图："
echo "  1. before_click.png (点击前)"
echo "  2. hover_effect.png (hover 效果)"
echo "  3. after_click_2s.png (点击后2秒)"
echo "  4. after_click_7s.png (点击后7秒)"
echo "  5. after_click_17s.png (点击后17秒)"
echo ""
echo "检查是否有以下变化："
echo "  - 按钮颜色变化"
echo "  - 出现连接进度"
echo "  - 出现 MFA 认证提示"
echo "  - 出现错误消息"
echo ""
