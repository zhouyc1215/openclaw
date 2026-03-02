#!/bin/bash
# 最大化 FortiClient 窗口

echo "查找 FortiClient 窗口..."
WINDOW_ID=$(DISPLAY=:1 xdotool search --name "FortiClient" | head -1)

if [ -z "$WINDOW_ID" ]; then
    echo "❌ 没有找到 FortiClient 窗口"
    exit 1
fi

echo "找到窗口 ID: $WINDOW_ID"
echo ""

echo "当前窗口状态:"
DISPLAY=:1 xdotool getwindowgeometry $WINDOW_ID

echo ""
echo "尝试显示和最大化窗口..."

# 取消最小化
DISPLAY=:1 wmctrl -i -r $WINDOW_ID -b remove,hidden 2>/dev/null || echo "  wmctrl 命令不可用"

# 激活窗口
DISPLAY=:1 xdotool windowactivate --sync $WINDOW_ID
sleep 0.5

# 移动窗口到可见位置
DISPLAY=:1 xdotool windowmove $WINDOW_ID 100 100
sleep 0.5

# 调整窗口大小
DISPLAY=:1 xdotool windowsize $WINDOW_ID 1200 800
sleep 0.5

# 再次激活
DISPLAY=:1 xdotool windowactivate --sync $WINDOW_ID
sleep 0.5

echo ""
echo "调整后的窗口状态:"
DISPLAY=:1 xdotool getwindowgeometry $WINDOW_ID

echo ""
echo "截图验证..."
DISPLAY=:1 scrot maximized_window.png
echo "✅ 截图已保存: maximized_window.png"
