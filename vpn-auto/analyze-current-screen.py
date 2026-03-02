#!/usr/bin/env python3
"""
分析当前截图，查找蓝色按钮
"""

import cv2
import numpy as np

# 配置
SCREENSHOT = "screen.png"

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

def main():
    print("读取截图...")
    img = cv2.imread(SCREENSHOT)
    if img is None:
        print("❌ 无法读取截图")
        return
    
    print(f"截图尺寸: {img.shape[1]}x{img.shape[0]}")
    print("")
    
    # 转换到 HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 查找蓝色区域
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    
    # 形态学处理
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"找到 {len(contours)} 个蓝色区域")
    print("")
    
    # 分析所有轮廓
    screen_center_x = img.shape[1] // 2
    screen_center_y = img.shape[0] // 2
    
    candidates = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        
        center_x = x + w // 2
        center_y = y + h // 2
        distance = np.sqrt((center_x - screen_center_x)**2 + (center_y - screen_center_y)**2)
        
        print(f"区域 {i+1}:")
        print(f"  位置: ({x}, {y})")
        print(f"  尺寸: {w}x{h}")
        print(f"  面积: {area:.0f}")
        print(f"  中心: ({center_x}, {center_y})")
        print(f"  距屏幕中心: {distance:.0f}")
        
        # 检查是否符合按钮条件
        if (MIN_BUTTON_AREA <= area <= MAX_BUTTON_AREA and
            MIN_BUTTON_WIDTH <= w <= MAX_BUTTON_WIDTH and
            MIN_BUTTON_HEIGHT <= h <= MAX_BUTTON_HEIGHT):
            print(f"  ✅ 符合按钮条件")
            candidates.append({
                'x': x, 'y': y, 'w': w, 'h': h,
                'center_x': center_x, 'center_y': center_y,
                'distance': distance
            })
        else:
            reasons = []
            if area < MIN_BUTTON_AREA:
                reasons.append(f"面积太小 (< {MIN_BUTTON_AREA})")
            elif area > MAX_BUTTON_AREA:
                reasons.append(f"面积太大 (> {MAX_BUTTON_AREA})")
            if w < MIN_BUTTON_WIDTH:
                reasons.append(f"宽度太小 (< {MIN_BUTTON_WIDTH})")
            elif w > MAX_BUTTON_WIDTH:
                reasons.append(f"宽度太大 (> {MAX_BUTTON_WIDTH})")
            if h < MIN_BUTTON_HEIGHT:
                reasons.append(f"高度太小 (< {MIN_BUTTON_HEIGHT})")
            elif h > MAX_BUTTON_HEIGHT:
                reasons.append(f"高度太大 (> {MAX_BUTTON_HEIGHT})")
            print(f"  ❌ 不符合: {', '.join(reasons)}")
        
        print("")
    
    print("=" * 60)
    if candidates:
        candidates.sort(key=lambda c: c['distance'])
        best = candidates[0]
        print(f"✅ 找到 {len(candidates)} 个候选按钮")
        print(f"最佳候选: ({best['center_x']}, {best['center_y']})")
    else:
        print("❌ 未找到符合条件的按钮")
    print("=" * 60)

if __name__ == "__main__":
    main()
