#!/usr/bin/env python3
"""
VPN 自动连接脚本（包含 FortiClient 重启）
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

def start_forticlient():
    """启动 FortiClient GUI（直接使用命令行）"""
    log("启动 FortiClient GUI...")
    try:
        # 直接使用命令行启动，指定 DISPLAY=:1
        cmd = f"DISPLAY={DISPLAY} nohup /usr/bin/forticlient gui > /tmp/forticlient-auto.log 2>&1 &"
        subprocess.run(cmd, shell=True)
        time.sleep(3)
        
        log("✅ FortiClient GUI 已启动")
        return True
    except Exception as e:
        log(f"❌ 启动失败: {e}")
        return False

def wait_for_window(max_wait=30):
    """等待窗口出现（先在 DISPLAY=:0 查找，然后在 DISPLAY=:1 查找）"""
    log(f"等待 FortiClient 窗口出现（最多 {max_wait} 秒）...")
    
    for i in range(max_wait):
        # 先在 DISPLAY=:0 查找
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", "FortiClient"],
                capture_output=True,
                text=True,
                env={"DISPLAY": ":0"}
            )
            
            if result.returncode == 0 and result.stdout.strip():
                log(f"✅ 窗口在 DISPLAY=:0 出现（等待 {i+1} 秒）")
                return True
        except Exception:
            pass
        
        # 再在 DISPLAY=:1 查找
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", "FortiClient"],
                capture_output=True,
                text=True,
                env={"DISPLAY": DISPLAY}
            )
            
            if result.returncode == 0 and result.stdout.strip():
                log(f"✅ 窗口在 DISPLAY=:1 出现（等待 {i+1} 秒）")
                return True
        except Exception:
            pass
        
        time.sleep(1)
    
    log(f"❌ 窗口出现超时")
    return False

def wait_for_gui_ready(wait_time=15):
    """等待 GUI 完全加载"""
    log(f"等待 GUI 完全加载（{wait_time} 秒）...")
    time.sleep(wait_time)
    log("✅ GUI 应该已完全加载")
    return True

def get_forticlient_display():
    """检测 FortiClient 窗口在哪个 DISPLAY"""
    # 先检查 DISPLAY=:0
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": ":0"}
        )
        if result.returncode == 0 and result.stdout.strip():
            return ":0"
    except Exception:
        pass
    
    # 再检查 DISPLAY=:1
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": ":1"}
        )
        if result.returncode == 0 and result.stdout.strip():
            return ":1"
    except Exception:
        pass
    
    return None

def resize_window():
    """调整窗口大小"""
    log("调整窗口大小...")
    
    # 检测窗口在哪个 DISPLAY
    window_display = get_forticlient_display()
    if not window_display:
        log("⚠️  未找到 FortiClient 窗口")
        return False
    
    log(f"FortiClient 窗口在 DISPLAY={window_display}")
    
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "FortiClient"],
            capture_output=True,
            text=True,
            env={"DISPLAY": window_display}
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip().split('\n')[0]
            
            # 移动窗口
            subprocess.run(
                ["xdotool", "windowmove", window_id, "100", "100"],
                env={"DISPLAY": window_display}
            )
            time.sleep(0.3)
            
            # 调整大小
            subprocess.run(
                ["xdotool", "windowsize", window_id, "1200", "800"],
                env={"DISPLAY": window_display}
            )
            time.sleep(0.5)
            
            # 激活窗口
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", window_id],
                env={"DISPLAY": window_display}
            )
            time.sleep(0.5)
            
            log("✅ 窗口已调整为 1200x800")
            return True
    except Exception as e:
        log(f"⚠️  调整窗口失败: {e}")
    
    return False

def trigger_vpn_connect():
    """在 FortiClient GUI 中触发 VPN 连接"""
    log("触发 VPN 连接...")
    try:
        # 使用 xdotool 模拟按键：Ctrl+Shift+C（FortiClient 的连接快捷键）
        # 或者点击窗口中的 Connect 按钮位置
        
        # 方法1：尝试快捷键
        subprocess.run(
            ["xdotool", "key", "ctrl+shift+c"],
            env={"DISPLAY": DISPLAY}
        )
        time.sleep(2)
        
        log("✅ 已触发 VPN 连接")
        return True
    except Exception as e:
        log(f"⚠️  触发连接失败: {e}")
        return False

def take_screenshot():
    """截图（使用检测到的 DISPLAY）"""
    window_display = get_forticlient_display()
    if not window_display:
        window_display = DISPLAY  # 默认使用 :1
    
    os.environ['DISPLAY'] = window_display
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
    """点击按钮（使用检测到的 DISPLAY）"""
    window_display = get_forticlient_display()
    if not window_display:
        window_display = DISPLAY  # 默认使用 :1
    
    os.environ['DISPLAY'] = window_display
    
    log(f"移动光标到 ({x}, {y})...")
    subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], env={"DISPLAY": window_display})
    time.sleep(1.0)
    
    log("点击...")
    subprocess.run(["xdotool", "click", "1"], env={"DISPLAY": window_display})
    time.sleep(0.5)
    
    log("按 Enter...")
    subprocess.run(["xdotool", "key", "Return"], env={"DISPLAY": window_display})
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
    
    log(f"❌ VPN 连接超时")
    return False

def main():
    log("=" * 60)
    log("VPN 自动连接（包含 FortiClient 重启）")
    log("=" * 60)
    log("")
    
    # 1. 停止 FortiClient
    if not stop_forticlient():
        log("警告：停止进程失败，继续执行...")
    log("")
    
    # 2. 启动 FortiClient
    if not start_forticlient():
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
    
    # 9. 查找按钮
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
    
    # 10. 点击按钮
    log("点击按钮...")
    click_button(button['center_x'], button['center_y'])
    log("")
    
    # 11. 检查 VPN 连接
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
