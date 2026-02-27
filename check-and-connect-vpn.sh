#!/bin/bash
# VPN 自动检查和连接脚本

set -e

VPN_NAME="${VPN_NAME:-default}"  # VPN配置名称，可通过环境变量设置
MAX_RETRIES=3
RETRY_DELAY=5

# 检查VPN状态
check_vpn_status() {
    local status=$(forticlient vpn status 2>&1)
    if echo "$status" | grep -q "Status: Connected"; then
        echo "✅ VPN已连接"
        return 0
    else
        echo "❌ VPN未连接: $status"
        return 1
    fi
}

# 检查网络连通性
check_internet() {
    if curl -s --connect-timeout 5 --max-time 10 https://www.google.com > /dev/null 2>&1; then
        echo "✅ 网络连通"
        return 0
    else
        echo "❌ 网络不通"
        return 1
    fi
}

# 连接VPN
connect_vpn() {
    echo "🔄 正在连接VPN..."
    
    # 方法1：使用CLI连接（需要配置文件）
    if forticlient vpn list 2>&1 | grep -q "$VPN_NAME"; then
        forticlient vpn connect "$VPN_NAME"
        sleep 5
        return 0
    fi
    
    # 方法2：检查GUI是否已经连接
    # 如果GUI运行且网络通，说明VPN可能已通过GUI连接
    if pgrep -f "FortiClient" > /dev/null; then
        echo "⚠️  FortiClient GUI正在运行，检查网络..."
        sleep 3
        if check_internet; then
            echo "✅ 网络已通过GUI连接"
            return 0
        fi
    fi
    
    # 方法3：尝试通过xdotool自动点击GUI连接按钮（如果安装了xdotool）
    if command -v xdotool &> /dev/null && pgrep -f "FortiClient" > /dev/null; then
        echo "🔄 尝试通过GUI自动连接..."
        # 这里需要根据实际GUI布局调整
        # xdotool可以模拟鼠标点击
        return 1
    fi
    
    echo "⚠️  无法自动连接VPN"
    echo "💡 请手动在FortiClient GUI中连接VPN"
    echo "💡 或者配置CLI VPN: forticlient vpn edit <name>"
    return 1
}

# 主逻辑
main() {
    echo "🔍 检查VPN连接状态..."
    
    # 先检查网络
    if check_internet; then
        echo "✅ 网络正常，无需VPN或VPN已连接"
        exit 0
    fi
    
    # 检查VPN状态
    if check_vpn_status; then
        echo "✅ VPN已连接但网络不通，可能需要重连"
    fi
    
    # 尝试连接VPN
    for i in $(seq 1 $MAX_RETRIES); do
        echo "🔄 尝试连接VPN (第 $i/$MAX_RETRIES 次)..."
        
        if connect_vpn; then
            sleep 5
            if check_vpn_status && check_internet; then
                echo "✅ VPN连接成功，网络正常"
                exit 0
            fi
        fi
        
        if [ $i -lt $MAX_RETRIES ]; then
            echo "⏳ 等待 $RETRY_DELAY 秒后重试..."
            sleep $RETRY_DELAY
        fi
    done
    
    echo "❌ VPN连接失败，请手动检查"
    exit 1
}

# 如果作为脚本运行
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
