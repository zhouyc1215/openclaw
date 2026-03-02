#!/usr/bin/env python3
"""
识别按钮区域的文字，确认是否是 SAML Login 按钮
"""

import cv2
import pytesseract
import os

def identify_button_text(image_path):
    """识别按钮区域的文字"""
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return None
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 无法读取图像: {image_path}")
        return None
    
    print(f"\n分析: {image_path}")
    print("=" * 60)
    
    # 按钮区域（993, 723 附近，扩大范围）
    button_x, button_y = 993, 723
    margin_x = 150  # 左右各150像素
    margin_y = 50   # 上下各50像素
    
    # 裁剪按钮区域
    y1 = max(0, button_y - margin_y)
    y2 = min(img.shape[0], button_y + margin_y)
    x1 = max(0, button_x - margin_x)
    x2 = min(img.shape[1], button_x + margin_x)
    
    button_region = img[y1:y2, x1:x2]
    
    # 保存按钮区域
    region_filename = image_path.replace('.png', '_text_region.png')
    cv2.imwrite(region_filename, button_region)
    print(f"按钮区域已保存: {region_filename}")
    print(f"区域尺寸: {button_region.shape[1]}x{button_region.shape[0]}")
    
    # 转换为灰度图
    gray = cv2.cvtColor(button_region, cv2.COLOR_BGR2GRAY)
    
    # 尝试多种预处理方法
    methods = [
        ("原始灰度图", gray),
        ("二值化（阈值127）", cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]),
        ("二值化（阈值180）", cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]),
        ("自适应阈值", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ("反转二值化", cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]),
    ]
    
    all_texts = []
    
    for method_name, processed in methods:
        # OCR 识别
        text = pytesseract.image_to_string(processed, lang='eng')
        
        if text.strip():
            print(f"\n{method_name}:")
            print(f"  识别到的文字: '{text.strip()}'")
            all_texts.append(text.strip())
            
            # 保存预处理后的图像
            method_filename = region_filename.replace('_text_region.png', f'_text_{method_name.replace(" ", "_").replace("（", "_").replace("）", "")}.png')
            cv2.imwrite(method_filename, processed)
    
    # 检查是否包含 SAML 或 Login
    contains_saml = any('SAML' in text.upper() for text in all_texts)
    contains_login = any('LOGIN' in text.upper() for text in all_texts)
    
    print("\n" + "=" * 60)
    if contains_saml and contains_login:
        print("✅ 确认：这是 SAML Login 按钮")
        return True
    elif contains_saml or contains_login:
        print("⚠️  可能：包含 SAML 或 Login 关键词")
        return None
    else:
        print("❌ 警告：未识别到 SAML Login 文字")
        print("   可能原因：")
        print("   1. 这不是 SAML Login 按钮")
        print("   2. OCR 识别失败")
        print("   3. 按钮使用图标而不是文字")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("按钮文字识别")
    print("=" * 60)
    
    # 要分析的截图
    screenshots = [
        'before_click.png',
        'hover_effect.png',
        'button_candidates.png'
    ]
    
    results = {}
    for screenshot in screenshots:
        result = identify_button_text(screenshot)
        results[screenshot] = result
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    
    for screenshot, result in results.items():
        if result is True:
            status = "✅ 确认是 SAML Login 按钮"
        elif result is None:
            status = "⚠️  可能是 SAML Login 按钮"
        elif result is False:
            status = "❌ 不是 SAML Login 按钮"
        else:
            status = "❓ 无法分析"
        
        print(f"{screenshot}: {status}")
    
    print("\n建议：")
    print("  1. 查看生成的 *_text_region.png 文件")
    print("  2. 查看生成的 *_text_*.png 预处理图像")
    print("  3. 手动确认按钮上的文字")
    print()

if __name__ == "__main__":
    main()
