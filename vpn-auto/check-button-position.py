#!/usr/bin/env python3
"""
检查特定位置的颜色和周围区域
"""

import cv2
import numpy as np

SCREENSHOT = "screen.png"
TARGET_X = 993
TARGET_Y = 723

def main():
    print(f"检查位置 ({TARGET_X}, {TARGET_Y}) 的颜色...")
    print("")
    
    img = cv2.imread(SCREENSHOT)
    if img is None:
        print("❌ 无法读取截图")
        return
    
    print(f"截图尺寸: {img.shape[1]}x{img.shape[0]}")
    print("")
    
    # 检查目标位置
    if TARGET_Y < img.shape[0] and TARGET_X < img.shape[1]:
        pixel_bgr = img[TARGET_Y, TARGET_X]
        pixel_rgb = pixel_bgr[::-1]
        
        # 转换到 HSV
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        pixel_hsv = hsv_img[TARGET_Y, TARGET_X]
        
        print(f"位置 ({TARGET_X}, {TARGET_Y}) 的颜色:")
        print(f"  BGR: {pixel_bgr}")
        print(f"  RGB: {pixel_rgb}")
        print(f"  HSV: {pixel_hsv}")
        print("")
        
        # 检查周围区域（100x100）
        y_start = max(0, TARGET_Y - 50)
        y_end = min(img.shape[0], TARGET_Y + 50)
        x_start = max(0, TARGET_X - 50)
        x_end = min(img.shape[1], TARGET_X + 50)
        
        region = img[y_start:y_end, x_start:x_end]
        hsv_region = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        
        # 统计颜色分布
        print(f"周围区域 ({x_start},{y_start}) 到 ({x_end},{y_end}):")
        print(f"  平均 BGR: {np.mean(region, axis=(0,1))}")
        print(f"  平均 HSV: {np.mean(hsv_region, axis=(0,1))}")
        print("")
        
        # 检查是否有蓝色
        blue_lower = np.array([100, 100, 100])
        blue_upper = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv_region, blue_lower, blue_upper)
        blue_pixels = np.sum(blue_mask > 0)
        
        print(f"蓝色像素数量: {blue_pixels} / {region.shape[0] * region.shape[1]}")
        print(f"蓝色占比: {blue_pixels / (region.shape[0] * region.shape[1]) * 100:.2f}%")
    else:
        print(f"❌ 位置超出截图范围")

if __name__ == "__main__":
    main()
