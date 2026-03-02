#!/bin/bash
# 最终版本：假设 FortiClient 已经在运行，直接点击 SAML Login 按钮

DISPLAY=:1

echo "=========================================="
echo "VPN 自动连接（简化版）"
echo "=========================================="
echo ""

# 1. 检查 FortiClient 是否运行
echo "检查 FortiClient..."
if ! DISPLAY=$DISPLAY xdotool search --name "FortiClient" > /dev/null 2>&1; then
    echo "❌ FortiClient 未运行"
    echo ""
    echo "请确保 FortiClient 已经启动"
    exit 1
fi
echo "✅ FortiClient 正在运行"
echo ""

# 2. 运行简化版脚本（直接点击 SAML Login 按钮）
echo "运行自动点击脚本..."
cd vpn-auto
python3 simple-click-button.py

# 3. 检查 VPN 状态
echo ""
echo "等待 VPN 连接（10秒）..."
sleep 10

echo ""
echo "检查 VPN 状态..."
if ip addr show ppp0 2>/dev/null | grep -q "inet "; then
    echo "✅ VPN 已连接！"
    ip addr show ppp0 | grep "inet "
else
    echo "⚠️  VPN 未连接，可能需要更长时间"
fi

echo ""
echo "=========================================="
echo "完成"
echo "=========================================="
