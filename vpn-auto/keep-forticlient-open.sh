#!/bin/bash
# 保持 FortiClient 窗口打开
# 使用 wmctrl 和 xdotool 防止窗口最小化

export DISPLAY=:1

echo "========================================"
echo "保持 FortiClient 窗口打开"
echo "========================================"
echo ""

# 检查依赖
if ! command -v wmctrl &> /dev/null; then
    echo "安装 wmctrl..."
    sudo apt-get install -y wmctrl
fi

# 查找 FortiClient 窗口
echo "查找 FortiClient 窗口..."
WINDOW_ID=$(xdotool search --name "FortiClient" 2>/dev/null | head -1)

if [ -z "$WINDOW_ID" ]; then
    echo "❌ 未找到 FortiClient 窗口"
    echo "请先启动 FortiClient GUI"
    exit 1
fi

echo "✅ 找到窗口 ID: $WINDOW_ID"
echo ""

# 设置窗口属性
echo "设置窗口属性..."

# 1. 取消最小化
xdotool windowactivate "$WINDOW_ID"
echo "✅ 激活窗口"

# 2. 设置窗口为 sticky（在所有工作区显示）
wmctrl -i -r "$WINDOW_ID" -b add,sticky
echo "✅ 设置为 sticky"

# 3. 设置窗口为 above（始终在上层）
wmctrl -i -r "$WINDOW_ID" -b add,above
echo "✅ 设置为 above"

# 4. 移动窗口到可见位置
xdotool windowmove "$WINDOW_ID" 100 100
echo "✅ 移动窗口到 (100, 100)"

# 5. 设置窗口大小
xdotool windowsize "$WINDOW_ID" 800 600
echo "✅ 设置窗口大小为 800x600"

echo ""
echo "========================================"
echo "✅ 窗口配置完成"
echo "========================================"
echo ""
echo "FortiClient 窗口现在应该保持打开状态"
echo ""
echo "如果需要监控窗口状态，运行："
echo "  ./monitor-forticlient-window.sh"
