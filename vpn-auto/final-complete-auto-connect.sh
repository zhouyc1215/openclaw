#!/bin/bash
# 最终完整版：重启 FortiClient 并自动连接 VPN
# 1. 停止 FortiClient
# 2. 在 GUI 左边栏点击第三个图标启动 FortiClient
# 3. 等待启动完成
# 4. 调用 simple-click-button.py 点击 SAML Login 按钮
# 5. 检查 VPN 连接状态

DISPLAY=:1
SUDO_PASSWORD="tsl123"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=========================================="
log "VPN 完整自动连接"
log "=========================================="
log ""

# 1. 停止 FortiClient
log "停止 FortiClient 进程..."
# 启动 sudo 命令（会弹出密码输入窗口）
sudo pkill -9 -f forticlient 2>/dev/null &
SUDO_PID=$!

# 等待密码输入窗口出现
sleep 2

# 在 GUI 模式下自动输入密码
log "自动输入密码..."
DISPLAY=$DISPLAY xdotool type "tsl123"
sleep 0.5
DISPLAY=$DISPLAY xdotool key Return
sleep 1

# 等待 sudo 命令完成
wait $SUDO_PID 2>/dev/null || true
sleep 2

log "✅ FortiClient 进程已停止"
log ""

# 2. 在 GUI 左边栏点击第三个图标启动 FortiClient
log "在 GUI 左边栏点击第三个图标启动 FortiClient..."
SIDEBAR_X=40
BUTTON_Y=200  # 第三个按钮的 Y 坐标

DISPLAY=$DISPLAY xdotool mousemove --sync $SIDEBAR_X $BUTTON_Y
sleep 0.5
DISPLAY=$DISPLAY xdotool click 1
sleep 2
log "✅ 已点击左边栏图标"
log ""

# 3. 等待 FortiClient 窗口出现
log "等待 FortiClient 窗口出现（最多 30 秒）..."
for i in {1..30}; do
    if DISPLAY=$DISPLAY xdotool search --name "FortiClient" > /dev/null 2>&1; then
        log "✅ 窗口已出现（等待 $i 秒）"
        break
    fi
    sleep 1
done

if ! DISPLAY=$DISPLAY xdotool search --name "FortiClient" > /dev/null 2>&1; then
    log "❌ FortiClient 窗口未出现"
    exit 1
fi
log ""

# 4. 等待 GUI 完全加载
log "等待 GUI 完全加载（15 秒）..."
sleep 15
log "✅ GUI 应该已完全加载"
log ""

# 5. 调用 simple-click-button.py
log "调用 simple-click-button.py 点击 SAML Login 按钮..."
cd "$(dirname "$0")"
python3 simple-click-button.py

# 6. 检查 VPN 连接状态
log ""
log "等待 VPN 连接（30 秒）..."
sleep 30

log ""
log "检查 VPN 状态..."
if ip addr show ppp0 2>/dev/null | grep -q "inet "; then
    log "✅ VPN 已连接！"
    ip addr show ppp0 | grep "inet "
    log ""
    log "=========================================="
    log "✅ VPN 自动连接成功！"
    log "=========================================="
    exit 0
else
    log "⚠️  VPN 未连接，可能需要手动完成 SAML 认证"
    log ""
    log "=========================================="
    log "⚠️  请在浏览器中完成 SAML 认证"
    log "=========================================="
    exit 1
fi
