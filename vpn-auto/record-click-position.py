#!/usr/bin/env python3
"""
记录实际点击位置
让用户手动点击按钮，记录准确的坐标
"""

import sys
import os
import time
from pynput import mouse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COORDS_FILE = os.path.join(SCRIPT_DIR, "button_coords.txt")

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"

def on_click(x, y, button, pressed):
    """鼠标点击事件处理"""
    if pressed:
        print(f"\n✅ 记录到点击位置: ({x}, {y})")
        
        # 保存坐标
        with open(COORDS_FILE, 'w') as f:
            f.write(f"{x},{y}\n")
        
        print(f"✅ 坐标已保存到: {COORDS_FILE}")
        print("\n现在可以使用这个坐标来自动点击")
        
        # 停止监听
        return False

def record_position():
    """记录点击位置"""
    print("========================================")
    print("记录按钮点击位置")
    print("========================================")
    print()
    print("说明：")
    print("1. 确保 FortiClient 窗口打开并显示 SAML login 按钮")
    print("2. 用鼠标点击 SAML login 按钮")
    print("3. 脚本会自动记录点击位置")
    print()
    print("等待点击...")
    print("(按 Ctrl+C 取消)")
    print()
    
    try:
        # 监听鼠标点击
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n已取消")

if __name__ == "__main__":
    setup()
    record_position()
