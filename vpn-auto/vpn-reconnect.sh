#!/bin/bash
# VPN 重连脚本
# 用途：拉起 FortiClient GUI 并触发自动登录

LOG_FILE="/home/tsl/openclaw/vpn-auto/reconnect.log"
PLAYWRIGHT_SCRIPT="/home/tsl/openclaw/vpn-auto/auto-saml-login.js"
MAX_RETRIES=3
RETRY_DELAY=10

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查 FortiClient 是否在运行
check_forticlient_running() {
    pgrep -f "FortiClient" > /dev/null
}

# 启动 FortiClient GUI
start_forticlient_gui() {
    log "启动 FortiClient GUI..."
    
    # 如果已经在运行，先关闭
    if check_forticlient_running; then
        log "FortiClient 已在运行，先关闭..."
        pkill -f "FortiClient"
        sleep 2
    fi
    
    # 启动 FortiClient（后台运行）
    nohup /opt/forticlient/fortitray > /dev/null 2>&1 &
    sleep 3
    
    if check_forticlient_running; then
        log "✅ FortiClient GUI 已启动"
        return 0
    else
        log "❌ FortiClient GUI 启动失败"
        return 1
    fi
}

# 触发 VPN 连接（通过 Playwright 自动化）
trigger_vpn_connect() {
    log "触发 VPN 连接（Playwright 自动化）..."
    
    if [ ! -f "$PLAYWRIGHT_SCRIPT" ]; then
        log "错误：Playwright 脚本不存在: $PLAYWRIGHT_SCRIPT"
        return 1
    fi
    
    # 运行 Playwright 脚本
    cd "$(dirname "$PLAYWRIGHT_SCRIPT")"
    node "$PLAYWRIGHT_SCRIPT" >> "$LOG_FILE" 2>&1
    
    return $?
}

# 主流程
log "========== VPN 重连开始 =========="

for i in $(seq 1 $MAX_RETRIES); do
    log "尝试 $i/$MAX_RETRIES..."
    
    # 启动 FortiClient GUI
    if ! start_forticlient_gui; then
        log "重试 $i 失败：无法启动 FortiClient"
        sleep "$RETRY_DELAY"
        continue
    fi
    
    # 触发自动登录
    if trigger_vpn_connect; then
        log "✅ VPN 连接成功"
        log "========== VPN 重连完成 =========="
        exit 0
    else
        log "重试 $i 失败：自动登录失败"
        sleep "$RETRY_DELAY"
    fi
done

log "❌ VPN 重连失败（已尝试 $MAX_RETRIES 次）"
log "========== VPN 重连失败 =========="
exit 1
