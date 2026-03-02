#!/usr/bin/env python3
"""
查找截图中所有可能的按钮（更宽松的条件）
"""

import cv2
import numpy as np
import pytesseract

SCREENSHOT = "screen.png"

def log(message):
    print(message)

def find_buttons_by_color(img):
    """通过颜色查找所有可能的按钮"""
    log("=" * 60)
    log("通过颜色查找按钮")
    log("=" * 60)
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 多种颜色范围
    color_ranges = [
        ("蓝色", np.array([100, 50, 50]), np.array([130, 255, 255])),
        ("绿色", np.array([40, 50, 50]), np.array([80, 255, 255])),
        ("红色1", np.array([0, 50, 50]), np.array([10, 255, 255])),
        ("红色2", np.array([170, 50, 50]), np.array([180, 255, 255])),
    ]
    
    all_candidates = []
    
    for color_name, lower, upper in color_ranges:
        mask = cv2.inRange(hsv, lower, upper)
        
        # 形态学处理
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            
            # 更宽松的条件：面积 > 500，宽度 > 40，高度 > 15
            if area > 500 and w > 40 and h > 15:
                center_x = x + w // 2
                center_y = y + h // 2
                all_candidates.append({
                    'color': color_name,
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'center_x': center_x, 'center_y': center_y,
                    'area': area
                })
    
    # 按面积排序
    all_candidates.sort(key=lambda c: c['area'], reverse=True)
    
    log(f"\n找到 {len(all_candidates)} 个候选按钮:\n")
    for i, btn in enumerate(all_candidates[:20], 1):  # 只显示前20个
        log(f"{i}. {btn['color']} 按钮:")
        log(f"   位置: ({btn['x']}, {btn['y']})")
        log(f"   尺寸: {btn['w']}x{btn['h']}")
        log(f"   面积: {btn['area']:.0f}")
        log(f"   中心: ({btn['center_x']}, {btn['center_y']})")
        log("")
    
    return all_candidates

def find_text_regions(img):
    """使用 OCR 查找文本区域"""
    log("=" * 60)
    log("使用 OCR 查找文本")
    log("=" * 60)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # OCR 识别
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    
    log("\n找到的文本:\n")
    for i, text in enumerate(data['text']):
        if text.strip():
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            conf = data['conf'][i]
            
            if conf > 30:  # 置信度 > 30
                log(f"'{text}' 在 ({x}, {y}), 尺寸: {w}x{h}, 置信度: {conf}")

def main():
    log("读取截图...")
    img = cv2.imread(SCREENSHOT)
    if img is None:
        log("❌ 无法读取截图")
        return
    
    log(f"截图尺寸: {img.shape[1]}x{img.shape[0]}")
    log("")
    
    # 查找按钮
    buttons = find_buttons_by_color(img)
    
    # 查找文本
    find_text_regions(img)

if __name__ == "__main__":
    main()
