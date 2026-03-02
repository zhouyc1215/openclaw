#!/usr/bin/env python3
"""
完整的 VPN 自动连接脚本
1. 停止 FortiClient
2. 在 GUI 左边栏点击第三个图标启动 FortiClient
3. 等待窗口出现并调整大小
4. 查找并点击 SAML Login 按钮
5. 检查 VPN 连接状态
"""

import cv2
import numpy as np
import os
import time
import subprocess
import sys

# 配置
SCREENSHOT = "screen.png"
DISPLAY = ":1"
SUDO_PASSWORD = "tsl123"

# 深蓝色的 HSV 范围
BLUE_LOWER = np.array([100, 100, 100])
BLUE_UPPER = np.array([130, 255, 255])

# 紫色的 HSV 范围（SAML Login 按钮可能是紫色）
PURPLE_LOWER = np.array([140, 200, 50])
PURPLE_UPPER = np.array([160, 255, 150])

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

def stop_forticlient():
    """停止 FortiClient 进程"""
    log("停止 FortiClient 进程...")
    try:
        cmd = f"echo {SUDO_PASSWORD} | sudo -S pkill -9 -f forticlient"
        subprocess.run(cmd, shell=True, capture_output=True)
        time.sleep(3)
        log("✅ FortiClient 进程已停止")
        return True
    except Exception as e:
        log(f"⚠️  停止进程失败: {e}")
        return False

def click_sidebar_to_start():
    """在 GUI 左边栏点击第三个图标启动 FortiClient"""
    log("在 GUI 左边栏点击第三个图标启动 FortiClient...")
    try:
        # 左边栏第三个按钮的位置
        sidebar_x = 40
        button_size = 64
        button_spacing = 10
        top_margin = 20
        button_number = 3
        
        button_y = top_margin + (button_number - 1) * (button_size + button_spacing) + button_size // 2
        
        log(f"点击位置: ({sidebar_x}, {button_y})")
        
        # 移动鼠标并点击
        subprocess.run(
            ["xdotool", "mousemove", "--sync", str(sidebar_x), str(button_y)],
            env={"DISPLAY": DISPLAY}
        )
        time.sleep(0.5)
        
        subprocess.run(
            ["xdotool", "click", "1"],
            env={"DISPLAY": DISPLAY}
        )
        time.sleep(2)
        
        log("✅ 已点击左边栏图标")
        return True
    except Exception as e:
        log(f"❌ 点击失败: {e}")
        return False

def wait_for_window(max_wait=30):
    """等待 FortiClient 窗口出现"""
    log(f"等待 FortiClient 窗口出现（最多 {max_wait} 秒）...")
    
    for i in range(max_wait):
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", "FortiClient"],
                capture_output=True,
                text=True,
                env={"DISPLAY": DISPLAY}
            )
            
            if result.returncode == 0 and result.stdout.strip():
                log(f"✅ 窗口已出现（等待 {i+1} 秒）")
                return True
        except Exception:
            pass
        
        time.sleep(1)
    
    log("❌ 窗口出现超时")
    return False

def wait_for_gui_ready(wait_time=15):
    """等待 GUI 完全加载"""
    log(f"等待 GUI 完全加载（{wait_time} 秒）...")
    time.sleep(wait_time)
    log("✅ GUI 应该已完全加载")
    return True

def resize_window():
    """调整窗口大小"""
    log("调整窗口大小...")
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": DISPLAY}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip().split('\n')[0]
            
            # 移动窗口
            subprocess.run(
                ["xdotool", "windowmove", window_id, "100", "100"],
                env={"DISPLAY": DISPLAY}
            )
            time.sleep(0.3)
            
            # 调整大小
            subprocess.run(
                ["xdotool", "windowsize", window_id, "1200", "800"],
                env={"DISPLAY": DISPLAY}
            )
            time.sleep(0.5)
            
            # 激活窗口
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", window_id],
                env={"DISPLAY": DISPLAY}
            )
            time.sleep(0.5)
            
            log("✅ 窗口已调整为 1200x800")
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
    """查找 SAML Login 按钮"""
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
    
    log(f"移动光标到 ({x}, {y})...")
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], env={"DISPLAY": DISPLAY})
    time.sleep(1.0)
    
    log("点击...")
    subprocess.run(["xdotool", "click", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    
    log("按 Enter...")
    subprocess.run(["xdotool", "key", "Return"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    
    log("✅ 已点击并按 Enter")

def check_vpn_connected(max_wait=30):
    """检查 VPN 是否连接"""
    log(f"等待 VPN 连接（最多 {max_wait} 秒）...")
    
    for i in range(max_wait):
        result = subprocess.run(
            ["ip", "addr", "show", "ppp0"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and "inet " in result.stdout:
            log(f"✅ VPN 已连接！（等待 {i+1} 秒）")
            # 显示 IP 地址
            for line in result.stdout.split('\n'):
                if 'inet ' in line:
                    log(f"   {line.strip()}")
            return True
        
        time.sleep(1)
    
    log("❌ VPN 连接超时")
    return False

def main():
    log("=" * 60)
    log("VPN 完整自动连接")
    log("=" * 60)
    log("")
    
    # 1. 停止 FortiClient
    if not stop_forticlient():
        log("警告：停止进程失败，继续执行...")
    log("")
    
    # 2. 点击左边栏启动 FortiClient
    if not click_sidebar_to_start():
        log("❌ 启动失败")
        return False
    log("")
    
    # 3. 等待窗口出现
    if not wait_for_window(max_wait=30):
        log("❌ 窗口未出现")
        return False
    log("")
    
    # 4. 等待 GUI 加载
    wait_for_gui_ready(wait_time=15)
    log("")
    
    # 5. 调整窗口
    resize_window()
    log("")
    
    # 6. 截图
    log("截图...")
    if not take_screenshot():
        log("❌ 截图失败")
        return False
    log("✅ 截图成功")
    log("")
    
    # 7. 查找按钮
    log("查找 SAML Login 按钮...")
    img = cv2.imread(SCREENSHOT)
    if img is None:
        log("❌ 无法读取截图")
        return False
    
    button = find_button(img)
    if button:
        log(f"✅ 找到按钮: ({button['center_x']}, {button['center_y']})")
        button_x = button['center_x']
        button_y = button['center_y']
    else:
        log("⚠️  未找到按钮，使用固定坐标 (993, 723)")
        button_x = 993
        button_y = 723
    log("")
    
    # 8. 点击按钮
    log("点击 SAML Login 按钮...")
    click_button(button_x, button_y)
    log("")
    
    # 9. 检查 VPN 连接
    if check_vpn_connected(max_wait=30):
        log("")
        log("=" * 60)
        log("✅ VPN 自动连接成功！")
        log("=" * 60)
        return True
    else:
        log("")
        log("=" * 60)
        log("⚠️  VPN 未连接，可能需要手动完成认证")
        log("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
