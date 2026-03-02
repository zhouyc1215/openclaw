#!/usr/bin/env python3
"""
测试光标移动功能
"""

import sys
import os
import time

try:
    import pyautogui
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    sys.exit(1)

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"

def test_cursor_movement():
    """测试光标移动"""
    print("========================================")
    print("测试光标移动功能")
    print("========================================")
    print()
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    print(f"屏幕尺寸: {screen_width}x{screen_height}")
    print()
    
    # 测试点 1: 屏幕左上角
    print("测试 1: 移动到左上角 (100, 100)")
    pyautogui.moveTo(100, 100, duration=1)
    time.sleep(0.5)
    pos = pyautogui.position()
    print(f"  当前位置: {pos}")
    print(f"  移动成功: {pos == (100, 100)}")
    print()
    
    # 测试点 2: 屏幕中央
    center_x = screen_width // 2
    center_y = screen_height // 2
    print(f"测试 2: 移动到中央 ({center_x}, {center_y})")
    pyautogui.moveTo(center_x, center_y, duration=1)
    time.sleep(0.5)
    pos = pyautogui.position()
    print(f"  当前位置: {pos}")
    print(f"  移动成功: {pos == (center_x, center_y)}")
    print()
    
    # 测试点 3: 按钮位置
    button_x = 942
    button_y = 787
    print(f"测试 3: 移动到按钮位置 ({button_x}, {button_y})")
    pyautogui.moveTo(button_x, button_y, duration=1)
    time.sleep(0.5)
    pos = pyautogui.position()
    print(f"  当前位置: {pos}")
    print(f"  移动成功: {pos == (button_x, button_y)}")
    print()
    
    # 测试点 4: 使用 move 相对移动
    print("测试 4: 相对移动 (+100, +100)")
    start_pos = pyautogui.position()
    print(f"  起始位置: {start_pos}")
    pyautogui.move(100, 100, duration=1)
    time.sleep(0.5)
    end_pos = pyautogui.position()
    print(f"  结束位置: {end_pos}")
    expected = (start_pos[0] + 100, start_pos[1] + 100)
    print(f"  预期位置: {expected}")
    print(f"  移动成功: {end_pos == expected}")
    print()
    
    print("========================================")
    print("测试完成")
    print("========================================")
    print()
    print("如果所有测试都显示'移动成功: False'，")
    print("说明 pyautogui 无法控制光标移动。")
    print()
    print("可能的原因：")
    print("1. X11 权限问题")
    print("2. 需要使用 xdotool 代替 pyautogui")
    print("3. 显示服务器配置问题")

if __name__ == "__main__":
    setup()
    test_cursor_movement()
