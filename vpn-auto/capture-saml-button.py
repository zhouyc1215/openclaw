#!/usr/bin/env python3
"""
自动捕获 FortiClient "SAML login" 按钮
使用 OCR 文字识别自动定位按钮位置
"""

import sys
import os
import time

try:
    import pyautogui
    from PIL import Image
    import pytesseract
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    print("请运行: pip3 install --user pytesseract")
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

def find_text_on_screen(text_to_find):
    """在屏幕上查找指定文字"""
    print(f"在屏幕上查找文字: '{text_to_find}'")
    
    # 截取全屏
    screenshot = pyautogui.screenshot()
    
    # 保存调试截图
    debug_path = os.path.join(SCRIPT_DIR, "saml_screen.png")
    screenshot.save(debug_path)
    print(f"屏幕截图已保存: {debug_path}")
    
    # 使用 OCR 识别文字
    print("正在进行 OCR 文字识别...")
    try:
        # 获取所有文字及其位置
        data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
        
        # 查找匹配的文字
        n_boxes = len(data['text'])
        matches = []
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text_to_find.lower() in text.lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = data['conf'][i]
                
                print(f"找到匹配文字: '{text}' 在位置 ({x}, {y}) 尺寸 ({w}x{h}) 置信度 {conf}")
                matches.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'conf': conf
                })
        
        return matches, screenshot
    except Exception as e:
        print(f"OCR 识别失败: {e}")
        return [], screenshot

def capture_button_area(screenshot, x, y, width, height, padding=20):
    """截取按钮区域（带边距）"""
    # 添加边距
    left = max(0, x - padding)
    top = max(0, y - padding)
    right = min(screenshot.width, x + width + padding)
    bottom = min(screenshot.height, y + height + padding)
    
    # 裁剪图像
    button_img = screenshot.crop((left, top, right, bottom))
    
    return button_img, (left, top, right, bottom)

def auto_capture_saml_button():
    """自动捕获 SAML login 按钮"""
    print("========================================")
    print("自动捕获 SAML login 按钮")
    print("========================================")
    print()
    
    # 查找 "SAML" 或 "login" 文字
    search_terms = ["SAML", "login", "SAML login"]
    
    all_matches = []
    screenshot = None
    
    for term in search_terms:
        matches, screenshot = find_text_on_screen(term)
        all_matches.extend(matches)
    
    if not all_matches:
        print()
        print("❌ 未找到 SAML login 按钮")
        print()
        print("可能的原因：")
        print("1. FortiClient 窗口未打开")
        print("2. 窗口被遮挡或最小化")
        print("3. 当前不在 SAML 登录界面")
        print("4. tesseract OCR 未正确安装")
        print()
        print("请确保：")
        print("1. FortiClient 窗口打开并可见")
        print("2. 显示 SAML login 按钮")
        print("3. 然后重新运行此脚本")
        return
    
    print()
    print(f"找到 {len(all_matches)} 个匹配项")
    print()
    
    # 选择最佳匹配（置信度最高的）
    best_match = max(all_matches, key=lambda m: m['conf'])
    
    print(f"选择最佳匹配: '{best_match['text']}'")
    print(f"  位置: ({best_match['x']}, {best_match['y']})")
    print(f"  尺寸: {best_match['width']}x{best_match['height']}")
    print(f"  置信度: {best_match['conf']}")
    print()
    
    # 截取按钮区域
    button_img, coords = capture_button_area(
        screenshot,
        best_match['x'],
        best_match['y'],
        best_match['width'],
        best_match['height'],
        padding=30  # 增加边距以包含整个按钮
    )
    
    # 保存按钮图像
    output_path = os.path.join(IMAGES_DIR, "saml_login_button.png")
    button_img.save(output_path, "PNG")
    
    print(f"✅ SAML login 按钮图像已保存: {output_path}")
    print(f"   截取区域: 左上({coords[0]}, {coords[1]}) 右下({coords[2]}, {coords[3]})")
    print(f"   图像尺寸: {button_img.width}x{button_img.height}")
    print()
    print("现在可以使用此图像进行自动点击")

def manual_capture():
    """手动捕获模式（如果 OCR 失败）"""
    print("========================================")
    print("手动捕获 SAML login 按钮")
    print("========================================")
    print()
    print("使用说明：")
    print("1. 确保 FortiClient 窗口已打开并显示 SAML login 按钮")
    print("2. 将鼠标移动到按钮的左上角")
    print("3. 按 Enter 键记录第一个坐标")
    print("4. 将鼠标移动到按钮的右下角")
    print("5. 按 Enter 键记录第二个坐标并截图")
    print()
    
    input("准备好后按 Enter 开始...")
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    print(f"屏幕尺寸: {screen_width}x{screen_height}")
    
    # 获取第一个坐标（左上角）
    print()
    print("将鼠标移动到 SAML login 按钮的左上角...")
    time.sleep(2)
    x1, y1 = pyautogui.position()
    print(f"左上角坐标: ({x1}, {y1})")
    input("按 Enter 继续...")
    
    # 获取第二个坐标（右下角）
    print()
    print("将鼠标移动到 SAML login 按钮的右下角...")
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
    
    print()
    print(f"捕获区域: 左上({left}, {top}) 右下({right}, {bottom}) 尺寸({width}x{height})")
    
    # 截图
    print("正在截图...")
    try:
        full_screenshot = pyautogui.screenshot()
        cropped = full_screenshot.crop((left, top, right, bottom))
        
        # 保存图像
        output_path = os.path.join(IMAGES_DIR, "saml_login_button.png")
        cropped.save(output_path, "PNG")
        
        print()
        print(f"✅ SAML login 按钮图像已保存: {output_path}")
        print(f"   图像尺寸: {width}x{height}")
    except Exception as e:
        print()
        print(f"❌ 保存图像失败: {e}")

if __name__ == "__main__":
    setup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        manual_capture()
    else:
        # 检查 tesseract 是否安装
        try:
            pytesseract.get_tesseract_version()
            auto_capture_saml_button()
        except Exception as e:
            print(f"⚠️  tesseract OCR 未安装或配置错误: {e}")
            print()
            print("切换到手动模式...")
            print()
            manual_capture()
