#!/bin/bash
# 测试安装状态

echo "检查关键依赖..."

# 检查 Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3: $(python3 --version)"
else
    echo "❌ Python3 未安装"
fi

# 检查 pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip3: $(pip3 --version)"
else
    echo "❌ pip3 未安装"
fi

# 检查 xdotool
if command -v xdotool &> /dev/null; then
    echo "✅ xdotool: $(xdotool --version)"
else
    echo "❌ xdotool 未安装"
fi

# 检查 scrot
if command -v scrot &> /dev/null; then
    echo "✅ scrot: 已安装"
else
    echo "❌ scrot 未安装"
fi

# 检查 Python 库
echo ""
echo "检查 Python 库..."

python3 -c "import yaml" 2>/dev/null && echo "✅ pyyaml" || echo "❌ pyyaml"
python3 -c "import cv2" 2>/dev/null && echo "✅ opencv-python" || echo "❌ opencv-python"
python3 -c "import numpy" 2>/dev/null && echo "✅ numpy" || echo "❌ numpy"

echo ""
echo "检查 apt 安装状态..."
if ps aux | grep -E "(apt|dpkg)" | grep -v grep > /dev/null; then
    echo "⚠️  apt 正在运行，安装尚未完成"
else
    echo "✅ apt 空闲，安装可能已完成"
fi
