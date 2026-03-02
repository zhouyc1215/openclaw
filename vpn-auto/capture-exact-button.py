#!/usr/bin/env python3
"""
精确捕获 SAML login 按钮
使用鼠标定位按钮的精确位置
"""

import sys
import os
import time

try:
    import pyautogui
    from PIL import Image
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

def capture_button():
    """捕获按钮"""
    print("========================================")
    print("精确捕获 SAML login 按钮")
    print("========================================")
    print()
    print("说明：")
    print("1. 确保 FortiClient 窗口打开并显示 SAML login 按钮")
    print("2. 将鼠标悬停在按钮上（不要点击）")
    print("3. 等待 3 秒，脚本会自动捕获按钮周围的小区域")
    print()
    
    input("准备好后按 Enter 开始...")
    
    print()
    print("将鼠标移动到 SAML login 按钮上...")
    print("3 秒后自动捕获...")
    
    time.sleep(3)
    
    # 获取鼠标位置
    center_x, center_y = pyautogui.position()
    print(f"鼠标位置: ({center_x}, {center_y})")
    
    # 截取全屏
    screenshot = pyautogui.screenshot()
    
    # 定义按钮区域（以鼠标为中心，捕获一个小区域）
    # 假设按钮大小约为 100x30
    button_width = 100
    button_height = 30
    
    left = center_x - button_width // 2
    top = center_y - button_height // 2
    right = center_x + button_width // 2
    bottom = center_y + button_height // 2
    
    # 确保坐标在屏幕范围内
    screen_width, screen_height = screenshot.size
    left = max(0, left)
    top = max(0, top)
    right = min(screen_width, right)
    bottom = min(screen_height, bottom)
    
    print(f"捕获区域: 左上({left}, {top}) 右下({right}, {bottom})")
    
    # 裁剪按钮区域
    button_img = screenshot.crop((left, top, right, bottom))
    
    # 保存
    output_path = os.path.join(IMAGES_DIR, "saml_button_exact.png")
    button_img.save(output_path, "PNG")
    
    print()
    print(f"✅ 按钮图像已保存: {output_path}")
    print(f"   图像尺寸: {button_img.width}x{button_img.height}")
    print()
    print("现在可以使用此图像进行自动点击")
    
    # 同时保存全屏截图用于调试
    fullscreen_path = os.path.join(SCRIPT_DIR, "fullscreen_exact.png")
    screenshot.save(fullscreen_path, "PNG")
    print(f"全屏截图已保存: {fullscreen_path}")

if __name__ == "__main__":
    setup()
    capture_button()
