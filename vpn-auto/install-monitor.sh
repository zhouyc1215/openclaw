#!/bin/bash
# VPN 监控服务安装脚本（半自动模式）

set -e

echo "=========================================="
echo "VPN 监控服务安装（半自动模式）"
echo "=========================================="
echo ""

# 检查是否在正确的目录
if [ ! -f "vpn-monitor.sh" ]; then
    echo "错误：请在 vpn-auto 目录下运行此脚本"
    exit 1
fi

echo "1. 设置脚本权限..."
chmod +x vpn-monitor.sh
echo "✅ 权限设置完成"
echo ""

echo "2. 停止旧的 vpn-watchdog 服务（如果存在）..."
sudo systemctl stop vpn-watchdog 2>/dev/null || true
sudo systemctl disable vpn-watchdog 2>/dev/null || true
echo "✅ 旧服务已停止"
echo ""

echo "3. 安装 systemd 服务..."
sudo cp vpn-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
echo "✅ 服务已安装"
echo ""

echo "4. 启用服务（开机自启动）..."
sudo systemctl enable vpn-monitor
echo "✅ 服务已启用"
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "常用命令："
echo "  启动服务: sudo systemctl start vpn-monitor"
echo "  停止服务: sudo systemctl stop vpn-monitor"
echo "  查看状态: sudo systemctl status vpn-monitor"
echo "  查看日志: journalctl -u vpn-monitor -f"
echo "  查看文件日志: tail -f monitor.log"
echo ""

read -p "是否立即启动服务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start vpn-monitor
    echo ""
    echo "服务已启动！"
    echo ""
    sleep 2
    sudo systemctl status vpn-monitor
fi
