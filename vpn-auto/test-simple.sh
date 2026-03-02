#!/bin/bash
# 简化测试：假设 FortiClient 已运行

echo "=========================================="
echo "简化测试（不重启 FortiClient）"
echo "=========================================="
echo ""

# 检查 FortiClient 是否运行
echo "检查 FortiClient..."
if ! DISPLAY=:1 xdotool search --name "FortiClient" > /dev/null 2>&1; then
    echo "❌ FortiClient 未运行"
    echo ""
    echo "请先启动 FortiClient:"
    echo "  DISPLAY=:1 /usr/bin/forticlient gui &"
    echo ""
    exit 1
fi
echo "✅ FortiClient 正在运行"
echo ""

# 运行简化脚本
echo "运行按钮点击脚本..."
python3 simple-click-button.py

echo ""
echo "等待 VPN 连接（10秒）..."
sleep 10

echo ""
echo "检查 VPN 状态..."
if ip addr show ppp0 2>/dev/null | grep -q "inet "; then
    echo "✅ VPN 已连接！"
    ip addr show ppp0 | grep "inet "
else
    echo "❌ VPN 未连接"
    echo ""
    echo "可能的原因："
    echo "  1. 需要在浏览器中完成 SAML 认证"
    echo "  2. 需要 MFA 认证"
    echo "  3. 需要更长的等待时间"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
