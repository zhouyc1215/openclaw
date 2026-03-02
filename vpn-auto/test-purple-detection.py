#!/usr/bin/env python3
"""
测试紫色按钮检测
"""

import cv2
import numpy as np

SCREENSHOT = "screen.png"

# 紫色的 HSV 范围
PURPLE_LOWER = np.array([140, 200, 50])
PURPLE_UPPER = np.array([160, 255, 150])

def main():
    print("测试紫色按钮检测...")
    print("")
    
    img = cv2.imread(SCREENSHOT)
    if img is None:
        print("❌ 无法读取截图")
        return
    
    print(f"截图尺寸: {img.shape[1]}x{img.shape[0]}")
    print("")
    
    # 转换到 HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 查找紫色区域
    mask = cv2.inRange(hsv, PURPLE_LOWER, PURPLE_UPPER)
    
    # 形态学处理
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"找到 {len(contours)} 个紫色区域")
    print("")
    
    for i, contour in enumerate(contours[:10], 1):
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        center_x = x + w // 2
        center_y = y + h // 2
        
        print(f"{i}. 位置: ({x}, {y}), 尺寸: {w}x{h}, 面积: {area:.0f}, 中心: ({center_x}, {center_y})")
        
        if area >= 2000 and w >= 80 and h >= 25:
            print(f"   ✅ 符合按钮条件")
        else:
            print(f"   ❌ 不符合按钮条件")

if __name__ == "__main__":
    main()
