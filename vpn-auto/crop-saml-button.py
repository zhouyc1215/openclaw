#!/usr/bin/env python3
"""
从全屏截图中裁剪 SAML login 按钮区域
"""

import os
import sys
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FULLSCREEN_PATH = os.path.join(SCRIPT_DIR, "fullscreen_saml.png")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "images", "saml_login_button.png")

def crop_button():
    """裁剪按钮区域"""
    if not os.path.exists(FULLSCREEN_PATH):
        print(f"❌ 全屏截图不存在: {FULLSCREEN_PATH}")
        return False
    
    # 打开图像
    img = Image.open(FULLSCREEN_PATH)
    width, height = img.size
    
    print(f"图像尺寸: {width}x{height}")
    
    # 计算按钮区域（中央下方）
    button_left = int(width * 0.3)
    button_top = int(height * 0.6)
    button_right = int(width * 0.7)
    button_bottom = int(height * 0.9)
    
    print(f"按钮区域: 左上({button_left}, {button_top}) 右下({button_right}, {button_bottom})")
    
    # 裁剪
    button_img = img.crop((button_left, button_top, button_right, button_bottom))
    
    # 保存
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    button_img.save(OUTPUT_PATH, "PNG")
    
    print(f"✅ 按钮区域已保存: {OUTPUT_PATH}")
    print(f"   尺寸: {button_img.width}x{button_img.height}")
    
    return True

if __name__ == "__main__":
    crop_button()
