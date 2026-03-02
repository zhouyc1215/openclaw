#!/usr/bin/env python3
"""
在 FortiClient GUI 中查找并点击 Connect 按钮
"""

import cv2
import numpy as np
import subprocess
import time
import pytesseract
from PIL import Image

DISPLAY = ":1"
SCREENSHOT = "forticlient-gui.png"

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def take_screenshot():
    """截图"""
    subprocess.run(["scrot", SCREENSHOT], env={"DISPLAY": DISPLAY})
    return SCREENSHOT

def find_connect_button_by_text(img):
    """使用 OCR 查找 Connect 按钮"""
    log("使用 OCR 查找 Connect 按钮...")
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # OCR 识别
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    
    # 查找包含 "Connect" 的文本
    for i, text in enumerate(data['text']):
        if 'connect' in text.lower() or 'conn' in text.lower():
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            
            if w > 30 and h > 15:  # 过滤太小的文本
                center_x = x + w // 2
                center_y = y + h // 2
                log(f"找到文本 '{text}' 在 ({center_x}, {center_y})")
                return (center_x, center_y)
    
    return None

def find_button_by_color(img):
    """通过颜色查找按钮（绿色或蓝色）"""
    log("通过颜色查找按钮...")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 绿色范围（Connect 按钮可能是绿色）
    green_lower = np.array([40, 40, 40])
    green_upper = np.array([80, 255, 255])
    
    # 蓝色范围
    blue_lower = np.array([100, 100, 100])
    blue_upper = np.array([130, 255, 255])
    
    # 查找绿色和蓝色区域
    green_mask = cv2.inRange(hsv, green_lower, green_upper)
    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
    
    mask = cv2.bitwise_or(green_mask, blue_mask)
    
    # 形态学处理
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 查找最大的按钮形状的区域
    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        
        # 按钮通常是矩形，宽度 > 高度
        if 1000 < area < 20000 and 50 < w < 200 and 20 < h < 60:
            center_x = x + w // 2
            center_y = y + h // 2
            candidates.append((center_x, center_y, area))
            log(f"找到候选按钮: ({center_x}, {center_y}), 面积={area}")
    
    if candidates:
        # 返回面积最大的
        candidates.sort(key=lambda c: c[2], reverse=True)
        return (candidates[0][0], candidates[0][1])
    
    return None

def click_position(x, y):
    """点击指定位置"""
    log(f"点击位置 ({x}, {y})...")
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    subprocess.run(["xdotool", "click", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    log("✅ 已点击")

def main():
    log("=" * 60)
    log("查找并点击 FortiClient Connect 按钮")
    log("=" * 60)
    log("")
    
    # 截图
    log("截图...")
    screenshot_path = take_screenshot()
    img = cv2.imread(screenshot_path)
    if img is None:
        log("❌ 无法读取截图")
        return False
    log(f"✅ 截图成功: {img.shape[1]}x{img.shape[0]}")
    log("")
    
    # 方法1：OCR 查找
    position = find_connect_button_by_text(img)
    if position:
        log(f"✅ 通过 OCR 找到按钮")
        click_position(position[0], position[1])
        return True
    log("")
    
    # 方法2：颜色查找
    position = find_button_by_color(img)
    if position:
        log(f"✅ 通过颜色找到按钮")
        click_position(position[0], position[1])
        return True
    log("")
    
    log("❌ 未找到 Connect 按钮")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
