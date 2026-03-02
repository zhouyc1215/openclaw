#!/bin/bash
# 半自动 VPN 连接脚本
# 用户需要手动在 FortiClient GUI 中点击 Connect，然后脚本自动点击 SAML Login 按钮

DISPLAY=:1

echo "=========================================="
echo "半自动 VPN 连接"
echo "=========================================="
echo ""

# 1. 检查 FortiClient 是否运行
echo "检查 FortiClient..."
if ! pgrep -f "FortiClient" > /dev/null; then
    echo "❌ FortiClient 未运行"
    echo ""
    echo "启动 FortiClient..."
    DISPLAY=$DISPLAY /usr/bin/forticlient gui &
    sleep 5
fi
echo "✅ FortiClient 正在运行"
echo ""

# 2. 提示用户手动点击连接
echo "=========================================="
echo "请在 FortiClient GUI 中手动点击 Connect 按钮"
echo "等待 SAML 登录页面出现后，脚本将自动点击登录按钮"
echo "=========================================="
echo ""
echo "按 Enter 键继续（当 SAML 登录页面出现后）..."
read

# 3. 运行简化版脚本
echo ""
echo "运行自动点击脚本..."
python3 vpn-auto/simple-click-button.py

# 4. 检查 VPN 状态
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
