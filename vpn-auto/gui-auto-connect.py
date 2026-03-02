#!/usr/bin/env python3
"""
FortiClient GUI 自动化脚本
使用图像识别自动点击连接按钮
"""

import sys
import time
import subprocess
import os

try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"错误：缺少依赖库 - {e}")
    print("请运行: ./install-gui-automation.sh")
    sys.exit(1)

# 配置
DISPLAY = ":1"
CONFIDENCE = 0.7  # 降低置信度以提高 SAML 按钮识别率
MAX_RETRIES = 5   # 增加重试次数
RETRY_DELAY = 2

# 图像路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")

def log(message):
    """打印日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def setup_display():
    """设置 DISPLAY 环境变量"""
    os.environ['DISPLAY'] = DISPLAY
    log(f"设置 DISPLAY={DISPLAY}")

def take_screenshot(filename="screenshot.png"):
    """截取屏幕截图"""
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        log(f"截图已保存: {filename}")
        return True
    except Exception as e:
        log(f"截图失败: {e}")
        return False

def find_image_on_screen(image_path, confidence=CONFIDENCE):
    """
    在屏幕上查找图像
    返回: (x, y) 坐标或 None
    """
    try:
        location = pyautogui.locateOnScreen(
            image_path, 
            confidence=confidence,
            grayscale=True  # 使用灰度模式提高识别速度
        )
        if location:
            # 获取中心点坐标
            x, y = pyautogui.center(location)
            log(f"找到图像 {os.path.basename(image_path)} 在位置: ({x}, {y})")
            return (x, y)
        else:
            log(f"未找到图像: {os.path.basename(image_path)}")
            return None
    except Exception as e:
        log(f"图像识别失败: {e}")
        return None

def click_at(x, y):
    """点击指定坐标"""
    try:
        pyautogui.click(x, y)
        log(f"点击坐标: ({x}, {y})")
        return True
    except Exception as e:
        log(f"点击失败: {e}")
        return False

def click_image(image_path, confidence=CONFIDENCE):
    """查找并点击图像"""
    location = find_image_on_screen(image_path, confidence)
    if location:
        x, y = location
        return click_at(x, y)
    return False

def is_forticlient_running():
    """检查 FortiClient 是否运行"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "fortitray"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        log(f"检查 FortiClient 失败: {e}")
        return False

def start_forticlient():
    """启动 FortiClient GUI"""
    if is_forticlient_running():
        log("FortiClient 已在运行")
        return True
    
    log("启动 FortiClient GUI...")
    try:
        subprocess.Popen(
            ["/opt/forticlient/fortitray"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
        
        if is_forticlient_running():
            log("✅ FortiClient GUI 已启动")
            return True
        else:
            log("❌ FortiClient GUI 启动失败")
            return False
    except Exception as e:
        log(f"启动 FortiClient 失败: {e}")
        return False

def auto_connect_vpn():
    """自动连接 VPN"""
    log("========================================")
    log("开始 VPN 自动连接")
    log("========================================")
    
    # 设置显示
    setup_display()
    
    # 确保 FortiClient 运行
    if not start_forticlient():
        log("❌ 无法启动 FortiClient")
        return False
    
    # 等待窗口加载
    time.sleep(2)
    
    # 检查按钮图像是否存在
    connect_images = [
        os.path.join(IMAGES_DIR, "saml_button_small.png"),   # 小的 SAML 按钮（最精确）
        os.path.join(IMAGES_DIR, "saml_login_button.png"),  # 大的 SAML 按钮
        os.path.join(IMAGES_DIR, "connect_button.png"),      # 普通连接按钮
    ]
    
    images_exist = any(os.path.exists(img) for img in connect_images)
    
    if not images_exist:
        log("❌ 连接按钮图像不存在")
        log("提示：请运行 capture-button.py 来捕获连接按钮图像")
        log("回退到命令行方式...")
        return False
    
    # 截图用于调试
    take_screenshot(os.path.join(SCRIPT_DIR, "debug_screen.png"))
    
    # 尝试查找并点击连接按钮
    for retry in range(MAX_RETRIES):
        log(f"尝试 {retry + 1}/{MAX_RETRIES}...")
        
        for image_path in connect_images:
            if not os.path.exists(image_path):
                continue
            
            if click_image(image_path):
                log("✅ 成功点击连接按钮")
                
                # 对于 SAML 按钮，点击一次就够了
                if "saml" in os.path.basename(image_path).lower():
                    log("✅ VPN 连接已触发（SAML 登录）")
                    log("请在手机上完成 MFA 认证")
                    return True
                
                # 对于普通按钮，检查 VPN 状态
                time.sleep(2)
                result = subprocess.run(
                    ["forticlient", "vpn", "status"],
                    capture_output=True,
                    text=True
                )
                
                if "Connecting" in result.stdout or "Connected" in result.stdout:
                    log("✅ VPN 连接已触发")
                    log("请在手机上完成 MFA 认证")
                    return True
        
        if retry < MAX_RETRIES - 1:
            log(f"等待 {RETRY_DELAY} 秒后重试...")
            time.sleep(RETRY_DELAY)
    
    log("❌ 未能找到连接按钮")
    return False

if __name__ == "__main__":
    success = auto_connect_vpn()
    sys.exit(0 if success else 1)
