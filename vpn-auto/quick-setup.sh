#!/bin/bash
# VPN GUI 自动化快速设置脚本

echo "=========================================="
echo "VPN GUI 自动化快速设置"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

echo "步骤 1/3: 安装依赖..."
echo "----------------------------------------"
./install-gui-automation.sh
echo ""

echo "步骤 2/3: 捕获连接按钮图像..."
echo "----------------------------------------"
echo "请确保 FortiClient 窗口已打开并可见"
echo ""
read -p "准备好后按 Enter 继续..." 
python3 capture-button.py
echo ""

echo "步骤 3/3: 测试自动连接..."
echo "----------------------------------------"
read -p "是否测试自动连接？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 gui-auto-connect.py
fi

echo ""
echo "=========================================="
echo "设置完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 安装监控服务: ./install-monitor.sh"
echo "2. 启动服务: sudo systemctl start vpn-monitor"
echo "3. 查看日志: journalctl -u vpn-monitor -f"
echo ""
echo "文档："
echo "- GUI 自动化指南: GUI-AUTOMATION-GUIDE.md"
echo "- 快速开始: QUICKSTART.md"
