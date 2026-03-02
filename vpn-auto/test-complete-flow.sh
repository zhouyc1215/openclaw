#!/bin/bash
# 完整测试 VPN 自动连接流程

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "完整测试 VPN 自动连接流程"
echo "=========================================="
echo ""

# 1. 清理环境
echo "步骤 1: 清理环境..."
echo "  停止 VPN 进程..."
echo "tsl123" | sudo -S pkill -9 openfortivpn 2>/dev/null || true
sleep 1
echo "  ✅ VPN 进程已清理"
echo ""

# 2. 重启 FortiClient GUI
echo "步骤 2: 重启 FortiClient GUI..."
echo "  停止 FortiClient 进程..."
echo "tsl123" | sudo -S pkill -9 -f forticlient 2>/dev/null || true
sleep 3

echo "  启动 FortiClient GUI..."
DISPLAY=:1 nohup /usr/bin/forticlient gui > /tmp/forticlient-gui.log 2>&1 &
sleep 3

echo "  等待 FortiClient 窗口出现（最多30秒）..."
for i in {1..30}; do
    if DISPLAY=:1 xdotool search --name "FortiClient" > /dev/null 2>&1; then
        echo "  ✅ FortiClient 窗口已出现（等待 ${i} 秒）"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "  ❌ FortiClient 窗口出现超时"
        echo ""
        echo "调试信息："
        tail -20 /tmp/forticlient-gui.log 2>/dev/null || echo "  无日志文件"
        exit 1
    fi
    
    sleep 1
done

echo "  等待 GUI 界面完全加载（10秒）..."
sleep 10
echo "  ✅ FortiClient GUI 已完全启动"
echo ""

# 3. 运行智能按钮查找脚本
echo "步骤 3: 运行智能按钮查找脚本..."
python3 smart-find-button.py
if [ $? -ne 0 ]; then
    echo "❌ 按钮查找失败"
    exit 1
fi
echo ""

# 4. 等待 VPN 连接
echo "步骤 4: 等待 VPN 连接（最多 30 秒）..."
for i in {1..6}; do
    echo "  检查 VPN 连接状态 ($i/6)..."
    
    # 检查 ppp0 接口
    if ip addr show ppp0 2>/dev/null | grep -q "inet "; then
        echo ""
        echo "✅ VPN 已成功连接！"
        echo ""
        ip addr show ppp0 | grep "inet "
        echo ""
        
        # 测试外网连接
        echo "步骤 5: 测试外网连接..."
        if ping -c 2 8.8.8.8 > /dev/null 2>&1; then
            echo "✅ 外网连接正常"
        else
            echo "⚠️  外网连接失败"
        fi
        echo ""
        
        echo "=========================================="
        echo "✅ 测试完成 - VPN 自动连接成功！"
        echo "=========================================="
        exit 0
    fi
    
    sleep 5
done

echo ""
echo "❌ VPN 连接超时（30秒内未建立连接）"
echo ""
echo "调试信息："
echo "  1. 检查 FortiClient GUI 是否显示连接中"
echo "  2. 查看调试图像："
echo "     - button_candidates.png (按钮识别)"
echo "     - hover_effect.png (hover 效果)"
echo "  3. 检查是否需要 MFA 认证"
echo ""

exit 1
