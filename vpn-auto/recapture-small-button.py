#!/usr/bin/env python3
"""
重新捕获更小的按钮区域
使用之前成功识别的坐标 (942, 787)
"""

import os
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")
FULLSCREEN_PATH = os.path.join(SCRIPT_DIR, "fullscreen_saml.png")

# 之前成功识别的按钮中心坐标
CENTER_X = 942
CENTER_Y = 787

# 定义更小的按钮区域
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 35

def recapture():
    """重新捕获小按钮区域"""
    print("重新捕获更小的按钮区域...")
    
    if not os.path.exists(FULLSCREEN_PATH):
        print(f"❌ 全屏截图不存在: {FULLSCREEN_PATH}")
        print("请先运行: ./capture-saml-auto.sh")
        return False
    
    # 打开全屏截图
    img = Image.open(FULLSCREEN_PATH)
    
    # 计算按钮区域
    left = CENTER_X - BUTTON_WIDTH // 2
    top = CENTER_Y - BUTTON_HEIGHT // 2
    right = CENTER_X + BUTTON_WIDTH // 2
    bottom = CENTER_Y + BUTTON_HEIGHT // 2
    
    print(f"按钮中心: ({CENTER_X}, {CENTER_Y})")
    print(f"捕获区域: 左上({left}, {top}) 右下({right}, {bottom})")
    print(f"区域尺寸: {BUTTON_WIDTH}x{BUTTON_HEIGHT}")
    
    # 裁剪
    button_img = img.crop((left, top, right, bottom))
    
    # 保存
    output_path = os.path.join(IMAGES_DIR, "saml_button_small.png")
    button_img.save(output_path, "PNG")
    
    print(f"✅ 小按钮图像已保存: {output_path}")
    print(f"   尺寸: {button_img.width}x{button_img.height}")
    
    return True

if __name__ == "__main__":
    recapture()
