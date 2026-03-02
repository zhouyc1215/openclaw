#!/usr/bin/env python3
"""
图像识别调试工具
测试不同的置信度参数，找到最佳识别设置
"""

import sys
import os
import pyautogui

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUTTON_IMAGE = os.path.join(SCRIPT_DIR, "images", "connect_button.png")

def test_recognition():
    """测试不同置信度的图像识别"""
    print("========================================")
    print("图像识别调试工具")
    print("========================================")
    print()
    
    # 设置 DISPLAY
    os.environ['DISPLAY'] = ":1"
    print(f"DISPLAY: {os.environ.get('DISPLAY')}")
    
    # 检查图像文件
    if not os.path.exists(BUTTON_IMAGE):
        print(f"❌ 按钮图像不存在: {BUTTON_IMAGE}")
        return
    
    print(f"✅ 按钮图像: {BUTTON_IMAGE}")
    print()
    
    # 截取当前屏幕
    print("截取当前屏幕...")
    screenshot = pyautogui.screenshot()
    debug_path = os.path.join(SCRIPT_DIR, "test_screen.png")
    screenshot.save(debug_path)
    print(f"✅ 屏幕截图已保存: {debug_path}")
    print()
    
    # 测试不同的置信度
    confidences = [0.9, 0.8, 0.7, 0.6, 0.5]
    
    print("测试不同的置信度参数...")
    print("----------------------------------------")
    
    for conf in confidences:
        print(f"\n测试置信度: {conf}")
        try:
            location = pyautogui.locateOnScreen(
                BUTTON_IMAGE,
                confidence=conf,
                grayscale=True
            )
            
            if location:
                x, y = pyautogui.center(location)
                print(f"  ✅ 找到按钮！位置: ({x}, {y})")
                print(f"  区域: {location}")
                print(f"  建议使用置信度: {conf}")
                
                # 在第一次成功后就停止
                print()
                print("========================================")
                print(f"✅ 最佳置信度: {conf}")
                print(f"✅ 按钮位置: ({x}, {y})")
                print("========================================")
                return
            else:
                print(f"  ❌ 未找到按钮")
        except Exception as e:
            print(f"  ❌ 识别失败: {e}")
    
    print()
    print("========================================")
    print("❌ 所有置信度都无法识别按钮")
    print("========================================")
    print()
    print("可能的原因：")
    print("1. FortiClient 窗口未打开或被遮挡")
    print("2. 窗口状态不同（已连接/正在连接）")
    print("3. 按钮图像需要重新捕获")
    print()
    print("建议操作：")
    print("1. 确保 FortiClient 窗口可见且处于'未连接'状态")
    print("2. 重新运行 capture-button.py 捕获按钮图像")
    print("3. 查看调试截图: test_screen.png")

if __name__ == "__main__":
    test_recognition()
