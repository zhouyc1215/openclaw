#!/bin/bash
# 自动截取 FortiClient SAML login 按钮
# 使用全屏截图，然后截取中央下方区域

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGES_DIR="$SCRIPT_DIR/images"

export DISPLAY=:1

echo "========================================"
echo "自动捕获 SAML login 按钮"
echo "========================================"
echo ""

# 创建 images 目录
mkdir -p "$IMAGES_DIR"

# 等待 2 秒
echo "2 秒后开始截图..."
sleep 2

# 使用 scrot 截取全屏
FULLSCREEN_PATH="$SCRIPT_DIR/fullscreen_saml.png"
echo "截取全屏..."
scrot "$FULLSCREEN_PATH"

if [ ! -f "$FULLSCREEN_PATH" ]; then
    echo "❌ 全屏截图失败"
    exit 1
fi

echo "✅ 全屏截图已保存: $FULLSCREEN_PATH"

# 获取屏幕尺寸
SCREEN_INFO=$(xdpyinfo -display :1 | grep dimensions | awk '{print $2}')
SCREEN_WIDTH=$(echo $SCREEN_INFO | cut -d'x' -f1)
SCREEN_HEIGHT=$(echo $SCREEN_INFO | cut -d'x' -f2)

echo "屏幕尺寸: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}"

# 计算按钮区域（中央下方）
# 假设按钮在屏幕中央下方 30%-70% 宽度，60%-90% 高度
BUTTON_LEFT=$((SCREEN_WIDTH * 30 / 100))
BUTTON_TOP=$((SCREEN_HEIGHT * 60 / 100))
BUTTON_WIDTH=$((SCREEN_WIDTH * 40 / 100))
BUTTON_HEIGHT=$((SCREEN_HEIGHT * 30 / 100))

echo "按钮区域: ${BUTTON_WIDTH}x${BUTTON_HEIGHT}+${BUTTON_LEFT}+${BUTTON_TOP}"

# 使用 ImageMagick 裁剪图像（如果可用）
BUTTON_PATH="$IMAGES_DIR/saml_login_button.png"

if command -v convert &> /dev/null; then
    echo "使用 ImageMagick 裁剪..."
    convert "$FULLSCREEN_PATH" -crop "${BUTTON_WIDTH}x${BUTTON_HEIGHT}+${BUTTON_LEFT}+${BUTTON_TOP}" "$BUTTON_PATH"
else
    echo "使用 Python 裁剪..."
    python3 "$SCRIPT_DIR/crop-saml-button.py"
fi

if [ ! -f "$BUTTON_PATH" ]; then
    echo "❌ 裁剪图像失败"
    exit 1
fi

echo "✅ 按钮区域已保存: $BUTTON_PATH"

# 显示文件信息
FILE_SIZE=$(ls -lh "$BUTTON_PATH" | awk '{print $5}')
IMAGE_SIZE=$(identify "$BUTTON_PATH" | awk '{print $3}')

echo ""
echo "文件大小: $FILE_SIZE"
echo "图像尺寸: $IMAGE_SIZE"

echo ""
echo "========================================"
echo "✅ 捕获完成"
echo "========================================"
echo ""
echo "注意：此图像包含按钮可能所在的区域"
echo "如果需要更精确的截图，请使用手动模式:"
echo "  python3 capture-saml-simple.py"
