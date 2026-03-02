#!/bin/bash
# 测试 OCR + 颜色检测方案

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "测试 OCR + 颜色检测方案"
echo "=========================================="
echo ""

# 检查依赖
echo "检查依赖..."
if ! command -v tesseract &> /dev/null; then
    echo "❌ tesseract 未安装"
    echo "请运行: sudo apt install tesseract-ocr"
    exit 1
fi

if ! python3 -c "import pytesseract" 2>/dev/null; then
    echo "❌ pytesseract 未安装"
    echo "请运行: pip3 install pytesseract"
    exit 1
fi

echo "✅ 所有依赖已安装"
echo ""

# 设置权限
chmod +x find-saml-button-ocr.py

# 运行脚本
echo "运行 OCR 检测脚本..."
echo ""
python3 find-saml-button-ocr.py

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "请检查:"
echo "  1. VPN 是否开始连接"
echo "  2. 查看调试图像: saml_button_detected.png"
echo ""
