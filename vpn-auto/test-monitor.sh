#!/bin/bash
# VPN 监控测试脚本

echo "=========================================="
echo "VPN 监控测试"
echo "=========================================="
echo ""

echo "1. 检查 VPN 状态..."
if ip addr show | grep -q "ppp\|tun\|wg"; then
    echo "✅ VPN 网络接口已检测到"
else
    echo "❌ VPN 网络接口未检测到"
fi

echo ""
echo "2. 检查 FortiClient 状态..."
forticlient vpn status

echo ""
echo "3. 测试外网连接..."
if curl -s --connect-timeout 3 --max-time 5 https://www.google.com -o /dev/null; then
    echo "✅ 可以访问 Google"
else
    echo "❌ 无法访问 Google"
fi

echo ""
echo "4. 测试飞书通知..."
read -p "是否发送测试通知到飞书？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd /home/tsl/openclaw
    pnpm openclaw message send \
        --channel feishu \
        --to "ou_b3afb7d2133e4d689be523fc48f3d2b3" \
        --message "🧪 VPN 监控测试

这是一条测试消息，用于验证飞书通知功能是否正常。

时间：$(date '+%Y-%m-%d %H:%M:%S')
主机：$(hostname)

如果你收到这条消息，说明通知功能正常！✅"
    
    echo ""
    echo "✅ 测试通知已发送"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
