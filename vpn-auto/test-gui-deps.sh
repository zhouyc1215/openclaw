#!/bin/bash
# 测试 GUI 自动化依赖

echo "=========================================="
echo "测试 GUI 自动化依赖"
echo "=========================================="
echo ""

export DISPLAY=:1
export XAUTHORITY=/home/tsl/.Xauthority

echo "1. 检查 Python 版本..."
python3 --version

echo ""
echo "2. 检查 pyautogui..."
python3 -c "import pyautogui; print('✅ pyautogui 已安装，版本:', pyautogui.__version__)" 2>&1 || echo "❌ pyautogui 未安装"

echo ""
echo "3. 检查 opencv..."
python3 -c "import cv2; print('✅ opencv 已安装，版本:', cv2.__version__)" 2>&1 || echo "❌ opencv 未安装"

echo ""
echo "4. 检查 PIL..."
python3 -c "from PIL import Image; print('✅ PIL 已安装')" 2>&1 || echo "❌ PIL 未安装"

echo ""
echo "5. 检查 scrot..."
which scrot && echo "✅ scrot 已安装" || echo "❌ scrot 未安装"

echo ""
echo "6. 测试截图功能..."
python3 << 'PYEOF'
import os
os.environ['DISPLAY'] = ':1'
try:
    import pyautogui
    screenshot = pyautogui.screenshot()
    screenshot.save('/tmp/test_screenshot.png')
    print('✅ 截图功能正常')
    print('   截图已保存: /tmp/test_screenshot.png')
except Exception as e:
    print(f'❌ 截图失败: {e}')
PYEOF

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
