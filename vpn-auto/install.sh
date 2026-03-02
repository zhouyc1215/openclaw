#!/bin/bash
# VPN 自动重连系统安装脚本

set -e

VPN_AUTO_DIR="/home/tsl/clawd/vpn-auto"
SERVICE_FILE="vpn-watchdog.service"

echo "=========================================="
echo "VPN 自动重连系统安装"
echo "=========================================="
echo ""

# 检查依赖
echo "1. 检查依赖..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "请先安装 Node.js: sudo apt install nodejs npm"
    exit 1
fi

if ! command -v forticlient &> /dev/null; then
    echo "❌ FortiClient 未安装"
    exit 1
fi

echo "✅ 依赖检查通过"
echo ""

# 安装 Playwright
echo "2. 安装 Playwright..."
cd "$VPN_AUTO_DIR"

if [ ! -d "node_modules" ]; then
    npm init -y
    npm install playwright
    npx playwright install chromium
    echo "✅ Playwright 安装完成"
else
    echo "✅ Playwright 已安装"
fi
echo ""

# 设置脚本权限
echo "3. 设置脚本权限..."
chmod +x "$VPN_AUTO_DIR/vpn-watchdog.sh"
chmod +x "$VPN_AUTO_DIR/vpn-reconnect.sh"
chmod +x "$VPN_AUTO_DIR/auto-saml-login.js"
echo "✅ 权限设置完成"
echo ""

# 安装 systemd 服务
echo "4. 安装 systemd 服务..."
sudo cp "$VPN_AUTO_DIR/$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload
echo "✅ systemd 服务已安装"
echo ""

# 启动服务
echo "5. 启动服务..."
read -p "是否立即启动 VPN Watchdog 服务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable vpn-watchdog.service
    sudo systemctl start vpn-watchdog.service
    echo "✅ 服务已启动"
    echo ""
    echo "查看服务状态: sudo systemctl status vpn-watchdog"
    echo "查看日志: journalctl -u vpn-watchdog -f"
else
    echo "跳过启动，稍后可手动启动："
    echo "  sudo systemctl enable vpn-watchdog.service"
    echo "  sudo systemctl start vpn-watchdog.service"
fi
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "管理命令："
echo "  启动服务: sudo systemctl start vpn-watchdog"
echo "  停止服务: sudo systemctl stop vpn-watchdog"
echo "  查看状态: sudo systemctl status vpn-watchdog"
echo "  查看日志: journalctl -u vpn-watchdog -f"
echo ""
echo "日志文件："
echo "  Watchdog: $VPN_AUTO_DIR/watchdog.log"
echo "  Reconnect: $VPN_AUTO_DIR/reconnect.log"
echo ""
