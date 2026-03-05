#!/usr/bin/env python3
"""
自动截取 FortiClient 连接按钮
使用 OpenCV 识别按钮位置并截取
"""

import os
import sys
import cv2
import numpy as np
import select
from pathlib import Path

# 设置 DISPLAY
os.environ['DISPLAY'] = ':1'

# 配置
SCREENSHOT_PATH = '/tmp/forticlient-full.png'
BUTTON_OUTPUT = '/home/tsl/openclaw/vpn-auto/v2/config/button.png'

# HSV 颜色范围（蓝色按钮）
HSV_LOWER = np.array([100, 100, 100])
HSV_UPPER = np.array([130, 255, 255])

# 按钮尺寸范围
MIN_AREA = 2000
MAX_AREA = 50000
MIN_WIDTH = 80
MAX_WIDTH = 300
MIN_HEIGHT = 25
MAX_HEIGHT = 80


def capture_screen():
    """截取整个屏幕"""
    print("📸 截取屏幕...")
    os.system(f'DISPLAY=:1 import -window root {SCREENSHOT_PATH}')
    
    if not os.path.exists(SCREENSHOT_PATH):
        print("❌ 截图失败")
        return None
    
    return cv2.imread(SCREENSHOT_PATH)


def find_button(image):
    """查找蓝色按钮"""
    print("🔍 查找按钮...")
    
    # 转换为 HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 创建掩码
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    
    # 形态学操作
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 筛选按钮
    buttons = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_AREA or area > MAX_AREA:
            continue
        
        x, y, w, h = cv2.boundingRect(contour)
        
        if w < MIN_WIDTH or w > MAX_WIDTH:
            continue
        if h < MIN_HEIGHT or h > MAX_HEIGHT:
            continue
        
        # 宽高比检查（按钮通常是横向的）
        aspect_ratio = w / h
        if aspect_ratio < 1.5 or aspect_ratio > 6:
            continue
        
        buttons.append({
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'area': area,
            'center': (x + w // 2, y + h // 2)
        })
    
    if not buttons:
        print("❌ 未找到符合条件的按钮")
        return None
    
    # 按面积排序，选择最大的
    buttons.sort(key=lambda b: b['area'], reverse=True)
    
    print(f"✅ 找到 {len(buttons)} 个候选按钮")
    for i, btn in enumerate(buttons[:3]):
        print(f"   {i+1}. 位置: ({btn['x']}, {btn['y']}), 尺寸: {btn['w']}x{btn['h']}, 面积: {btn['area']}")
    
    return buttons[0]


def extract_button(image, button, padding=10):
    """提取按钮图像"""
    print("✂️  提取按钮图像...")
    
    x = max(0, button['x'] - padding)
    y = max(0, button['y'] - padding)
    w = button['w'] + 2 * padding
    h = button['h'] + 2 * padding
    
    # 确保不超出图像边界
    x2 = min(image.shape[1], x + w)
    y2 = min(image.shape[0], y + h)
    
    button_img = image[y:y2, x:x2]
    
    return button_img


def main():
    print("=" * 60)
    print("FortiClient 按钮自动截取工具")
    print("=" * 60)
    print()
    
    # 1. 截取屏幕
    image = capture_screen()
    if image is None:
        sys.exit(1)
    
    print(f"   屏幕尺寸: {image.shape[1]}x{image.shape[0]}")
    print()
    
    # 2. 查找按钮
    button = find_button(image)
    if button is None:
        print()
        print("提示：")
        print("- 确保 FortiClient 窗口已打开")
        print("- 确保连接按钮可见（蓝色）")
        print("- 可以尝试手动截图：bash vpn-auto/v2/capture-button.sh")
        sys.exit(1)
    
    print()
    
    # 3. 提取按钮图像
    button_img = extract_button(image, button)
    
    # 4. 保存
    cv2.imwrite(BUTTON_OUTPUT, button_img)
    print(f"💾 按钮图像已保存到: {BUTTON_OUTPUT}")
    print(f"   尺寸: {button_img.shape[1]}x{button_img.shape[0]}")
    print()
    
    # 5. 显示预览（可选）
    print("是否显示预览？(y/n): ", end='', flush=True)
    try:
        # 等待 3 秒输入
        if select.select([sys.stdin], [], [], 3)[0]:
            choice = sys.stdin.readline().strip().lower()
            if choice == 'y':
                # 在原图上标记按钮位置
                marked = image.copy()
                cv2.rectangle(marked, 
                            (button['x'], button['y']), 
                            (button['x'] + button['w'], button['y'] + button['h']), 
                            (0, 255, 0), 3)
                
                # 保存标记图像
                marked_path = '/tmp/forticlient-marked.png'
                cv2.imwrite(marked_path, marked)
                
                print(f"\n📍 标记图像已保存到: {marked_path}")
                print("   使用图像查看器打开查看")
                
                # 尝试打开图像
                os.system(f'DISPLAY=:1 xdg-open {marked_path} 2>/dev/null &')
                os.system(f'DISPLAY=:1 xdg-open {BUTTON_OUTPUT} 2>/dev/null &')
    except:
        pass
    
    print()
    print("=" * 60)
    print("✅ 完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 检查按钮图像是否正确")
    print("2. 重启 VPN 服务测试 PyAutoDriver")
    print("   sudo systemctl restart vpn-auto.service")
    print()
    
    # 清理临时文件
    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)


if __name__ == '__main__':
    main()
