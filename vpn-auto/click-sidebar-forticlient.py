#!/usr/bin/env python3
"""
点击桌面左边栏的第三个按钮启动 FortiClient
"""

import subprocess
import time
import os

DISPLAY = ":1"

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def click_sidebar_button(button_number=3):
    """
    点击左边栏的按钮
    假设左边栏在屏幕左侧，按钮垂直排列
    """
    os.environ['DISPLAY'] = DISPLAY
    
    # 左边栏通常在屏幕左侧，宽度约 60-80 像素
    # 按钮通常是正方形，大小约 48x48 或 64x64
    # 第一个按钮通常在顶部，间距约 10-20 像素
    
    sidebar_x = 40  # 左边栏中心 X 坐标
    button_size = 64  # 按钮大小
    button_spacing = 10  # 按钮间距
    top_margin = 20  # 顶部边距
    
    # 计算第 N 个按钮的 Y 坐标
    button_y = top_margin + (button_number - 1) * (button_size + button_spacing) + button_size // 2
    
    log(f"点击左边栏第 {button_number} 个按钮...")
    log(f"位置: ({sidebar_x}, {button_y})")
    
    # 移动鼠标
    subprocess.run(
        ["xdotool", "mousemove", "--sync", str(sidebar_x), str(button_y)],
        env={"DISPLAY": DISPLAY}
    )
    time.sleep(0.5)
    
    # 点击
    subprocess.run(
        ["xdotool", "click", "1"],
        env={"DISPLAY": DISPLAY}
    )
    time.sleep(0.5)
    
    log("✅ 已点击")

def wait_for_forticlient(max_wait=10):
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
                log(f"✅ FortiClient 窗口已出现（等待 {i+1} 秒）")
                return True
        except Exception:
            pass
        
        time.sleep(1)
    
    log("❌ FortiClient 窗口未出现")
    return False

def main():
    log("=" * 60)
    log("通过左边栏启动 FortiClient")
    log("=" * 60)
    log("")
    
    # 点击左边栏第三个按钮
    click_sidebar_button(button_number=3)
    log("")
    
    # 等待窗口出现
    if wait_for_forticlient(max_wait=10):
        log("")
        log("=" * 60)
        log("✅ FortiClient 已启动")
        log("=" * 60)
        return True
    else:
        log("")
        log("=" * 60)
        log("⚠️  FortiClient 可能未启动，请检查")
        log("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
