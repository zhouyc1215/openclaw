#!/usr/bin/env python3
"""
直接点击已知坐标
使用之前成功识别的按钮位置
"""

import sys
import os
import time

try:
    import pyautogui
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    sys.exit(1)

# 之前成功识别的按钮坐标
BUTTON_X = 942
BUTTON_Y = 787

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"

def click_button():
    """直接点击按钮"""
    print("========================================")
    print("直接点击 SAML login 按钮")
    print("========================================")
    print()
    
    print(f"按钮坐标: ({BUTTON_X}, {BUTTON_Y})")
    print()
    
    # 先移动鼠标到按钮位置
    print("移动鼠标到按钮...")
    pyautogui.moveTo(BUTTON_X, BUTTON_Y, duration=0.5)
    time.sleep(0.3)
    
    # 点击
    print("点击按钮...")
    pyautogui.click()
    time.sleep(1)
    
    print("✅ 已点击按钮")
    print()
    print("请检查 FortiClient 窗口是否有反应")

if __name__ == "__main__":
    setup()
    click_button()
