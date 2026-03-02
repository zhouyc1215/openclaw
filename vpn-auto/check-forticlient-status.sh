#!/bin/bash
# 检查 FortiClient 状态

echo "=========================================="
echo "检查 FortiClient 状态"
echo "=========================================="
echo ""

# 检查窗口
echo "1. 检查 FortiClient 窗口..."
DISPLAY=:1 xdotool search --name "FortiClient" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ FortiClient 窗口存在"
else
    echo "❌ FortiClient 窗口不存在"
fi
echo ""

# 检查进程
echo "2. 检查 FortiClient 进程..."
ps aux | grep forticlient | grep -v grep
echo ""

# 检查 VPN 进程
echo "3. 检查 openfortivpn 进程..."
ps aux | grep openfortivpn | grep -v grep
if [ $? -eq 0 ]; then
    echo "✅ openfortivpn 进程运行中"
else
    echo "❌ openfortivpn 进程未运行"
fi
echo ""

# 检查 VPN 接口
echo "4. 检查 VPN 接口..."
ip addr show ppp0 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ VPN 接口已建立"
else
    echo "❌ VPN 接口未建立"
fi
echo ""

# 截图当前状态
echo "5. 截图当前 FortiClient 状态..."
DISPLAY=:1 scrot forticlient_current_status.png 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 截图已保存: forticlient_current_status.png"
else
    echo "❌ 截图失败"
fi
echo ""

echo "=========================================="
echo "检查完成"
echo "=========================================="
