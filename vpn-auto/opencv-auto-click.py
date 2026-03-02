#!/usr/bin/env python3
"""
使用 OpenCV 模板匹配 + xdotool 点击
更可靠的 GUI 自动化方案
"""

import cv2
import numpy as np
import os
import time
import subprocess

# 配置
SCREENSHOT = "screen.png"
TEMPLATE = "images/saml_login_button.png"
THRESHOLD = 0.7  # 匹配精度（0~1），降低以提高识别率
DISPLAY = ":1"

def log(message):
    """打印日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def take_screenshot():
    """使用 scrot 截图"""
    os.environ['DISPLAY'] = DISPLAY
    result = subprocess.run(["scrot", SCREENSHOT], capture_output=True)
    if result.returncode == 0:
        log(f"✅ 截图已保存: {SCREENSHOT}")
        return True
    else:
        log(f"❌ 截图失败: {result.stderr.decode()}")
        return False

def find_button():
    """使用 OpenCV 模板匹配查找按钮"""
    if not os.path.exists(SCREENSHOT):
        log(f"❌ 截图文件不存在: {SCREENSHOT}")
        return None
    
    if not os.path.exists(TEMPLATE):
        log(f"❌ 模板文件不存在: {TEMPLATE}")
        return None
    
    # 读取图像
    screen = cv2.imread(SCREENSHOT)
    template = cv2.imread(TEMPLATE)
    
    if screen is None:
        log(f"❌ 无法读取截图: {SCREENSHOT}")
        return None
    
    if template is None:
        log(f"❌ 无法读取模板: {TEMPLATE}")
        return None
    
    log(f"屏幕尺寸: {screen.shape[1]}x{screen.shape[0]}")
    log(f"模板尺寸: {template.shape[1]}x{template.shape[0]}")
    
    # 模板匹配
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    log(f"匹配度: {max_val:.3f} (阈值: {THRESHOLD})")
    
    if max_val < THRESHOLD:
        log(f"❌ 匹配度过低，未找到按钮")
        return None
    
    # 计算按钮中心坐标
    h, w, _ = template.shape
    center_x = max_loc[0] + w // 2
    center_y = max_loc[1] + h // 2
    
    log(f"✅ 找到按钮位置: ({center_x}, {center_y})")
    log(f"   左上角: {max_loc}")
    log(f"   尺寸: {w}x{h}")
    
    return center_x, center_y

def click(x, y):
    """使用 xdotool 点击"""
    os.environ['DISPLAY'] = DISPLAY
    
    # 移动鼠标
    log(f"移动鼠标到 ({x}, {y})...")
    subprocess.run(["xdotool", "mousemove", str(x), str(y)])
    time.sleep(0.3)
    
    # 点击
    log(f"点击...")
    subprocess.run(["xdotool", "click", "1"])
    time.sleep(0.5)
    
    log(f"✅ 已点击坐标 ({x}, {y})")

def main():
    """主函数"""
    log("========================================")
    log("OpenCV 模板匹配 + xdotool 自动点击")
    log("========================================")
    log("")
    
    # 1. 截图
    log("步骤 1: 截取屏幕...")
    if not take_screenshot():
        return False
    log("")
    
    # 2. 查找按钮
    log("步骤 2: 查找按钮...")
    pos = find_button()
    if not pos:
        return False
    log("")
    
    # 3. 点击
    log("步骤 3: 点击按钮...")
    click(*pos)
    log("")
    
    log("========================================")
    log("✅ 操作完成")
    log("========================================")
    log("")
    log("请检查 FortiClient 窗口是否有反应")
    log("如果需要 MFA 认证，请在手机上完成")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
