#!/bin/bash
# VPN 自动重连系统测试脚本

VPN_AUTO_DIR="/home/tsl/clawd/vpn-auto"

echo "=========================================="
echo "VPN 自动重连系统测试"
echo "=========================================="
echo ""

# 测试 1：检查脚本是否存在
echo "测试 1: 检查脚本文件..."
files=(
    "vpn-watchdog.sh"
    "vpn-reconnect.sh"
    "auto-saml-login.js"
)

for file in "${files[@]}"; do
    if [ -f "$VPN_AUTO_DIR/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (缺失)"
    fi
done
echo ""

# 测试 2：检查脚本权限
echo "测试 2: 检查脚本权限..."
for file in "${files[@]}"; do
    if [ -x "$VPN_AUTO_DIR/$file" ]; then
        echo "  ✅ $file (可执行)"
    else
        echo "  ❌ $file (不可执行)"
    fi
done
echo ""

# 测试 3：检查 Node.js 和 Playwright
echo "测试 3: 检查依赖..."
if command -v node &> /dev/null; then
    echo "  ✅ Node.js: $(node --version)"
else
    echo "  ❌ Node.js 未安装"
fi

if [ -d "$VPN_AUTO_DIR/node_modules/playwright" ]; then
    echo "  ✅ Playwright 已安装"
else
    echo "  ❌ Playwright 未安装"
fi
echo ""

# 测试 4：检查 FortiClient
echo "测试 4: 检查 FortiClient..."
if command -v forticlient &> /dev/null; then
    echo "  ✅ FortiClient 已安装"
    forticlient vpn status 2>&1 | head -3
else
    echo "  ❌ FortiClient 未安装"
fi
echo ""

# 测试 5：测试 VPN 连接检测
echo "测试 5: 测试 VPN 连接检测..."
if ip addr show | grep -q "ppp\|tun\|wg"; then
    echo "  ✅ VPN 已连接"
else
    echo "  ❌ VPN 未连接"
fi
echo ""

# 测试 6：检查 systemd 服务
echo "测试 6: 检查 systemd 服务..."
if systemctl list-unit-files | grep -q "vpn-watchdog.service"; then
    echo "  ✅ systemd 服务已安装"
    sudo systemctl status vpn-watchdog.service --no-pager | head -10
else
    echo "  ❌ systemd 服务未安装"
fi
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "如果所有测试通过，可以运行："
echo "  sudo systemctl start vpn-watchdog"
echo ""
