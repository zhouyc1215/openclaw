#!/bin/bash
# 使用 xdotool 点击 SAML login 按钮
# xdotool 更可靠，可以激活窗口并模拟真实的鼠标点击

set -e

export DISPLAY=:1

BUTTON_X=942
BUTTON_Y=787

echo "========================================"
echo "使用 xdotool 点击 SAML login 按钮"
echo "========================================"
echo ""

# 检查 xdotool 是否安装
if ! command -v xdotool &> /dev/null; then
    echo "❌ xdotool 未安装"
    echo "安装: sudo apt-get install xdotool"
    exit 1
fi

echo "✅ xdotool 已安装"
echo ""

# 1. 查找 FortiClient 窗口
echo "步骤 1: 查找 FortiClient 窗口..."
WINDOW_ID=$(xdotool search --name "FortiClient" | head -1)

if [ -z "$WINDOW_ID" ]; then
    echo "❌ 未找到 FortiClient 窗口"
    exit 1
fi

echo "✅ 找到窗口 ID: $WINDOW_ID"
echo ""

# 2. 激活窗口
echo "步骤 2: 激活窗口..."
xdotool windowactivate --sync "$WINDOW_ID"
sleep 0.5
echo "✅ 窗口已激活"
echo ""

# 3. 移动鼠标到按钮位置
echo "步骤 3: 移动鼠标到按钮 ($BUTTON_X, $BUTTON_Y)..."
xdotool mousemove --sync "$BUTTON_X" "$BUTTON_Y"
sleep 0.3

# 验证鼠标位置
CURRENT_POS=$(xdotool getmouselocation --shell)
echo "$CURRENT_POS"
echo "✅ 鼠标已移动"
echo ""

# 4. 点击
echo "步骤 4: 点击按钮..."
xdotool click 1
sleep 0.5
echo "✅ 已点击按钮"
echo ""

echo "========================================"
echo "✅ 操作完成"
echo "========================================"
echo ""
echo "请检查 FortiClient 窗口是否有反应"
echo "如果需要 MFA 认证，请在手机上完成"
