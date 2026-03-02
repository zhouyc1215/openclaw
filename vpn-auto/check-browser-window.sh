#!/bin/bash
# 检查是否有浏览器窗口打开（SAML 认证）

echo "=========================================="
echo "检查浏览器窗口"
echo "=========================================="
echo ""

echo "1. 检查所有窗口..."
DISPLAY=:1 xdotool search --name "" 2>/dev/null | while read window_id; do
    window_name=$(DISPLAY=:1 xdotool getwindowname "$window_id" 2>/dev/null)
    if [ -n "$window_name" ]; then
        echo "  窗口 ID: $window_id"
        echo "  窗口名称: $window_name"
        echo ""
    fi
done

echo "=========================================="
echo ""

echo "2. 检查浏览器窗口..."
for browser in "Chrome" "Firefox" "chromium" "firefox"; do
    if DISPLAY=:1 xdotool search --name "$browser" > /dev/null 2>&1; then
        echo "✅ 找到 $browser 窗口"
        DISPLAY=:1 xdotool search --name "$browser" 2>/dev/null | while read window_id; do
            window_name=$(DISPLAY=:1 xdotool getwindowname "$window_id" 2>/dev/null)
            echo "  窗口 ID: $window_id"
            echo "  窗口名称: $window_name"
        done
        echo ""
    fi
done

echo "=========================================="
echo ""

echo "3. 截图当前状态..."
DISPLAY=:1 scrot current_state.png 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 截图已保存: current_state.png"
else
    echo "❌ 截图失败"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
