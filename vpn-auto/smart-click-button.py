#!/usr/bin/env python3
"""
智能点击 SAML login 按钮
1. 先查找按钮位置
2. 检查光标是否在按钮上方
3. 如果不在，移动到按钮上方
4. 点击按钮
"""

import sys
import os
import time

try:
    import pyautogui
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUTTON_IMAGE = os.path.join(SCRIPT_DIR, "images", "saml_login_button.png")
CONFIDENCE = 0.7

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"

def log(message):
    """打印日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def is_cursor_on_button(cursor_x, cursor_y, button_box):
    """检查光标是否在按钮区域内"""
    left, top, width, height = button_box.left, button_box.top, button_box.width, button_box.height
    right = left + width
    bottom = top + height
    
    return left <= cursor_x <= right and top <= cursor_y <= bottom

def smart_click():
    """智能点击按钮"""
    log("========================================")
    log("智能点击 SAML login 按钮")
    log("========================================")
    
    # 检查按钮图像
    if not os.path.exists(BUTTON_IMAGE):
        log(f"❌ 按钮图像不存在: {BUTTON_IMAGE}")
        return False
    
    log(f"✅ 按钮图像: {BUTTON_IMAGE}")
    
    # 1. 查找按钮位置
    log("步骤 1: 查找按钮位置...")
    try:
        location = pyautogui.locateOnScreen(
            BUTTON_IMAGE,
            confidence=CONFIDENCE,
            grayscale=True
        )
        
        if not location:
            log("❌ 未找到按钮")
            return False
        
        # 获取按钮中心坐标
        button_x, button_y = pyautogui.center(location)
        log(f"✅ 找到按钮")
        log(f"   位置: ({button_x}, {button_y})")
        log(f"   区域: Box(left={location.left}, top={location.top}, width={location.width}, height={location.height})")
        
        # 2. 获取当前光标位置
        log("")
        log("步骤 2: 检查光标位置...")
        cursor_x, cursor_y = pyautogui.position()
        log(f"当前光标: ({cursor_x}, {cursor_y})")
        
        # 3. 检查光标是否在按钮上
        is_on_button = is_cursor_on_button(cursor_x, cursor_y, location)
        
        if is_on_button:
            log("✅ 光标已在按钮上方")
        else:
            log("⚠️  光标不在按钮上方")
            log("")
            log("步骤 3: 移动光标到按钮...")
            
            # 移动光标到按钮中心
            pyautogui.moveTo(button_x, button_y, duration=0.5)
            time.sleep(0.3)
            
            # 验证移动
            new_cursor_x, new_cursor_y = pyautogui.position()
            log(f"✅ 光标已移动到: ({new_cursor_x}, {new_cursor_y})")
            
            # 再次检查
            if not is_cursor_on_button(new_cursor_x, new_cursor_y, location):
                log("⚠️  光标移动后仍不在按钮上，但继续尝试点击...")
        
        # 4. 点击按钮
        log("")
        log("步骤 4: 点击按钮...")
        pyautogui.click(button_x, button_y)
        time.sleep(0.5)
        
        log("✅ 已点击按钮")
        log("")
        log("========================================")
        log("✅ 操作完成")
        log("========================================")
        log("")
        log("请检查 FortiClient 窗口是否有反应")
        log("如果需要 MFA 认证，请在手机上完成")
        
        return True
        
    except Exception as e:
        log(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup()
    success = smart_click()
    sys.exit(0 if success else 1)
