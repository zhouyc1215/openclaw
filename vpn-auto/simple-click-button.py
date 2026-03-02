#!/usr/bin/env python3
"""
简化版：假设 FortiClient 已经运行，只执行按钮点击
"""

import cv2
import numpy as np
import os
import time
import subprocess

# 配置
SCREENSHOT = "screen.png"
DISPLAY = ":1"

# 深蓝色的 HSV 范围
BLUE_LOWER = np.array([100, 100, 100])
BLUE_UPPER = np.array([130, 255, 255])

# 按钮尺寸范围
MIN_BUTTON_AREA = 2000
MAX_BUTTON_AREA = 50000
MIN_BUTTON_WIDTH = 80
MAX_BUTTON_WIDTH = 300
MIN_BUTTON_HEIGHT = 25
MAX_BUTTON_HEIGHT = 80

def log(message):
    """打印日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_forticlient_running():
    """检查 FortiClient 是否运行"""
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        return result.returncode == 0 and result.stdout.strip()
    except Exception:
        return False

def resize_window_if_needed():
    """如果窗口太小，调整大小"""
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip().split('\n')[0]
            
            # 获取窗口大小
            geom_result = subprocess.run(
                ["xdotool", "getwindowgeometry", window_id],
                capture_output=True,
                text=True,
                env={"DISPLAY": DISPLAY}
            )
            
            # 检查是否需要调整
            if "10x10" in geom_result.stdout or "Geometry: 10" in geom_result.stdout:
                log("窗口太小，调整大小...")
                subprocess.run(["xdotool", "windowmove", window_id, "100", "100"], env={"DISPLAY": DISPLAY})
                time.sleep(0.3)
                subprocess.run(["xdotool", "windowsize", window_id, "1200", "800"], env={"DISPLAY": DISPLAY})
                time.sleep(0.5)
                log("✅ 窗口已调整")
                return True
            else:
                log("窗口大小正常")
                return True
    except Exception as e:
        log(f"⚠️  调整窗口失败: {e}")
    
    return False

def take_screenshot():
    """截图"""
    os.environ['DISPLAY'] = DISPLAY
    result = subprocess.run(["scrot", SCREENSHOT], capture_output=True)
    return result.returncode == 0

def find_button(img):
    """查找按钮"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    screen_center_x = img.shape[1] // 2
    screen_center_y = img.shape[0] // 2
    
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        
        if (MIN_BUTTON_AREA <= area <= MAX_BUTTON_AREA and
            MIN_BUTTON_WIDTH <= w <= MAX_BUTTON_WIDTH and
            MIN_BUTTON_HEIGHT <= h <= MAX_BUTTON_HEIGHT):
            
            center_x = x + w // 2
            center_y = y + h // 2
            distance = np.sqrt((center_x - screen_center_x)**2 + (center_y - screen_center_y)**2)
            
            candidates.append({
                'x': x, 'y': y, 'w': w, 'h': h,
                'center_x': center_x, 'center_y': center_y,
                'distance': distance
            })
    
    candidates.sort(key=lambda c: c['distance'])
    return candidates[0] if candidates else None

def click_button(x, y):
    """点击按钮"""
    os.environ['DISPLAY'] = DISPLAY
    
    # 移动光标
    log(f"移动光标到 ({x}, {y})...")
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], env={"DISPLAY": DISPLAY})
    time.sleep(1.0)
    
    # 点击
    log(f"点击...")
    subprocess.run(["xdotool", "click", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    
    # 按 Enter
    log(f"按 Enter...")
    subprocess.run(["xdotool", "key", "Return"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    
    log(f"✅ 已点击并按 Enter")

def main():
    log("=" * 60)
    log("简化版按钮点击脚本")
    log("=" * 60)
    log("")
    
    # 1. 检查 FortiClient 是否运行
    log("检查 FortiClient...")
    if not check_forticlient_running():
        log("❌ FortiClient 未运行")
        log("请先手动启动 FortiClient GUI")
        return False
    log("✅ FortiClient 正在运行")
    log("")
    
    # 2. 调整窗口大小（如果需要）
    log("检查窗口大小...")
    resize_window_if_needed()
    log("")
    
    # 3. 截图
    log("截图...")
    if not take_screenshot():
        log("❌ 截图失败")
        return False
    log("✅ 截图成功")
    log("")
    
    # 4. 查找按钮
    log("查找按钮...")
    img = cv2.imread(SCREENSHOT)
    if img is None:
        log("❌ 无法读取截图")
        return False
    
    button = find_button(img)
    if not button:
        log("❌ 未找到按钮")
        return False
    
    log(f"✅ 找到按钮: ({button['center_x']}, {button['center_y']})")
    log("")
    
    # 5. 点击按钮
    log("点击按钮...")
    click_button(button['center_x'], button['center_y'])
    log("")
    
    log("=" * 60)
    log("✅ 完成")
    log("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
