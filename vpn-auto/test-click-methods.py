#!/usr/bin/env python3
"""
测试不同的点击方式
"""

import sys
import os
import time

try:
    import pyautogui
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUTTON_IMAGE = os.path.join(SCRIPT_DIR, "images", "saml_button_small.png")

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"

def test_clicks():
    """测试不同的点击方式"""
    print("========================================")
    print("测试不同的点击方式")
    print("========================================")
    print()
    
    if not os.path.exists(BUTTON_IMAGE):
        print(f"❌ 按钮图像不存在: {BUTTON_IMAGE}")
        return
    
    print(f"✅ 按钮图像: {BUTTON_IMAGE}")
    print()
    
    # 查找按钮
    print("查找按钮...")
    try:
        location = pyautogui.locateOnScreen(
            BUTTON_IMAGE,
            confidence=0.7,
            grayscale=True
        )
        
        if not location:
            print("❌ 未找到按钮")
            return
        
        x, y = pyautogui.center(location)
        print(f"✅ 找到按钮: ({x}, {y})")
        print()
        
        # 方法 1: 单击
        print("方法 1: 单击")
        pyautogui.click(x, y)
        print(f"  点击坐标: ({x}, {y})")
        time.sleep(2)
        print()
        
        # 方法 2: 双击
        print("方法 2: 双击")
        pyautogui.doubleClick(x, y)
        print(f"  双击坐标: ({x}, {y})")
        time.sleep(2)
        print()
        
        # 方法 3: 移动后点击
        print("方法 3: 移动鼠标后点击")
        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(0.2)
        pyautogui.click()
        print(f"  移动到: ({x}, {y}) 然后点击")
        time.sleep(2)
        print()
        
        print("========================================")
        print("测试完成")
        print("========================================")
        print()
        print("请检查 FortiClient 窗口是否有反应")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    setup()
    test_clicks()
