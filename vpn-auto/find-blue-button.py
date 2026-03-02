#!/usr/bin/env python3
"""
通过颜色检测找到深蓝色的 SAML Login 按钮
然后点击按钮中心
"""

import cv2
import numpy as np
import os
import time
import subprocess

# 配置
SCREENSHOT = "screen.png"
DISPLAY = ":1"

# 深蓝色的 HSV 范围（需要根据实际按钮颜色调整）
# 蓝色在 HSV 中的 H 值大约在 100-130 之间
BLUE_LOWER = np.array([100, 100, 100])  # H, S, V 下限
BLUE_UPPER = np.array([130, 255, 255])  # H, S, V 上限

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

def find_blue_button():
    """通过颜色检测找到深蓝色按钮"""
    if not os.path.exists(SCREENSHOT):
        log(f"❌ 截图文件不存在")
        return None
    
    # 读取图像
    img = cv2.imread(SCREENSHOT)
    if img is None:
        log(f"❌ 无法读取截图")
        return None
    
    log(f"屏幕尺寸: {img.shape[1]}x{img.shape[0]}")
    
    # 转换到 HSV 色彩空间
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 创建蓝色掩码
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    
    # 形态学操作，去除噪点
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 保存掩码图像用于调试
    cv2.imwrite("blue_mask.png", mask)
    log(f"✅ 蓝色掩码已保存: blue_mask.png")
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        log(f"❌ 未找到蓝色区域")
        return None
    
    log(f"找到 {len(contours)} 个蓝色区域")
    
    # 找到最大的蓝色区域（假设按钮是最大的蓝色区域）
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    
    log(f"最大蓝色区域面积: {area}")
    
    # 如果面积太小，可能不是按钮
    if area < 1000:
        log(f"❌ 蓝色区域太小，可能不是按钮")
        return None
    
    # 获取边界框
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # 计算中心点
    center_x = x + w // 2
    center_y = y + h // 2
    
    log(f"✅ 找到按钮")
    log(f"   位置: ({center_x}, {center_y})")
    log(f"   边界框: x={x}, y={y}, w={w}, h={h}")
    log(f"   面积: {area}")
    
    # 在原图上标记按钮位置（用于调试）
    debug_img = img.copy()
    cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.circle(debug_img, (center_x, center_y), 5, (0, 0, 255), -1)
    cv2.imwrite("button_detected.png", debug_img)
    log(f"✅ 检测结果已保存: button_detected.png")
    
    return center_x, center_y

def activate_window():
    """激活 FortiClient 窗口"""
    try:
        # 查找窗口
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip().split('\n')[0]
            log(f"找到窗口 ID: {window_id}")
            
            # 激活窗口
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

def click(x, y):
    """使用 xdotool 点击"""
    os.environ['DISPLAY'] = DISPLAY
    
    # 移动鼠标
    log(f"移动鼠标到 ({x}, {y})...")
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)])
    time.sleep(0.5)
    
    # 点击
    log(f"点击...")
    subprocess.run(["xdotool", "click", "1"])
    time.sleep(0.5)
    
    log(f"✅ 已点击坐标 ({x}, {y})")

def main():
    """主函数"""
    log("========================================")
    log("通过颜色检测找到深蓝色按钮并点击")
    log("========================================")
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
    
    # 3. 查找按钮
    log("步骤 3: 查找深蓝色按钮...")
    pos = find_blue_button()
    if not pos:
        log("")
        log("提示：如果未找到按钮，可能需要调整颜色范围")
        log("请查看 blue_mask.png 来确认蓝色检测是否正确")
        return False
    log("")
    
    # 4. 点击
    log("步骤 4: 点击按钮...")
    click(*pos)
    log("")
    
    log("========================================")
    log("✅ 操作完成")
    log("========================================")
    log("")
    log("请检查 VPN 是否开始连接")
    log("调试文件:")
    log("  - blue_mask.png (蓝色掩码)")
    log("  - button_detected.png (检测结果)")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
