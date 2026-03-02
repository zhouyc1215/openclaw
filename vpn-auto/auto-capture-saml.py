#!/usr/bin/env python3
"""
完全自动化捕获 FortiClient SAML login 按钮
无需手动操作，自动查找窗口并截图
"""

import sys
import os
import subprocess
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

def find_forticlient_window():
    """查找 FortiClient 窗口"""
    try:
        # 使用 xdotool 查找 FortiClient 窗口
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": ":1"}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_ids = result.stdout.strip().split('\n')
            print(f"找到 {len(window_ids)} 个 FortiClient 窗口")
            return window_ids[0]  # 返回第一个窗口
        else:
            print("未找到 FortiClient 窗口")
            return None
    except FileNotFoundError:
        print("xdotool 未安装，尝试其他方法...")
        return None
    except Exception as e:
        print(f"查找窗口失败: {e}")
        return None

def get_window_geometry(window_id):
    """获取窗口位置和大小"""
    try:
        result = subprocess.run(
            ["xdotool", "getwindowgeometry", window_id],
            capture_output=True,
            text=True,
            env={"DISPLAY": ":1"}
        )
        
        if result.returncode == 0:
            output = result.stdout
            # 解析输出
            # Position: 100,200 (screen: 0)
            # Geometry: 800x600
            
            for line in output.split('\n'):
                if 'Position:' in line:
                    pos = line.split('Position:')[1].split('(')[0].strip()
                    x, y = map(int, pos.split(','))
                elif 'Geometry:' in line:
                    geo = line.split('Geometry:')[1].strip()
                    width, height = map(int, geo.split('x'))
            
            return x, y, width, height
    except Exception as e:
        print(f"获取窗口几何信息失败: {e}")
    
    return None

def activate_window(window_id):
    """激活窗口（置于前台）"""
    try:
        subprocess.run(
            ["xdotool", "windowactivate", window_id],
            env={"DISPLAY": ":1"}
        )
        time.sleep(0.5)  # 等待窗口激活
        return True
    except Exception as e:
        print(f"激活窗口失败: {e}")
        return False

def capture_window_area(x, y, width, height):
    """截取窗口区域"""
    try:
        # 截取全屏
        screenshot = pyautogui.screenshot()
        
        # 裁剪到窗口区域
        window_img = screenshot.crop((x, y, x + width, y + height))
        
        return window_img
    except Exception as e:
        print(f"截取窗口失败: {e}")
        return None

def find_button_in_image(image):
    """在图像中查找按钮区域（基于颜色和位置启发式）"""
    # 假设 SAML login 按钮在窗口底部中央
    width, height = image.size
    
    # 按钮通常在底部 1/3 区域
    button_top = int(height * 0.6)
    button_bottom = height
    
    # 按钮通常在中央 1/2 区域
    button_left = int(width * 0.25)
    button_right = int(width * 0.75)
    
    # 截取可能包含按钮的区域
    button_area = image.crop((button_left, button_top, button_right, button_bottom))
    
    return button_area, (button_left, button_top, button_right, button_bottom)

def auto_capture():
    """完全自动化捕获"""
    print("========================================")
    print("自动捕获 SAML login 按钮")
    print("========================================")
    print()
    
    # 1. 查找 FortiClient 窗口
    print("步骤 1: 查找 FortiClient 窗口...")
    window_id = find_forticlient_window()
    
    if not window_id:
        print("❌ 未找到 FortiClient 窗口")
        print()
        print("尝试直接截取全屏...")
        return capture_fullscreen()
    
    print(f"✅ 找到窗口 ID: {window_id}")
    
    # 2. 获取窗口位置和大小
    print()
    print("步骤 2: 获取窗口几何信息...")
    geometry = get_window_geometry(window_id)
    
    if not geometry:
        print("❌ 无法获取窗口信息")
        print()
        print("尝试直接截取全屏...")
        return capture_fullscreen()
    
    x, y, width, height = geometry
    print(f"✅ 窗口位置: ({x}, {y})")
    print(f"✅ 窗口大小: {width}x{height}")
    
    # 3. 激活窗口
    print()
    print("步骤 3: 激活窗口...")
    if activate_window(window_id):
        print("✅ 窗口已激活")
    else:
        print("⚠️  窗口激活失败，继续尝试...")
    
    # 4. 截取窗口
    print()
    print("步骤 4: 截取窗口...")
    window_img = capture_window_area(x, y, width, height)
    
    if not window_img:
        print("❌ 截取窗口失败")
        return False
    
    # 保存完整窗口截图
    window_path = os.path.join(SCRIPT_DIR, "forticlient_window.png")
    window_img.save(window_path, "PNG")
    print(f"✅ 窗口截图已保存: {window_path}")
    
    # 5. 查找按钮区域
    print()
    print("步骤 5: 定位按钮区域...")
    button_img, coords = find_button_in_image(window_img)
    
    print(f"✅ 按钮区域: 左上({coords[0]}, {coords[1]}) 右下({coords[2]}, {coords[3]})")
    print(f"✅ 按钮尺寸: {button_img.width}x{button_img.height}")
    
    # 6. 保存按钮图像
    output_path = os.path.join(IMAGES_DIR, "saml_login_button.png")
    button_img.save(output_path, "PNG")
    
    print()
    print(f"✅ SAML login 按钮图像已保存: {output_path}")
    print()
    print("注意：此图像包含按钮可能所在的区域")
    print("如果自动识别不准确，请使用手动模式重新捕获")
    
    return True

def capture_fullscreen():
    """回退方案：截取全屏"""
    print()
    print("使用全屏截图方案...")
    
    try:
        # 截取全屏
        screenshot = pyautogui.screenshot()
        
        # 保存全屏截图
        fullscreen_path = os.path.join(SCRIPT_DIR, "fullscreen_saml.png")
        screenshot.save(fullscreen_path, "PNG")
        print(f"✅ 全屏截图已保存: {fullscreen_path}")
        
        # 假设按钮在屏幕中央下方
        width, height = screenshot.size
        
        # 截取中央下方区域
        button_left = int(width * 0.3)
        button_top = int(height * 0.6)
        button_right = int(width * 0.7)
        button_bottom = int(height * 0.9)
        
        button_img = screenshot.crop((button_left, button_top, button_right, button_bottom))
        
        # 保存按钮区域
        output_path = os.path.join(IMAGES_DIR, "saml_login_button.png")
        button_img.save(output_path, "PNG")
        
        print(f"✅ 按钮区域已保存: {output_path}")
        print(f"   区域: 左上({button_left}, {button_top}) 右下({button_right}, {button_bottom})")
        print()
        print("注意：使用了全屏截图的估算区域")
        print("如果不准确，请使用手动模式重新捕获")
        
        return True
    except Exception as e:
        print(f"❌ 全屏截图失败: {e}")
        return False

if __name__ == "__main__":
    setup()
    
    print("提示：确保 FortiClient 窗口已打开并显示 SAML login 按钮")
    print()
    
    # 等待 2 秒让用户准备
    print("2 秒后开始自动捕获...")
    time.sleep(2)
    
    success = auto_capture()
    
    if success:
        print()
        print("========================================")
        print("✅ 捕获完成")
        print("========================================")
    else:
        print()
        print("========================================")
        print("❌ 捕获失败")
        print("========================================")
        print()
        print("请尝试手动模式:")
        print("  python3 capture-saml-simple.py")
