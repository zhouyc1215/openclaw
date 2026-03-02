#!/usr/bin/env python3
"""
测试不同的点击方式
"""

import subprocess
import time
import os

DISPLAY = ":1"
BUTTON_X = 993
BUTTON_Y = 723

def log(message):
    """打印日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def move_to_button():
    """移动光标到按钮"""
    os.environ['DISPLAY'] = DISPLAY
    subprocess.run(["xdotool", "mousemove", str(BUTTON_X), str(BUTTON_Y)],
                   env={"DISPLAY": DISPLAY})
    time.sleep(0.5)

def take_screenshot(name):
    """截图"""
    subprocess.run(["scrot", f"{name}.png"],
                   env={"DISPLAY": DISPLAY},
                   capture_output=True)
    log(f"  截图已保存: {name}.png")

def test_method_1():
    """方法 1: 鼠标按下-停留-释放"""
    log("=" * 60)
    log("测试方法 1: 鼠标按下-停留-释放")
    log("=" * 60)
    
    move_to_button()
    take_screenshot("method1_before")
    
    log("按下鼠标...")
    subprocess.run(["xdotool", "mousedown", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(0.5)
    
    log("释放鼠标...")
    subprocess.run(["xdotool", "mouseup", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(2)
    
    take_screenshot("method1_after")
    log("✅ 方法 1 完成")
    log("")

def test_method_2():
    """方法 2: 双击（间隔200ms）"""
    log("=" * 60)
    log("测试方法 2: 双击（间隔200ms）")
    log("=" * 60)
    
    move_to_button()
    take_screenshot("method2_before")
    
    log("双击...")
    subprocess.run(["xdotool", "click", "--repeat", "2", "--delay", "200", "1"],
                   env={"DISPLAY": DISPLAY})
    time.sleep(2)
    
    take_screenshot("method2_after")
    log("✅ 方法 2 完成")
    log("")

def test_method_3():
    """方法 3: 三击"""
    log("=" * 60)
    log("测试方法 3: 三击")
    log("=" * 60)
    
    move_to_button()
    take_screenshot("method3_before")
    
    log("三击...")
    subprocess.run(["xdotool", "click", "--repeat", "3", "--delay", "100", "1"],
                   env={"DISPLAY": DISPLAY})
    time.sleep(2)
    
    take_screenshot("method3_after")
    log("✅ 方法 3 完成")
    log("")

def test_method_4():
    """方法 4: 慢速单击（移动时间0.5秒）"""
    log("=" * 60)
    log("测试方法 4: 慢速单击")
    log("=" * 60)
    
    take_screenshot("method4_before")
    
    log("慢速移动到按钮...")
    # 使用 --sync 确保移动完成
    subprocess.run(["xdotool", "mousemove", "--sync", str(BUTTON_X), str(BUTTON_Y)],
                   env={"DISPLAY": DISPLAY})
    time.sleep(1.0)
    
    log("单击...")
    subprocess.run(["xdotool", "click", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(2)
    
    take_screenshot("method4_after")
    log("✅ 方法 4 完成")
    log("")

def test_method_5():
    """方法 5: 点击按钮左侧"""
    log("=" * 60)
    log("测试方法 5: 点击按钮左侧")
    log("=" * 60)
    
    left_x = 950  # 按钮左侧
    
    take_screenshot("method5_before")
    
    log(f"移动到按钮左侧 ({left_x}, {BUTTON_Y})...")
    subprocess.run(["xdotool", "mousemove", str(left_x), str(BUTTON_Y)],
                   env={"DISPLAY": DISPLAY})
    time.sleep(1.0)
    
    log("单击...")
    subprocess.run(["xdotool", "click", "1"], env={"DISPLAY": DISPLAY})
    time.sleep(2)
    
    take_screenshot("method5_after")
    log("✅ 方法 5 完成")
    log("")

def check_vpn_status():
    """检查 VPN 状态"""
    log("检查 VPN 状态...")
    result = subprocess.run(["ip", "addr", "show", "ppp0"],
                          capture_output=True,
                          text=True)
    
    if result.returncode == 0:
        log("✅ VPN 接口已建立！")
        return True
    else:
        log("❌ VPN 接口未建立")
        return False

def main():
    """主函数"""
    log("=" * 60)
    log("测试不同的点击方式")
    log("=" * 60)
    log("")
    log(f"按钮位置: ({BUTTON_X}, {BUTTON_Y})")
    log("")
    
    # 测试方法 1
    test_method_1()
    if check_vpn_status():
        log("🎉 方法 1 成功！")
        return
    time.sleep(3)
    
    # 测试方法 2
    test_method_2()
    if check_vpn_status():
        log("🎉 方法 2 成功！")
        return
    time.sleep(3)
    
    # 测试方法 3
    test_method_3()
    if check_vpn_status():
        log("🎉 方法 3 成功！")
        return
    time.sleep(3)
    
    # 测试方法 4
    test_method_4()
    if check_vpn_status():
        log("🎉 方法 4 成功！")
        return
    time.sleep(3)
    
    # 测试方法 5
    test_method_5()
    if check_vpn_status():
        log("🎉 方法 5 成功！")
        return
    
    log("")
    log("=" * 60)
    log("所有方法测试完成")
    log("=" * 60)
    log("")
    log("请查看截图对比点击前后的变化：")
    log("  - method1_before.png / method1_after.png")
    log("  - method2_before.png / method2_after.png")
    log("  - method3_before.png / method3_after.png")
    log("  - method4_before.png / method4_after.png")
    log("  - method5_before.png / method5_after.png")

if __name__ == "__main__":
    main()
