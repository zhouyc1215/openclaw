#!/bin/bash
# 重启后验证脚本
# 用法: bash verify-after-reboot.sh

echo "=========================================="
echo "VPN 自动重连系统 - 重启后验证"
echo "=========================================="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 检查 systemd 服务状态
echo "1. 检查 systemd 服务状态..."
if systemctl is-active --quiet vpn-auto.service; then
    echo "✅ vpn-auto.service 正在运行"
    systemctl status vpn-auto.service --no-pager -l | head -15
else
    echo "❌ vpn-auto.service 未运行"
    echo "尝试查看失败原因:"
    sudo journalctl -u vpn-auto.service -n 20 --no-pager
fi
echo ""

# 2. 检查服务是否开机自启动
echo "2. 检查开机自启动..."
if systemctl is-enabled --quiet vpn-auto.service; then
    echo "✅ vpn-auto.service 已启用开机自启动"
else
    echo "❌ vpn-auto.service 未启用开机自启动"
fi
echo ""

# 3. 检查进程
echo "3. 检查进程..."
if pgrep -f "vpn-auto/v2/core/watchdog.py" > /dev/null; then
    echo "✅ Watchdog 进程正在运行"
    ps aux | grep "watchdog.py" | grep -v grep
else
    echo "❌ Watchdog 进程未运行"
fi
echo ""

# 4. 检查日志文件
echo "4. 检查日志文件..."
LOG_DIR="$HOME/openclaw/vpn-auto/v2/logs"
if [ -d "$LOG_DIR" ]; then
    LATEST_LOG=$(ls -t "$LOG_DIR"/vpn-*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "✅ 日志文件存在: $LATEST_LOG"
        echo "最近 10 行日志:"
        tail -10 "$LATEST_LOG"
    else
        echo "⚠️  未找到日志文件"
    fi
else
    echo "❌ 日志目录不存在"
fi
echo ""

# 5. 检查 VPN 状态
echo "5. 检查 VPN 连接状态..."
if ip addr show ppp0 2>/dev/null | grep -q "inet "; then
    echo "✅ VPN 已连接 (ppp0)"
    ip addr show ppp0 | grep "inet "
else
    echo "⚠️  VPN 未连接"
    echo "系统会在连续失败 3 次后自动重连"
fi
echo ""

# 6. 检查 FortiClient 进程
echo "6. 检查 FortiClient 进程..."
if pgrep -f forticlient > /dev/null; then
    echo "✅ FortiClient 进程正在运行"
    pgrep -af forticlient
else
    echo "⚠️  FortiClient 进程未运行"
fi
echo ""

# 7. 检查 DISPLAY 环境
echo "7. 检查 DISPLAY 环境..."
if DISPLAY=:1 xdotool search --name "FortiClient" 2>/dev/null; then
    echo "✅ FortiClient 窗口存在 (DISPLAY=:1)"
else
    echo "⚠️  FortiClient 窗口未找到"
fi
echo ""

# 8. 测试配置文件
echo "8. 测试配置文件..."
cd "$HOME/openclaw/vpn-auto/v2"
if python3 -c "from core.config_loader import load_config; load_config()" 2>/dev/null; then
    echo "✅ 配置文件加载正常"
else
    echo "❌ 配置文件加载失败"
fi
echo ""

# 9. 检查定时任务
echo "9. 检查定时任务状态..."
if [ -f "$HOME/.openclaw/cron/jobs.json" ]; then
    echo "✅ 定时任务配置存在"
    TASK_COUNT=$(jq '. | length' "$HOME/.openclaw/cron/jobs.json" 2>/dev/null || echo "0")
    echo "   已配置 $TASK_COUNT 个定时任务"
else
    echo "⚠️  定时任务配置不存在"
fi
echo ""

# 10. 系统资源使用
echo "10. 系统资源使用..."
if pgrep -f "watchdog.py" > /dev/null; then
    PID=$(pgrep -f "watchdog.py")
    echo "Watchdog 进程资源使用:"
    ps -p $PID -o pid,ppid,%cpu,%mem,vsz,rss,cmd --no-headers
fi
echo ""

echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "如果发现问题，可以："
echo "1. 查看详细日志: sudo journalctl -u vpn-auto.service -f"
echo "2. 查看应用日志: tail -f ~/openclaw/vpn-auto/v2/logs/vpn-*.log"
echo "3. 重启服务: sudo systemctl restart vpn-auto.service"
echo "4. 手动测试: bash ~/openclaw/vpn-auto/v2/run.sh"
echo ""
