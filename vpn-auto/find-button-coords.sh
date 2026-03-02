#!/bin/bash
# 查找按钮的准确坐标
# 方法：让用户将鼠标移动到按钮上，然后记录坐标

export DISPLAY=:1

echo "========================================"
echo "查找 SAML login 按钮的准确坐标"
echo "========================================"
echo ""
echo "说明："
echo "1. 确保 FortiClient 窗口打开并显示 SAML login 按钮"
echo "2. 将鼠标移动到按钮的中心位置"
echo "3. 按 Enter 键记录坐标"
echo ""

read -p "准备好后按 Enter..."

echo ""
echo "将鼠标移动到 SAML login 按钮的中心..."
echo "3 秒后自动记录坐标..."
sleep 3

# 获取鼠标位置
MOUSE_POS=$(xdotool getmouselocation --shell)
eval "$MOUSE_POS"

echo ""
echo "✅ 记录到坐标:"
echo "   X = $X"
echo "   Y = $Y"
echo "   窗口 ID = $WINDOW"
echo ""

# 保存到文件
echo "$X,$Y" > button_coords.txt
echo "✅ 坐标已保存到: button_coords.txt"
echo ""

# 测试点击
echo "是否测试点击这个位置？(y/n)"
read -p "> " TEST_CLICK

if [ "$TEST_CLICK" = "y" ] || [ "$TEST_CLICK" = "Y" ]; then
    echo ""
    echo "测试点击 ($X, $Y)..."
    
    # 激活窗口
    if [ -n "$WINDOW" ]; then
        xdotool windowactivate --sync "$WINDOW"
        sleep 0.3
    fi
    
    # 点击
    xdotool mousemove --sync "$X" "$Y"
    sleep 0.2
    xdotool click 1
    
    echo "✅ 已点击"
    echo ""
    echo "请检查 FortiClient 窗口是否有反应"
fi

echo ""
echo "========================================"
echo "完成"
echo "========================================"
