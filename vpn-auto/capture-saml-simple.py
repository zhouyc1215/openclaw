#!/usr/bin/env python3
"""
手动捕获 FortiClient "SAML login" 按钮
简化版本，不依赖 OCR
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
    
    # 创建 images 目录
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

def capture_saml_button():
    """手动捕获 SAML login 按钮"""
    print("========================================")
    print("捕获 SAML login 按钮")
    print("========================================")
    print()
    print("使用说明：")
    print("1. 确保 FortiClient 窗口已打开并显示 SAML login 按钮")
    print("2. 将鼠标移动到按钮的中心位置")
    print("3. 等待 3 秒，脚本会自动捕获按钮")
    print()
    
    input("准备好后按 Enter 开始...")
    
    # 获取屏幕尺寸
    try:
        screen_width, screen_height = pyautogui.size()
        print(f"屏幕尺寸: {screen_width}x{screen_height}")
    except Exception as e:
        print(f"警告：无法获取屏幕尺寸: {e}")
        screen_width, screen_height = 1920, 1080
    
    # 获取按钮中心坐标
    print()
    print("将鼠标移动到 SAML login 按钮的中心位置...")
    print("（脚本会自动扩展捕获区域）")
    time.sleep(3)
    center_x, center_y = pyautogui.position()
    print(f"按钮中心坐标: ({center_x}, {center_y})")
    
    # 自动计算按钮区域（假设按钮大小约为 150x40）
    button_width = 150
    button_height = 40
    
    x1 = center_x - button_width // 2
    y1 = center_y - button_height // 2
    x2 = center_x + button_width // 2
    y2 = center_y + button_height // 2
    
    print(f"自动计算区域: 左上({x1}, {y1}) 右下({x2}, {y2})")
    
    # 确保坐标顺序正确
    left = min(x1, x2)
    top = min(y1, y2)
    right = max(x1, x2)
    bottom = max(y1, y2)
    width = right - left
    height = bottom - top
    
    # 验证坐标
    if left < 0 or top < 0 or right > screen_width or bottom > screen_height:
        print()
        print(f"错误：坐标超出屏幕范围")
        print(f"  左上角: ({left}, {top})")
        print(f"  右下角: ({right}, {bottom})")
        print(f"  屏幕尺寸: {screen_width}x{screen_height}")
        return
    
    if width < 10 or height < 10:
        print()
        print(f"错误：捕获区域太小 ({width}x{height})")
        return
    
    print()
    print(f"捕获区域: 左上({left}, {top}) 右下({right}, {bottom}) 尺寸({width}x{height})")
    
    # 截图
    print("正在截图...")
    try:
        # 先截取全屏，然后裁剪
        full_screenshot = pyautogui.screenshot()
        cropped = full_screenshot.crop((left, top, right, bottom))
        
        # 保存图像
        output_path = os.path.join(IMAGES_DIR, "saml_login_button.png")
        cropped.save(output_path, "PNG")
        
        print()
        print(f"✅ SAML login 按钮图像已保存: {output_path}")
        print(f"   图像尺寸: {width}x{height}")
        print()
        print("现在可以使用此图像进行自动点击")
    except Exception as e:
        print()
        print(f"❌ 保存图像失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup()
    capture_saml_button()
