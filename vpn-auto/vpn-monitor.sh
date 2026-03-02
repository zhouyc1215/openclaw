#!/bin/bash
# VPN 监控脚本（半自动模式）
# 用途：监控 VPN 连接状态，断线时发送飞书通知

LOG_FILE="/home/tsl/openclaw/vpn-auto/monitor.log"
CHECK_INTERVAL=60  # 检查间隔（秒）
FEISHU_USER_ID="ou_b3afb7d2133e4d689be523fc48f3d2b3"
GATEWAY_URL="ws://10.71.1.116:18789"
OPENCLAW_DIR="/home/tsl/openclaw"
LAST_STATUS="unknown"

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
    
    # 方法3：测试外网连接
    if curl -s --connect-timeout 3 --max-time 5 https://www.google.com -o /dev/null; then
        return 0
    fi
    
    return 1
}

send_feishu_notification() {
    local status="$1"
    local message="$2"
    
    log "发送飞书通知: $message"
    
    # 切换到 openclaw 目录并发送消息
    (cd "$OPENCLAW_DIR" && pnpm openclaw message send \
        --channel feishu \
        --target "$FEISHU_USER_ID" \
        --message "$message") 2>&1 | tee -a "$LOG_FILE"
}

start_forticlient_gui() {
    log "启动 FortiClient GUI..."
    
    # 检查 FortiClient 是否已经在运行
    if pgrep -f "fortitray" > /dev/null; then
        log "FortiClient GUI 已在运行"
        return 0
    fi
    
    # 设置 DISPLAY 环境变量
    export DISPLAY=:1
    export XAUTHORITY=/home/tsl/.Xauthority
    
    # 启动 FortiClient GUI（后台运行）
    nohup /opt/forticlient/fortitray > /dev/null 2>&1 &
    
    sleep 3
    
    if pgrep -f "fortitray" > /dev/null; then
        log "✅ FortiClient GUI 已启动"
        return 0
    else
        log "❌ FortiClient GUI 启动失败"
        return 1
    fi
}

trigger_vpn_connect() {
    log "触发 VPN 连接..."
    
    # 方法1：使用 GUI 自动化（推荐）
    if [ -f "/home/tsl/openclaw/vpn-auto/gui-auto-connect.py" ]; then
        log "使用 GUI 自动化点击连接按钮..."
        python3 /home/tsl/openclaw/vpn-auto/gui-auto-connect.py 2>&1 | tee -a "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            log "✅ GUI 自动化成功"
            return 0
        else
            log "⚠️ GUI 自动化失败，尝试命令行方式..."
        fi
    fi
    
    # 方法2：使用 forticlient 命令行工具
    forticlient vpn connect vpn-krgc.dasanns.com 2>&1 | tee -a "$LOG_FILE"
    
    sleep 2
    
    # 检查是否成功触发连接
    if forticlient vpn status 2>/dev/null | grep -qi "connecting\|connected"; then
        log "✅ VPN 连接已触发"
        return 0
    else
        log "⚠️ VPN 连接触发可能失败，请手动完成 MFA 认证"
        return 1
    fi
}

log "========================================="
log "VPN 监控启动（半自动模式）"
log "检查间隔: ${CHECK_INTERVAL}秒"
log "========================================="

while true; do
    if check_vpn_connected; then
        if [ "$LAST_STATUS" != "connected" ]; then
            log "✅ VPN 已连接"
            
            # 如果之前是断开状态，发送恢复通知
            if [ "$LAST_STATUS" = "disconnected" ]; then
                send_feishu_notification "connected" "✅ VPN 连接已恢复

VPN 状态：已连接
时间：$(date '+%Y-%m-%d %H:%M:%S')

可以正常访问外网了。"
            fi
            
            LAST_STATUS="connected"
        fi
    else
        if [ "$LAST_STATUS" != "disconnected" ]; then
            log "❌ VPN 未连接"
            
            # 自动启动 FortiClient GUI
            if start_forticlient_gui; then
                log "尝试触发 VPN 连接..."
                trigger_vpn_connect
            fi
            
            send_feishu_notification "disconnected" "⚠️ VPN 连接已断开

VPN 状态：未连接
时间：$(date '+%Y-%m-%d %H:%M:%S')

已自动启动 FortiClient 并触发 VPN 连接。
请在手机上完成 Microsoft MFA 认证：
1. 打开 Microsoft Authenticator 应用
2. 批准登录请求
3. 或输入验证码

如果未收到 MFA 请求，请手动点击 FortiClient 中的连接按钮。"
            
            LAST_STATUS="disconnected"
        fi
    fi
    
    sleep "$CHECK_INTERVAL"
done
