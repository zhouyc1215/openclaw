#!/usr/bin/env python3
"""
调试 OCR 识别结果
显示所有识别到的文字
"""

import cv2
import pytesseract
import os

SCREENSHOT = "screen.png"

if not os.path.exists(SCREENSHOT):
    print(f"❌ 截图文件不存在: {SCREENSHOT}")
    exit(1)

# 读取图像
img = cv2.imread(SCREENSHOT)
if img is None:
    print(f"❌ 无法读取截图")
    exit(1)

print(f"屏幕尺寸: {img.shape[1]}x{img.shape[0]}")
print("")

# 使用 OCR 识别所有文字
print("OCR 识别结果:")
print("=" * 80)

data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

for i, text in enumerate(data['text']):
    if text.strip():
        x = data['left'][i]
        y = data['top'][i]
        w = data['width'][i]
        h = data['height'][i]
        conf = data['conf'][i]
        
        print(f"文字: '{text}'")
        print(f"  位置: x={x}, y={y}, w={w}, h={h}")
        print(f"  置信度: {conf}")
        print("")

print("=" * 80)
print("")
print("如果没有识别到 'SAML Login'，可能需要:")
print("  1. 预处理图像（灰度化、二值化、降噪）")
print("  2. 调整 OCR 参数")
print("  3. 裁剪特定区域进行识别")
