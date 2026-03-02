#!/usr/bin/env python3
"""
结合 OCR 文字识别和颜色检测找到 SAML Login 按钮
1. 使用 tesseract OCR 识别 "SAML Login" 文字
2. 在文字周围查找深蓝色区域
3. 移动光标到按钮上触发 hover 效果
4. 点击按钮
"""

import cv2
import numpy as np
import pytesseract
import os
import time
import subprocess
import re

# 配置
SCREENSHOT = "screen.png"
DISPLAY = ":1"

# 深蓝色的 HSV 范围
BLUE_LOWER = np.array([100, 80, 80])
BLUE_UPPER = np.array([130, 255, 255])

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
        log(f"❌ 截图失败")
        return False

def find_text_with_ocr(img):
    """使用 OCR 查找 'SAML Login' 文字位置"""
    log("使用 OCR 识别文字...")
    
    # 使用 pytesseract 获取详细信息
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    # 查找包含 "SAML" 或 "Login" 的文字
    saml_boxes = []
    
    for i, text in enumerate(data['text']):
        if text.strip():
            # 清理文字
            clean_text = re.sub(r'[^a-zA-Z]', '', text).upper()
            
            if 'SAML' in clean_text or 'LOGIN' in clean_text:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = data['conf'][i]
                
                log(f"  找到文字: '{text}' (置信度: {conf})")
                log(f"    位置: x={x}, y={y}, w={w}, h={h}")
                
                saml_boxes.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'conf': conf
                })
    
    return saml_boxes

def find_blue_region_near_text(img, text_box, search_radius=100):
    """在文字周围查找深蓝色区域"""
    log(f"在文字周围 {search_radius}px 范围内查找深蓝色区域...")
    
    # 获取文字中心点
    text_center_x = text_box['x'] + text_box['w'] // 2
    text_center_y = text_box['y'] + text_box['h'] // 2
    
    # 定义搜索区域
    x1 = max(0, text_center_x - search_radius)
    y1 = max(0, text_center_y - search_radius)
    x2 = min(img.shape[1], text_center_x + search_radius)
    y2 = min(img.shape[0], text_center_y + search_radius)
    
    # 裁剪搜索区域
    search_area = img[y1:y2, x1:x2]
    
    # 转换到 HSV
    hsv = cv2.cvtColor(search_area, cv2.COLOR_BGR2HSV)
    
    # 创建蓝色掩码
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    
    # 形态学操作
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        log(f"  ❌ 未找到蓝色区域")
        return None
    
    log(f"  找到 {len(contours)} 个蓝色区域")
    
    # 找到包含文字的蓝色区域
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 500:  # 太小的区域忽略
            continue
        
        # 获取边界框（相对于搜索区域）
        x, y, w, h = cv2.boundingRect(contour)
        
        # 转换为绝对坐标
        abs_x = x1 + x
        abs_y = y1 + y
        
        # 检查文字是否在这个蓝色区域内
        if (abs_x <= text_center_x <= abs_x + w and
            abs_y <= text_center_y <= abs_y + h):
            
            center_x = abs_x + w // 2
            center_y = abs_y + h // 2
            
            log(f"  ✅ 找到包含文字的蓝色区域")
            log(f"    位置: x={abs_x}, y={abs_y}, w={w}, h={h}")
            log(f"    中心: ({center_x}, {center_y})")
            log(f"    面积: {area}")
            
            return {
                'x': abs_x,
                'y': abs_y,
                'w': w,
                'h': h,
                'center_x': center_x,
                'center_y': center_y,
                'area': area
            }
    
    log(f"  ❌ 未找到包含文字的蓝色区域")
    return None

def activate_window():
    """激活 FortiClient 窗口"""
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip().split('\n')[0]
            log(f"找到窗口 ID: {window_id}")
            
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", window_id],
                env={"DISPLAY": DISPLAY}
            )
            time.sleep(0.5)
            log(f"✅ 窗口已激活")
            return True
    except Exception as e:
        log(f"⚠️  激活窗口失败: {e}")
    
    return False

def hover_and_click(x, y):
    """移动光标到按钮上（触发 hover 效果）然后点击"""
    os.environ['DISPLAY'] = DISPLAY
    
    # 移动鼠标到按钮上方
    log(f"移动光标到 ({x}, {y}) 触发 hover 效果...")
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)])
    
    # 等待 hover 效果生效（背景变白）
    time.sleep(1.0)
    log(f"等待 hover 效果...")
    
    # 点击
    log(f"点击按钮...")
    subprocess.run(["xdotool", "click", "1"])
    time.sleep(0.5)
    
    log(f"✅ 已点击坐标 ({x}, {y})")

def save_debug_image(img, text_boxes, button_region):
    """保存调试图像"""
    debug_img = img.copy()
    
    # 标记文字位置
    for box in text_boxes:
        x, y, w, h = box['x'], box['y'], box['w'], box['h']
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(debug_img, box['text'], (x, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # 标记按钮区域
    if button_region:
        x = button_region['x']
        y = button_region['y']
        w = button_region['w']
        h = button_region['h']
        cx = button_region['center_x']
        cy = button_region['center_y']
        
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (255, 0, 0), 3)
        cv2.circle(debug_img, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(debug_img, "SAML Login Button", (x, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    cv2.imwrite("saml_button_detected.png", debug_img)
    log(f"✅ 调试图像已保存: saml_button_detected.png")

def main():
    """主函数"""
    log("=" * 60)
    log("使用 OCR + 颜色检测找到 SAML Login 按钮")
    log("=" * 60)
    log("")
    
    # 1. 激活窗口
    log("步骤 1: 激活 FortiClient 窗口...")
    activate_window()
    log("")
    
    # 2. 截图
    log("步骤 2: 截取屏幕...")
    if not take_screenshot():
        return False
    log("")
    
    # 3. 读取图像
    img = cv2.imread(SCREENSHOT)
    if img is None:
        log(f"❌ 无法读取截图")
        return False
    
    log(f"屏幕尺寸: {img.shape[1]}x{img.shape[0]}")
    log("")
    
    # 4. OCR 识别文字
    log("步骤 3: 使用 OCR 识别 'SAML Login' 文字...")
    text_boxes = find_text_with_ocr(img)
    
    if not text_boxes:
        log(f"❌ 未找到 'SAML Login' 文字")
        return False
    
    log(f"✅ 找到 {len(text_boxes)} 个相关文字")
    log("")
    
    # 5. 在文字周围查找深蓝色区域
    log("步骤 4: 在文字周围查找深蓝色按钮区域...")
    button_region = None
    
    for text_box in text_boxes:
        log(f"检查文字 '{text_box['text']}' 周围...")
        region = find_blue_region_near_text(img, text_box, search_radius=150)
        
        if region:
            button_region = region
            break
    
    if not button_region:
        log(f"❌ 未找到按钮区域")
        log("")
        log("提示：")
        log("  1. 检查 FortiClient 窗口是否打开")
        log("  2. 检查 SAML Login 按钮是否可见")
        log("  3. 调整颜色范围或搜索半径")
        return False
    
    log("")
    
    # 6. 保存调试图像
    save_debug_image(img, text_boxes, button_region)
    log("")
    
    # 7. Hover + Click
    log("步骤 5: 移动光标并点击按钮...")
    hover_and_click(button_region['center_x'], button_region['center_y'])
    log("")
    
    log("=" * 60)
    log("✅ 操作完成")
    log("=" * 60)
    log("")
    log("请检查 VPN 是否开始连接")
    log("调试文件: saml_button_detected.png")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
