#!/bin/bash
# 安装 GUI 自动化依赖

echo "=========================================="
echo "安装 GUI 自动化依赖"
echo "=========================================="
echo ""

echo "1. 安装 Python 依赖..."
pip3 install --user pyautogui opencv-python-headless pillow

echo ""
echo "2. 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y scrot python3-tk python3-dev

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
