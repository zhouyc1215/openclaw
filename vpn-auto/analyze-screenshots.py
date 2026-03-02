#!/usr/bin/env python3
"""
分析截图文件，对比点击前后的变化
"""

import cv2
import numpy as np
import os
from pathlib import Path

def analyze_image(image_path):
    """分析单个图像"""
    if not os.path.exists(image_path):
        return None
    
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 基本信息
    height, width, channels = img.shape
    
    # 计算颜色统计
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 深蓝色区域
    blue_lower = np.array([100, 100, 100])
    blue_upper = np.array([130, 255, 255])
    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
    blue_pixels = np.sum(blue_mask > 0)
    
    # 白色区域（hover 效果）
    white_lower = np.array([0, 0, 200])
    white_upper = np.array([180, 30, 255])
    white_mask = cv2.inRange(hsv, white_lower, white_upper)
    white_pixels = np.sum(white_mask > 0)
    
    # 按钮区域（993, 723 附近）
    button_x, button_y = 993, 723
    button_region = img[button_y-20:button_y+20, button_x-60:button_x+60]
    
    # 计算按钮区域的平均颜色
    if button_region.size > 0:
        avg_color = np.mean(button_region, axis=(0, 1))
        button_hsv = cv2.cvtColor(button_region, cv2.COLOR_BGR2HSV)
        avg_hsv = np.mean(button_hsv, axis=(0, 1))
    else:
        avg_color = [0, 0, 0]
        avg_hsv = [0, 0, 0]
    
    return {
        'path': image_path,
        'size': (width, height),
        'blue_pixels': blue_pixels,
        'white_pixels': white_pixels,
        'button_avg_bgr': avg_color,
        'button_avg_hsv': avg_hsv
    }

def compare_images(img1_info, img2_info):
    """对比两个图像"""
    if img1_info is None or img2_info is None:
        return None
    
    blue_diff = img2_info['blue_pixels'] - img1_info['blue_pixels']
    white_diff = img2_info['white_pixels'] - img1_info['white_pixels']
    
    bgr_diff = np.abs(img2_info['button_avg_bgr'] - img1_info['button_avg_bgr'])
    hsv_diff = np.abs(img2_info['button_avg_hsv'] - img1_info['button_avg_hsv'])
    
    return {
        'blue_diff': blue_diff,
        'white_diff': white_diff,
        'bgr_diff': bgr_diff,
        'hsv_diff': hsv_diff
    }

def extract_button_region(image_path, output_path):
    """提取按钮区域并保存"""
    if not os.path.exists(image_path):
        return False
    
    img = cv2.imread(image_path)
    if img is None:
        return False
    
    # 按钮区域
    button_x, button_y = 993, 723
    margin = 100
    button_region = img[button_y-margin:button_y+margin, button_x-margin:button_x+margin]
    
    # 在按钮区域标记中心点
    cv2.circle(button_region, (margin, margin), 5, (0, 0, 255), -1)
    cv2.circle(button_region, (margin, margin), 10, (0, 0, 255), 2)
    
    cv2.imwrite(output_path, button_region)
    return True

def main():
    """主函数"""
    print("=" * 80)
    print("截图分析报告")
    print("=" * 80)
    print()
    
    # 要分析的截图列表
    screenshots = [
        'before_click.png',
        'hover_effect.png',
        'after_click_2s.png',
        'after_click_7s.png',
        'after_click_17s.png',
        'button_candidates.png'
    ]
    
    # 分析所有截图
    results = {}
    for screenshot in screenshots:
        print(f"分析 {screenshot}...")
        info = analyze_image(screenshot)
        if info:
            results[screenshot] = info
            print(f"  尺寸: {info['size'][0]}x{info['size'][1]}")
            print(f"  深蓝色像素: {info['blue_pixels']}")
            print(f"  白色像素: {info['white_pixels']}")
            print(f"  按钮区域平均颜色 (BGR): {info['button_avg_bgr']}")
            print(f"  按钮区域平均颜色 (HSV): {info['button_avg_hsv']}")
            
            # 提取按钮区域
            button_output = screenshot.replace('.png', '_button_region.png')
            if extract_button_region(screenshot, button_output):
                print(f"  ✅ 按钮区域已保存: {button_output}")
        else:
            print(f"  ❌ 文件不存在或无法读取")
        print()
    
    # 对比分析
    print("=" * 80)
    print("对比分析")
    print("=" * 80)
    print()
    
    if 'before_click.png' in results and 'hover_effect.png' in results:
        print("1. 点击前 vs Hover 效果")
        diff = compare_images(results['before_click.png'], results['hover_effect.png'])
        if diff:
            print(f"   深蓝色像素变化: {diff['blue_diff']:+d}")
            print(f"   白色像素变化: {diff['white_diff']:+d}")
            print(f"   按钮颜色变化 (BGR): {diff['bgr_diff']}")
            print(f"   按钮颜色变化 (HSV): {diff['hsv_diff']}")
            
            if diff['white_diff'] > 1000:
                print("   ✅ 检测到 hover 效果（白色像素增加）")
            else:
                print("   ⚠️  未检测到明显的 hover 效果")
        print()
    
    if 'hover_effect.png' in results and 'after_click_2s.png' in results:
        print("2. Hover 效果 vs 点击后2秒")
        diff = compare_images(results['hover_effect.png'], results['after_click_2s.png'])
        if diff:
            print(f"   深蓝色像素变化: {diff['blue_diff']:+d}")
            print(f"   白色像素变化: {diff['white_diff']:+d}")
            print(f"   按钮颜色变化 (BGR): {diff['bgr_diff']}")
            print(f"   按钮颜色变化 (HSV): {diff['hsv_diff']}")
            
            if np.sum(diff['bgr_diff']) > 10:
                print("   ✅ 检测到界面变化")
            else:
                print("   ⚠️  未检测到明显变化")
        print()
    
    if 'before_click.png' in results and 'after_click_17s.png' in results:
        print("3. 点击前 vs 点击后17秒")
        diff = compare_images(results['before_click.png'], results['after_click_17s.png'])
        if diff:
            print(f"   深蓝色像素变化: {diff['blue_diff']:+d}")
            print(f"   白色像素变化: {diff['white_diff']:+d}")
            print(f"   按钮颜色变化 (BGR): {diff['bgr_diff']}")
            print(f"   按钮颜色变化 (HSV): {diff['hsv_diff']}")
            
            if np.sum(diff['bgr_diff']) > 10:
                print("   ✅ 检测到界面变化")
            else:
                print("   ⚠️  未检测到明显变化（可能点击无效）")
        print()
    
    # 检查 button_candidates.png
    if 'button_candidates.png' in results:
        print("4. 按钮识别结果")
        print(f"   识别到的按钮位置: (993, 723)")
        print(f"   按钮区域平均颜色: {results['button_candidates.png']['button_avg_bgr']}")
        print()
    
    print("=" * 80)
    print("分析完成")
    print("=" * 80)
    print()
    print("生成的按钮区域截图：")
    for screenshot in screenshots:
        button_output = screenshot.replace('.png', '_button_region.png')
        if os.path.exists(button_output):
            print(f"  - {button_output}")
    print()
    print("建议：")
    print("  1. 查看 *_button_region.png 文件，确认识别的按钮是否正确")
    print("  2. 如果 hover 效果明显但点击后无变化，可能是点击方式不对")
    print("  3. 如果完全没有变化，可能识别到了错误的按钮")
    print()

if __name__ == "__main__":
    main()
