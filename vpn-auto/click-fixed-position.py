#!/usr/bin/env python3
"""
使用固定坐标点击 SAML Login 按钮
基于之前成功的测试，按钮位置在 (993, 723)
"""

import subprocess
import time
import os

DISPLAY = ":1"
BUTTON_X = 993
BUTTON_Y = 723

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def click_button(x, y):
    """点击指定位置"""
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
            for line in result.stdout.split('\n'):
                if 'inet ' in line:
                    log(f"   {line.strip()}")
            return True
        
        time.sleep(1)
    
    log("⚠️  VPN 未连接")
    return False

def main():
    log("=" * 60)
    log("点击固定位置的 SAML Login 按钮")
    log("=" * 60)
    log("")
    
    # 点击按钮
    log(f"点击位置 ({BUTTON_X}, {BUTTON_Y})...")
    click_button(BUTTON_X, BUTTON_Y)
    log("")
    
    # 检查 VPN 连接
    if check_vpn_connected(max_wait=30):
        log("")
        log("=" * 60)
        log("✅ VPN 连接成功！")
        log("=" * 60)
        return True
    else:
        log("")
        log("=" * 60)
        log("⚠️  VPN 未连接，可能需要更长时间")
        log("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
