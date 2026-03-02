#!/usr/bin/env python3
"""
图像对比工具
显示按钮图像和当前屏幕的信息，帮助调试识别问题
"""

import os
import sys
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUTTON_IMAGE = os.path.join(SCRIPT_DIR, "images", "connect_button.png")
SCREEN_IMAGE = os.path.join(SCRIPT_DIR, "test_screen.png")

def analyze_images():
    """分析图像信息"""
    print("========================================")
    print("图像对比分析工具")
    print("========================================")
    print()
    
    # 检查按钮图像
    if not os.path.exists(BUTTON_IMAGE):
        print(f"❌ 按钮图像不存在: {BUTTON_IMAGE}")
        return
    
    button_img = Image.open(BUTTON_IMAGE)
    print(f"按钮图像:")
    print(f"  路径: {BUTTON_IMAGE}")
    print(f"  尺寸: {button_img.size} (宽x高)")
    print(f"  模式: {button_img.mode}")
    print(f"  格式: {button_img.format}")
    
    # 显示按钮图像的像素统计
    extrema = button_img.getextrema()
    print(f"  像素范围: {extrema}")
    print()
    
    # 检查屏幕截图
    if not os.path.exists(SCREEN_IMAGE):
        print(f"⚠️  屏幕截图不存在: {SCREEN_IMAGE}")
        print("请先运行: python3 test-image-recognition.py")
        return
    
    screen_img = Image.open(SCREEN_IMAGE)
    print(f"屏幕截图:")
    print(f"  路径: {SCREEN_IMAGE}")
    print(f"  尺寸: {screen_img.size} (宽x高)")
    print(f"  模式: {screen_img.mode}")
    print(f"  格式: {screen_img.format}")
    print()
    
    # 检查尺寸比例
    button_width, button_height = button_img.size
    screen_width, screen_height = screen_img.size
    
    print("分析:")
    print(f"  按钮占屏幕比例: {button_width/screen_width*100:.2f}% x {button_height/screen_height*100:.2f}%")
    
    if button_width > screen_width or button_height > screen_height:
        print("  ⚠️  按钮图像比屏幕还大！")
    elif button_width < 20 or button_height < 20:
        print("  ⚠️  按钮图像太小，可能识别困难")
    else:
        print("  ✅ 按钮尺寸合理")
    
    print()
    print("建议:")
    print("1. 确保 FortiClient 窗口可见")
    print("2. 确保窗口处于'未连接'状态（显示连接按钮）")
    print("3. 如果窗口状态不同，重新捕获按钮图像")
    print("4. 查看截图文件确认:")
    print(f"   - 按钮图像: {BUTTON_IMAGE}")
    print(f"   - 屏幕截图: {SCREEN_IMAGE}")

if __name__ == "__main__":
    analyze_images()
