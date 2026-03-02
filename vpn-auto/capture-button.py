#!/usr/bin/env python3
"""
FortiClient 连接按钮图像捕获工具
用于捕获连接按钮的截图，供 GUI 自动化使用
"""

import sys
import time
import os

try:
    import pyautogui
    from PIL import Image
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    print("请运行: ./install-gui-automation.sh")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"
    
    # 创建 images 目录
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        print(f"创建目录: {IMAGES_DIR}")

def capture_region():
    """交互式捕获屏幕区域"""
    print("========================================")
    print("FortiClient 连接按钮捕获工具")
    print("========================================")
    print()
    print("使用说明：")
    print("1. 确保 FortiClient 窗口已打开")
    print("2. 将鼠标移动到连接按钮的左上角")
    print("3. 按 Enter 键记录第一个坐标")
    print("4. 将鼠标移动到连接按钮的右下角")
    print("5. 按 Enter 键记录第二个坐标并截图")
    print()
    
    input("准备好后按 Enter 开始...")
    
    # 获取屏幕尺寸
    try:
        screen_width, screen_height = pyautogui.size()
        print(f"屏幕尺寸: {screen_width}x{screen_height}")
    except Exception as e:
        print(f"警告：无法获取屏幕尺寸: {e}")
        screen_width, screen_height = 1920, 1080  # 默认值
    
    # 获取第一个坐标（左上角）
    print()
    print("将鼠标移动到连接按钮的左上角...")
    time.sleep(2)
    x1, y1 = pyautogui.position()
    print(f"左上角坐标: ({x1}, {y1})")
    input("按 Enter 继续...")
    
    # 获取第二个坐标（右下角）
    print()
    print("将鼠标移动到连接按钮的右下角...")
    time.sleep(2)
    x2, y2 = pyautogui.position()
    print(f"右下角坐标: ({x2}, {y2})")
    
    # 确保坐标顺序正确
    left = min(x1, x2)
    top = min(y1, y2)
    right = max(x1, x2)
    bottom = max(y1, y2)
    width = right - left
    height = bottom - top
    
    # 验证坐标在屏幕范围内
    if left < 0 or top < 0 or right > screen_width or bottom > screen_height:
        print()
        print(f"错误：坐标超出屏幕范围")
        print(f"  左上角: ({left}, {top})")
        print(f"  右下角: ({right}, {bottom})")
        print(f"  屏幕尺寸: {screen_width}x{screen_height}")
        return
    
    # 验证区域大小合理
    if width < 10 or height < 10:
        print()
        print(f"错误：捕获区域太小 ({width}x{height})")
        print("请确保选择了完整的按钮区域")
        return
    
    if width > 500 or height > 200:
        print()
        print(f"警告：捕获区域较大 ({width}x{height})")
        print("建议只捕获按钮本身，不要包含过多背景")
        response = input("是否继续？(y/n) ")
        if response.lower() != 'y':
            return
    
    print()
    print(f"捕获区域: 左上({left}, {top}) 右下({right}, {bottom}) 尺寸({width}x{height})")
    
    # 截图
    print("正在截图...")
    try:
        # 先截取全屏，然后裁剪（更安全的方式）
        full_screenshot = pyautogui.screenshot()
        
        # 裁剪到目标区域
        cropped = full_screenshot.crop((left, top, right, bottom))
        
        # 保存图像
        output_path = os.path.join(IMAGES_DIR, "connect_button.png")
        cropped.save(output_path, "PNG")
        
        print()
        print(f"✅ 连接按钮图像已保存: {output_path}")
        print(f"   图像尺寸: {width}x{height}")
        print()
        print("现在可以运行 gui-auto-connect.py 来测试自动连接")
    except Exception as e:
        print()
        print(f"❌ 保存图像失败: {e}")
        import traceback
        traceback.print_exc()
        print("请检查坐标是否正确")

def capture_fullscreen():
    """捕获全屏截图（用于调试）"""
    print("捕获全屏截图...")
    screenshot = pyautogui.screenshot()
    output_path = os.path.join(SCRIPT_DIR, "fullscreen.png")
    screenshot.save(output_path)
    print(f"✅ 全屏截图已保存: {output_path}")

if __name__ == "__main__":
    setup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fullscreen":
        capture_fullscreen()
    else:
        capture_region()
