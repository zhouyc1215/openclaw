#!/bin/bash
# VPN 连接检测守护进程
# 用途：定期检查 VPN 连接状态，断开时自动重连

LOG_FILE="/home/tsl/openclaw/vpn-auto/watchdog.log"
CHECK_INTERVAL=60  # 检查间隔（秒）
RECONNECT_SCRIPT="/home/tsl/openclaw/vpn-auto/vpn-reconnect.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_vpn_connected() {
    # 方法1：检查网络接口
    if ip addr show | grep -q "ppp\|tun\|wg"; then
        return 0
    fi
    
    # 方法2：检查 FortiClient 状态
    if forticlient vpn status 2>/dev/null | grep -qi "connected"; then
        return 0
    fi
    
    return 1
}

log "VPN Watchdog 启动"

while true; do
    if check_vpn_connected; then
        log "✅ VPN 已连接"
    else
        log "❌ VPN 未连接，触发重连..."
        
        # 调用重连脚本
        if [ -x "$RECONNECT_SCRIPT" ]; then
            "$RECONNECT_SCRIPT" >> "$LOG_FILE" 2>&1
        else
            log "错误：重连脚本不存在或不可执行: $RECONNECT_SCRIPT"
        fi
    fi
    
    sleep "$CHECK_INTERVAL"
done
