#!/usr/bin/env python3
"""
自动点击 FortiClient SAML login 按钮
"""

import sys
import time
import os

try:
    import pyautogui
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUTTON_IMAGE = os.path.join(SCRIPT_DIR, "images", "saml_login_button.png")
CONFIDENCE = 0.7  # 降低置信度以提高识别率
MAX_RETRIES = 5
RETRY_DELAY = 2

def log(message):
    """打印日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def setup():
    """初始化"""
    os.environ['DISPLAY'] = ":1"
    log("设置 DISPLAY=:1")

def find_and_click_button():
    """查找并点击 SAML login 按钮"""
    log("========================================")
    log("开始查找 SAML login 按钮")
    log("========================================")
    
    # 检查按钮图像
    if not os.path.exists(BUTTON_IMAGE):
        log(f"❌ 按钮图像不存在: {BUTTON_IMAGE}")
        log("请先运行: ./capture-saml-auto.sh")
        return False
    
    log(f"✅ 按钮图像: {BUTTON_IMAGE}")
    
    # 尝试多次查找
    for attempt in range(1, MAX_RETRIES + 1):
        log(f"尝试 {attempt}/{MAX_RETRIES}...")
        
        try:
            # 截取当前屏幕
            screenshot = pyautogui.screenshot()
            debug_path = os.path.join(SCRIPT_DIR, "click_debug_screen.png")
            screenshot.save(debug_path)
            log(f"屏幕截图已保存: {debug_path}")
            
            # 查找按钮
            location = pyautogui.locateOnScreen(
                BUTTON_IMAGE,
                confidence=CONFIDENCE,
                grayscale=True
            )
            
            if location:
                # 获取中心点
                x, y = pyautogui.center(location)
                log(f"✅ 找到按钮！位置: ({x}, {y})")
                log(f"   区域: {location}")
                
                # 点击按钮
                log(f"点击坐标: ({x}, {y})")
                pyautogui.click(x, y)
                
                log("✅ 成功点击 SAML login 按钮")
                log("请在手机上完成 MFA 认证")
                return True
            else:
                log(f"❌ 未找到按钮（置信度: {CONFIDENCE}）")
                
                if attempt < MAX_RETRIES:
                    log(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
        
        except Exception as e:
            log(f"❌ 识别失败: {e}")
            
            if attempt < MAX_RETRIES:
                log(f"等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
    
    log("❌ 所有尝试都失败了")
    log("")
    log("可能的原因：")
    log("1. FortiClient 窗口未打开或被遮挡")
    log("2. 当前不在 SAML 登录界面")
    log("3. 按钮图像需要重新捕获")
    log("")
    log("建议操作：")
    log("1. 确保 FortiClient 窗口可见")
    log("2. 确保显示 SAML login 按钮")
    log("3. 重新捕获按钮图像: ./capture-saml-auto.sh")
    log("4. 查看调试截图: click_debug_screen.png")
    
    return False

if __name__ == "__main__":
    setup()
    success = find_and_click_button()
    
    if success:
        log("")
        log("========================================")
        log("✅ VPN 连接已触发")
        log("========================================")
        sys.exit(0)
    else:
        log("")
        log("========================================")
        log("❌ VPN 连接失败")
        log("========================================")
        sys.exit(1)
