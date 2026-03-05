#!/bin/bash
# 截取 FortiClient 连接按钮图像

DISPLAY="${DISPLAY:-:1}"
OUTPUT_FILE="/home/tsl/vpn-auto/v2/config/button.png"

echo "=========================================="
echo "FortiClient 按钮截图工具"
echo "=========================================="
echo ""
echo "使用方法："
echo "1. 确保 FortiClient 窗口已打开"
echo "2. 运行此脚本"
echo "3. 在 5 秒内将鼠标移动到连接按钮上"
echo "4. 脚本会自动截取按钮区域"
echo ""
echo "按 Enter 开始..."
read

echo "5 秒后开始截图，请将鼠标移动到按钮上..."
sleep 1
echo "4..."
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1

# 获取鼠标位置
MOUSE_POS=$(DISPLAY=$DISPLAY xdotool getmouselocation --shell)
eval $MOUSE_POS

echo ""
echo "鼠标位置: X=$X, Y=$Y"

# 定义按钮区域（以鼠标为中心，截取 200x60 的区域）
BUTTON_WIDTH=200
BUTTON_HEIGHT=60
BUTTON_X=$((X - BUTTON_WIDTH / 2))
BUTTON_Y=$((Y - BUTTON_HEIGHT / 2))

# 确保坐标不为负数
if [ $BUTTON_X -lt 0 ]; then
    BUTTON_X=0
fi
if [ $BUTTON_Y -lt 0 ]; then
    BUTTON_Y=0
fi

echo "截取区域: X=$BUTTON_X, Y=$BUTTON_Y, W=$BUTTON_WIDTH, H=$BUTTON_HEIGHT"

# 使用 import 命令截图（ImageMagick）
if command -v import &> /dev/null; then
    DISPLAY=$DISPLAY import -window root -crop ${BUTTON_WIDTH}x${BUTTON_HEIGHT}+${BUTTON_X}+${BUTTON_Y} "$OUTPUT_FILE"
    echo "✅ 截图已保存到: $OUTPUT_FILE"
    
    # 显示图像信息
    if command -v identify &> /dev/null; then
        identify "$OUTPUT_FILE"
    fi
    
    # 可选：显示截图
    if command -v display &> /dev/null; then
        echo ""
        echo "是否查看截图？(y/n)"
        read -n 1 SHOW
        echo ""
        if [ "$SHOW" = "y" ] || [ "$SHOW" = "Y" ]; then
            DISPLAY=$DISPLAY display "$OUTPUT_FILE" &
        fi
    fi
    
elif command -v gnome-screenshot &> /dev/null; then
    # 使用 gnome-screenshot（需要手动选择区域）
    echo "使用 gnome-screenshot，请手动选择按钮区域..."
    DISPLAY=$DISPLAY gnome-screenshot -a -f "$OUTPUT_FILE"
    echo "✅ 截图已保存到: $OUTPUT_FILE"
    
else
    echo "❌ 未找到截图工具（import 或 gnome-screenshot）"
    echo "请安装 ImageMagick: sudo apt install imagemagick"
    exit 1
fi

echo ""
echo "=========================================="
echo "完成！"
echo "=========================================="
echo ""
echo "按钮图像已保存到: $OUTPUT_FILE"
echo ""
echo "提示："
echo "- 如果按钮截取不准确，可以重新运行此脚本"
echo "- 或者使用图像编辑工具手动裁剪"
echo "- 建议按钮图像尺寸: 150x50 到 250x70 像素"
