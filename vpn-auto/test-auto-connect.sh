#!/bin/bash
# 测试自动连接功能

echo "=========================================="
echo "测试 VPN 自动连接功能"
echo "=========================================="
echo ""

echo "1. 检查当前 VPN 状态..."
forticlient vpn status
echo ""

echo "2. 检查 FortiClient GUI 是否运行..."
if pgrep -f "fortitray" > /dev/null; then
    echo "✅ FortiClient GUI 正在运行"
    echo "进程 ID: $(pgrep -f fortitray)"
else
    echo "❌ FortiClient GUI 未运行"
    echo ""
    echo "3. 启动 FortiClient GUI..."
    export DISPLAY=:0
    export XAUTHORITY=/home/tsl/.Xauthority
    nohup /opt/forticlient/fortitray > /dev/null 2>&1 &
    sleep 3
    
    if pgrep -f "fortitray" > /dev/null; then
        echo "✅ FortiClient GUI 已启动"
    else
        echo "❌ FortiClient GUI 启动失败"
        exit 1
    fi
fi

echo ""
echo "4. 触发 VPN 连接..."
forticlient vpn connect vpn-krgc.dasanns.com

echo ""
echo "5. 等待 5 秒..."
sleep 5

echo ""
echo "6. 检查连接状态..."
forticlient vpn status

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "如果状态显示 'Connecting' 或 'Connected'，说明自动连接功能正常。"
echo "请在手机上完成 Microsoft MFA 认证以完成连接。"
